"""Chapter 01: strict local JSONL authentication summaries.

Usage (from repository root):
  python -m projects.foundations.auth_summary \
    --input fixtures/foundations-auth.jsonl --output /tmp/auth-summary.json

Synthetic owned data only; no network operations, account actions or secrets.
Report output is written only after the complete input has been validated.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile

MAX_LINE_BYTES = 4096
MAX_RECORDS = 1000
MAX_ACTORS = 500
IDENTIFIER = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")


@dataclass(frozen=True)
class Event:
    source: str
    event_id: str
    timestamp_utc: datetime
    actor: str
    action: str


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def _no_nonjson_constant(text: str) -> None:
    raise ValueError(f"invalid JSON numeric constant: {text}")


def _clean_id(value: object, label: str) -> str:
    if type(value) is not str or IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"invalid {label}")
    return value


def parse_event(raw: bytes) -> Event:
    """Accept exact schema with aware time, not merely any valid JSON."""
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_LINE_BYTES:
        raise ValueError("record byte size invalid")
    try:
        obj = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_no_nonjson_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8/JSON") from exc
    required = {"source", "event_id", "timestamp", "actor", "action"}
    if type(obj) is not dict or set(obj) != required:
        raise ValueError("wrong event schema")
    source = _clean_id(obj["source"], "source")
    event_id = _clean_id(obj["event_id"], "event_id")
    actor = _clean_id(obj["actor"], "actor")
    if obj["action"] not in ("login_success", "login_failure"):
        raise ValueError("invalid action")
    if type(obj["action"]) is not str:
        raise ValueError("action type")
    raw_time = obj["timestamp"]
    if type(raw_time) is not str or not 10 <= len(raw_time) <= 64:
        raise ValueError("timestamp format")
    try:
        when = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("timezone required")
    return Event(source, event_id, when.astimezone(timezone.utc), actor, obj["action"])


def read_events(
    path: Path, *, max_records: int = MAX_RECORDS
) -> tuple[list[Event], int, str]:
    """Read only bounded local records. Error means report incomplete.

    Duplicate source-qualified IDs with identical records count as replays;
    a conflicting record with the same ID is an explicit error.
    """
    if type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS:
        raise ValueError("record limit")
    if path.is_symlink() or not path.is_file():
        raise ValueError("input must be a regular, non-symlink file")
    seen: dict[tuple[str, str], Event] = {}
    ordered: list[Event] = []
    duplicate_count = 0
    digest = sha256()
    with path.open("rb") as source:
        for line_number in range(1, max_records + 2):
            raw = source.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            if line_number > max_records:
                raise ValueError("record limit exceeded")
            if len(raw) > MAX_LINE_BYTES:
                raise ValueError(f"line {line_number}: size limit")
            digest.update(raw)
            try:
                event = parse_event(raw)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: {exc}") from exc
            identity = (event.source, event.event_id)
            if identity in seen:
                if seen[identity] != event:
                    raise ValueError(f"line {line_number}: conflicting event ID")
                duplicate_count += 1
            else:
                seen[identity] = event
                ordered.append(event)
    return ordered, duplicate_count, digest.hexdigest()


def summarize(path: Path, *, max_records: int = MAX_RECORDS) -> dict:
    """Return a complete deterministic toy summary or raise."""
    events, duplicates, source_hash = read_events(path, max_records=max_records)
    counts = Counter()
    success = 0
    for event in events:
        if event.action == "login_failure":
            if event.actor not in counts and len(counts) >= MAX_ACTORS:
                raise ValueError("actor cardinality cap exceeded")
            counts[event.actor] += 1
        else:
            success += 1
    return {
        "complete": True,
        "source_sha256": source_hash,
        "input_unique_events": len(events),
        "duplicate_events": duplicates,
        "login_success_events": success,
        "failures_by_actor": dict(sorted(counts.items())),
        "interpretation": "Synthetic counts only; no attack attribution.",
    }


def atomic_json_report(destination: Path, obj: dict) -> None:
    """Stage a single-file JSON report in the destination directory.

    Atomic replacement on supported filesystems is not complete crash-durability
    or a transaction spanning multiple files. Caller owns authorization.
    """
    if not destination.parent.is_dir():
        raise ValueError("output directory does not exist")
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=destination.parent, prefix=".auth-report-", suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(obj, stream, sort_keys=True, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS)
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output cannot refer to the same file")
        summary = summarize(args.input, max_records=args.max_records)
        atomic_json_report(args.output, summary)
    except (ValueError, OSError) as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(f"COMPLETE: {summary['input_unique_events']} unique synthetic records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
