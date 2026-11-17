"""Project 2: offline synthetic IP-indicator normalization and expiry.

Usage:
 python -m projects.builds.indicator_quality fixtures/project-indicators.jsonl

This example intentionally accepts only its own documented toy schema.
No live reputation lookups, network connections, or blocking actions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import ipaddress
import json
from pathlib import Path
import sys

MAX_LINE_BYTES = 8192
MAX_RECORDS = 1000


def _iso_time(value: object) -> datetime:
    if type(value) is not str or not 1 <= len(value) <= 64:
        raise ValueError("timestamp type or size")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO timestamp") from exc
    if dt.utcoffset() is None:
        raise ValueError("timezone offset required")
    return dt.astimezone(timezone.utc)


def normalize(record: dict, *, as_of: datetime) -> dict:
    """Normalize an indicator without claiming it is malicious."""
    if type(record) is not dict or set(record) != {
        "ip","source","observed_at","ttl_days","confidence"
    }:
        raise ValueError("indicator fields mismatch")
    source = record["source"]
    if type(source) is not str or not 1 <= len(source) <= 128:
        raise ValueError("bad source")
    ip = record["ip"]
    if type(ip) is not str or not 1 <= len(ip) <= 64:
        raise ValueError("bad IP")
    try:
        canonical = str(ipaddress.ip_address(ip))
    except ValueError as exc:
        raise ValueError("invalid IP address") from exc
    observed = _iso_time(record["observed_at"])
    ttl = record["ttl_days"]
    if type(ttl) is not int or not 1 <= ttl <= 365:
        raise ValueError("TTL out of range")
    if record["confidence"] not in ("low","medium","high"):
        raise ValueError("unrecognized confidence label")
    if as_of.utcoffset() is None:
        raise ValueError("as_of must have timezone")
    expires = observed + timedelta(days=ttl)
    return {
        "ip": canonical, "source": source,
        "observed_at_utc": observed.isoformat(),
        "expires_at_utc": expires.isoformat(),
        "confidence": record["confidence"],
        "expired": as_of.astimezone(timezone.utc) >= expires,
    }


def ingest(path: Path, *, as_of: datetime, max_records: int = MAX_RECORDS) -> dict:
    if type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS:
        raise ValueError("record cap invalid")
    unique = {}
    duplicates = 0
    count = 0
    with path.open("rb") as stream:
        while True:
            raw = stream.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAX_LINE_BYTES:
                raise ValueError(f"line {count+1}: byte cap exceeded")
            if not raw.strip():
                continue
            count += 1
            if count > max_records:
                raise ValueError("record cap exceeded")
            try:
                record = normalize(json.loads(raw.decode("utf-8", "strict")),
                                   as_of=as_of)
            except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as exc:
                raise ValueError(f"line {count}: invalid indicator") from exc
            key = (record["source"],record["ip"])
            if key in unique:
                duplicates += 1
                # No silent overwriting: conflicting records are not conflated.
                if unique[key] != record:
                    raise ValueError(f"line {count}: conflicting source indicator")
                continue
            unique[key] = record
    return {"complete":True,"input_records":count,"duplicates":duplicates,
            "indicators":list(unique.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path",type=Path)
    parser.add_argument("--as-of",default="2026-01-01T00:00:00Z",
                        help="explicit UTC/offset comparison instant")
    args = parser.parse_args(argv)
    try:
        report = ingest(args.path, as_of=_iso_time(args.as_of))
    except (ValueError,OSError) as exc:
        print(f"incomplete normalization: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
