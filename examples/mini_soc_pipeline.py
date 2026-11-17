"""Offline, local-first mini-SOC example with explicit failure semantics.

Accepts small synthetic JSONL files, validates event types, rejects duplicate JSON
keys, normalizes event timestamps to UTC, deduplicates source+event_id and
generates *review* candidates from failed-login bursts.

This is teaching code, NOT a real SIEM, a forensic collector or an access control
mechanism. Input must be event-time-sorted; no remote network requests occur.
"""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterator

MAX_LINE_BYTES = 16_384
MAX_ACTOR_LEN = 128
MAX_EVENT_ID_LEN = 128
MAX_SOURCE_LEN = 128
ALLOWED_ACTIONS = frozenset({"login_failure", "login_success"})
ALLOWED_KEYS = frozenset({
    "timestamp", "actor", "action", "event_id", "source", "src_ip", "outcome",
})


@dataclass(frozen=True)
class AuthEvent:
    source: str
    event_id: str
    timestamp_utc: datetime
    actor: str
    action: str
    src_ip: str | None
    source_line: int


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid numeric constant: {value}")


def _short_text(value: object, *, label: str, max_length: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= max_length:
        raise ValueError(f"{label}: expected 1-{max_length} characters")
    return value


def parse_event(raw: bytes, *, line_number: int, default_source: str) -> AuthEvent:
    """Parse one bounded JSONL line, validating shape, types and timezone."""
    if not isinstance(raw, bytes) or len(raw) > MAX_LINE_BYTES:
        raise ValueError("invalid or oversized raw record")
    if type(line_number) is not int or line_number < 1:
        raise ValueError("invalid line number")
    _short_text(default_source, label="default_source", max_length=MAX_SOURCE_LEN)
    try:
        data = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError("event must be a JSON object")
    if not {"timestamp", "actor", "action"}.issubset(data):
        raise ValueError("missing required event fields")
    if set(data) - ALLOWED_KEYS:
        raise ValueError("unknown event fields")
    actor = _short_text(data["actor"], label="actor", max_length=MAX_ACTOR_LEN)
    action = data["action"]
    if not isinstance(action, str) or action not in ALLOWED_ACTIONS:
        raise ValueError("unsupported action")
    source = _short_text(
        data.get("source", default_source),
        label="source", max_length=MAX_SOURCE_LEN,
    )
    event_id = _short_text(
        data.get("event_id", f"line:{line_number}"),
        label="event_id", max_length=MAX_EVENT_ID_LEN,
    )
    original_time = data["timestamp"]
    if not isinstance(original_time, str) or len(original_time) > 64:
        raise ValueError("invalid timestamp type/size")
    try:
        timestamp = datetime.fromisoformat(
            original_time.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("invalid ISO 8601 timestamp") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must contain offset")
    src_ip = data.get("src_ip")
    if src_ip is not None:
        if not isinstance(src_ip, str) or len(src_ip) > 64:
            raise ValueError("invalid src_ip")
        try:
            src_ip = str(ipaddress.ip_address(src_ip))
        except ValueError as exc:
            raise ValueError("invalid src_ip") from exc
    if "outcome" in data and (
        not isinstance(data["outcome"], str) or len(data["outcome"]) > 64
    ):
        raise ValueError("invalid outcome")
    return AuthEvent(
        source=source, event_id=event_id,
        timestamp_utc=timestamp.astimezone(timezone.utc),
        actor=actor, action=action, src_ip=src_ip, source_line=line_number,
    )


def read_events(path: Path, *, max_records: int = 100_000) -> Iterator[AuthEvent]:
    if type(max_records) is not int or not 1 <= max_records <= 1_000_000:
        raise ValueError("invalid record limit")
    count = 0
    with path.open("rb") as source:
        for line_number, line in enumerate(
            iter(lambda: source.readline(MAX_LINE_BYTES + 1), b""), 1
        ):
            if len(line) > MAX_LINE_BYTES:
                raise ValueError(f"line {line_number}: byte cap exceeded")
            if not line.strip():
                continue
            count += 1
            if count > max_records:
                raise ValueError("record limit exceeded")
            try:
                yield parse_event(line, line_number=line_number,
                                  default_source=path.name)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: {exc}") from exc


def detect_bursts(
    events: Iterator[AuthEvent],
    *,
    threshold: int = 3,
    window_seconds: int = 300,
    max_actors: int = 10_000,
    max_queue_per_actor: int = 5_000,
) -> Iterator[dict]:
    """Yield review alerts when an actor crosses an event-time threshold."""
    for name, value, hi in (
        ("threshold", threshold, 5_000), ("window_seconds", window_seconds, 86_400),
        ("max_actors", max_actors, 100_000),
        ("max_queue_per_actor", max_queue_per_actor, 100_000),
    ):
        if type(value) is not int or not 1 <= value <= hi:
            raise ValueError(f"{name} invalid")
    windows: dict[str, deque[AuthEvent]] = {}
    signaled: set[str] = set()
    seen: set[tuple[str, str]] = set()
    last_timestamp: datetime | None = None
    window = timedelta(seconds=window_seconds)
    for event in events:
        if last_timestamp is not None and event.timestamp_utc < last_timestamp:
            raise ValueError(
                f"line {event.source_line}: out-of-order event-time; input must be sorted"
            )
        last_timestamp = event.timestamp_utc
        identity = (event.source, event.event_id)
        if identity in seen:
            continue
        if len(seen) >= 100_000:
            raise ValueError("deduplication cardinality cap exceeded")
        seen.add(identity)
        if event.action != "login_failure":
            continue
        if event.actor not in windows and len(windows) >= max_actors:
            raise ValueError("active actor cap exceeded")
        queue = windows.setdefault(event.actor, deque())
        while queue and event.timestamp_utc - queue[0].timestamp_utc > window:
            queue.popleft()
        if len(queue) >= max_queue_per_actor:
            raise ValueError("per-actor queue cap exceeded")
        queue.append(event)
        if len(queue) < threshold:
            signaled.discard(event.actor)  # only rearm after post-arrival count falls
        if len(queue) >= threshold and event.actor not in signaled:
            signaled.add(event.actor)
            supporting = list(queue)[-threshold:]
            yield {
                "rule_id": "AUTH-BURST-001", "rule_version": "2.0",
                "actor": event.actor, "failure_count": len(queue),
                "window_seconds": window_seconds,
                "timestamp_utc": event.timestamp_utc.isoformat(),
                "supporting_event_ids": [
                    f"{item.source}:{item.event_id}" for item in supporting
                ],
                "classification": "review", "confidence": "rule-only",
            }


def write_findings_atomic(
    input_path: Path, output_path: Path, *,
    threshold: int = 3, window_seconds: int = 300
) -> int:
    """Write only on complete success. No false 'all clear' after partial input."""
    if input_path.resolve() == output_path.resolve():
        raise ValueError("output must differ from input")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=output_path.parent, prefix=".mini-soc-", suffix=".tmp",
            delete=False,
        ) as target:
            tmp_path = Path(target.name)
            alerts = 0
            for alert in detect_bursts(
                read_events(input_path),
                threshold=threshold, window_seconds=window_seconds,
            ):
                alerts += 1
                if alerts > 100_000:
                    raise ValueError("alert cap exceeded")
                target.write(json.dumps(alert, ensure_ascii=False) + "\n")
        os.replace(tmp_path, output_path)
        return alerts
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="synthetic JSONL input file you own")
    parser.add_argument("--output", required=True, type=Path,
                        help="new or explicitly replaceable local report")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--window-seconds", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        count = write_findings_atomic(
            args.input, args.output, threshold=args.threshold,
            window_seconds=args.window_seconds,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"incomplete ingest; no report committed: {exc}", file=sys.stderr)
        return 2
    print(f"complete: wrote {count} review alert(s) to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
