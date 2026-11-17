"""Project 3: cross-source synthetic incident timeline and provenance.

Two invented providers:
  lab-linux: {"provider":"lab-linux","event_id":"...", "time":"...Z",
              "actor":"...", "kind":"failure"|"success"}
  lab-windows: {"provider":"lab-windows","event_id":"...", "time":"...+07:00",
                "actor":"...", "event_code":1001|1002}

The numbers are NOT real Windows event IDs. No privileged collection occurs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

MAX_LINE_BYTES = 8192
MAX_RECORDS = 10_000


def _unique_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate key: {name}")
        result[name] = value
    return result


def _event(row: object, source_name: str, line: int) -> dict:
    if type(row) is not dict:
        raise ValueError("event must be a JSON object")
    provider = row.get("provider")
    if provider == "lab-linux":
        keys = {"provider","event_id","time","actor","kind"}
        mapping = {"failure":"authentication_failure","success":"authentication_success"}
        if set(row) != keys or row["kind"] not in mapping:
            raise ValueError("invalid lab-linux event")
        action = mapping[row["kind"]]
    elif provider == "lab-windows":
        keys = {"provider","event_id","time","actor","event_code"}
        mapping = {1001:"authentication_failure",1002:"authentication_success"}
        if set(row) != keys or type(row["event_code"]) is not int or row["event_code"] not in mapping:
            raise ValueError("invalid lab-windows event")
        action = mapping[row["event_code"]]
    else:
        raise ValueError("unknown toy provider")

    for key in ("provider","event_id","time","actor"):
        value = row[key]
        if type(value) is not str or not 1 <= len(value) <= 128:
            raise ValueError(f"invalid {key}")
    try:
        when = datetime.fromisoformat(row["time"].replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO timestamp") from exc
    if when.utcoffset() is None:
        raise ValueError("timezone is required")
    return {
        "source_file":source_name, "source_line":line,
        "provider":provider, "event_id":row["event_id"],
        "time_original":row["time"],
        "time_utc":when.astimezone(timezone.utc).isoformat(),
        "actor":row["actor"],"action":action,
    }


def build_timeline(paths: list[Path], *, max_records: int=MAX_RECORDS) -> dict:
    if type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS:
        raise ValueError("invalid max_records")
    if not paths:
        raise ValueError("at least one input required")
    events = []
    sources = []
    identities = set()
    for path in paths:
        h = sha256()
        with path.open("rb") as stream:
            line=0
            while True:
                raw = stream.readline(MAX_LINE_BYTES+1)
                if not raw:
                    break
                h.update(raw)
                line += 1
                if len(raw) > MAX_LINE_BYTES:
                    raise ValueError(f"{path.name}:{line}: line too long")
                if not raw.strip():
                    continue
                if len(events) >= max_records:
                    raise ValueError("record cap exceeded")
                try:
                    row=json.loads(raw.decode("utf-8","strict"),
                                   object_pairs_hook=_unique_keys)
                    ev=_event(row, path.name, line)
                except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as exc:
                    raise ValueError(f"{path.name}:{line}: malformed event") from exc
                identity=(ev["provider"],ev["event_id"])
                if identity in identities:
                    raise ValueError(f"{path.name}:{line}: duplicate provider/event ID")
                identities.add(identity)
                events.append(ev)
        sources.append({"name":path.name,"sha256":h.hexdigest(),"lines":line})
    events.sort(key=lambda ev:(ev["time_utc"],ev["source_file"],ev["source_line"]))
    return {"complete":True,"sources":sources,"events":events,
            "limitations":"Synthetic events; source clocks and identities not authenticated"}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths",type=Path,nargs="+")
    args=parser.parse_args(argv)
    try:
        result=build_timeline(args.paths)
    except (ValueError,OSError) as exc:
        print(f"timeline incomplete: {exc}",file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
