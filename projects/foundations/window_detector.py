"""Chapter 02: deterministic, bounded, offline authentication burst detector.

Run from repository root:
  python -m projects.foundations.window_detector \
    --input fixtures/foundations-auth.jsonl --output /tmp/burst-report.json

No network collection, live account actions, or autonomous blocking.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import timedelta
from pathlib import Path
import sys

from projects.foundations.auth_summary import (
    Event, atomic_json_report, read_events, MAX_RECORDS,
)


def detect(
    events: list[Event],
    *,
    window_seconds: int = 60,
    threshold: int = 3,
    max_actors: int = 500,
    max_per_actor: int = 100,
) -> list[dict]:
    """Require sorted event times and alert only on true threshold crossings."""
    bounds = (window_seconds, threshold, max_actors, max_per_actor)
    if any(type(x) is not int or x < 1 for x in bounds):
        raise ValueError("positive integer bounds required")
    if threshold > max_per_actor:
        raise ValueError("threshold exceeds per-actor capacity")
    if type(events) is not list or len(events) > MAX_RECORDS:
        raise ValueError("event count cap")
    windows: dict[tuple[str, str], deque[Event]] = {}
    active: set[tuple[str, str]] = set()
    previous = None
    alerts = []
    window = timedelta(seconds=window_seconds)
    for event in events:
        if type(event) is not Event:
            raise ValueError("expected normalized Event")
        if previous is not None and event.timestamp_utc < previous:
            raise ValueError("out-of-order event time; analysis incomplete")
        previous = event.timestamp_utc
        if event.action != "login_failure":
            continue
        identity = (event.source, event.actor)
        if identity not in windows:
            if len(windows) >= max_actors:
                raise ValueError("actor cardinality cap; analysis incomplete")
            windows[identity] = deque()
        queue = windows[identity]
        while queue and event.timestamp_utc - queue[0].timestamp_utc > window:
            queue.popleft()
        if len(queue) >= max_per_actor:
            raise ValueError("per-actor queue cap; analysis incomplete")
        queue.append(event)
        if len(queue) < threshold:
            active.discard(identity)
        if len(queue) >= threshold and identity not in active:
            active.add(identity)
            alerts.append({
                "classification": "review",
                "source": event.source,
                "actor": event.actor,
                "threshold": threshold,
                "window_seconds": window_seconds,
                "trigger_time_utc": event.timestamp_utc.isoformat(),
                "supporting_event_ids": [
                    f"{member.source}:{member.event_id}" for member in queue
                ],
            })
    return alerts


def analyze(
    path: Path, *,
    window_seconds: int = 60,
    threshold: int = 3,
    max_records: int = MAX_RECORDS,
) -> dict:
    events, duplicates, source_hash = read_events(path, max_records=max_records)
    alerts = detect(
        events, window_seconds=window_seconds, threshold=threshold
    )
    return {
        "complete": True,
        "source_sha256": source_hash,
        "unique_events": len(events),
        "duplicate_events": duplicates,
        "alerts": alerts,
        "limitations": "Synthetic review candidates; not evidence of compromise.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--window-seconds", type=int, default=60)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS)
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("input and output cannot refer to the same file")
        report = analyze(
            args.input,
            window_seconds=args.window_seconds,
            threshold=args.threshold,
            max_records=args.max_records,
        )
        atomic_json_report(args.output, report)
    except (ValueError, OSError) as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(f"COMPLETE: {len(report['alerts'])} synthetic review candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
