"""Self-contained, standard-library examples for third-edition chapter expansions.

All data are synthetic. No remote network calls and no privileged actions.
These are audited learning examples, not production security services.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_non_json_constant(token: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {token}")


def _strict_object(raw: bytes, max_bytes: int = 8192) -> dict:
    if type(raw) is not bytes or len(raw) > max_bytes:
        raise ValueError("expected bounded bytes")
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_non_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON") from exc
    if type(value) is not dict:
        raise ValueError("expected JSON object")
    return value


@dataclass(frozen=True)
class LoginPolicy:
    enabled: bool
    max_attempts: int
    user: str


def parse_login_policy(raw: bytes) -> LoginPolicy:
    obj = _strict_object(raw, max_bytes=2048)
    if set(obj) != {"enabled", "max_attempts", "user"}:
        raise ValueError("wrong policy fields")
    if type(obj["enabled"]) is not bool:
        raise ValueError("enabled must be bool")
    if type(obj["max_attempts"]) is not int or not 1 <= obj["max_attempts"] <= 20:
        raise ValueError("max_attempts must be int 1..20")
    if type(obj["user"]) is not str or not 1 <= len(obj["user"]) <= 64:
        raise ValueError("user must be short nonempty text")
    return LoginPolicy(
        enabled=obj["enabled"],
        max_attempts=obj["max_attempts"],
        user=obj["user"],
    )


LAB_LOG_PATTERN = re.compile(
    r"time=(?P<timestamp>[0-9T:+.Z-]{1,40}) "
    r"user=(?P<user>[A-Za-z0-9_.-]{1,64}) "
    r"action=(?P<action>login_failure|login_success)"
)


def parse_toy_log(line: str) -> dict[str, str]:
    if type(line) is not str or not 1 <= len(line) <= 160:
        raise ValueError("line length/type invalid")
    match = LAB_LOG_PATTERN.fullmatch(line)
    if match is None:
        raise ValueError("line not in toy log format")
    fields = match.groupdict()
    try:
        when = datetime.fromisoformat(fields["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp syntax invalid") from exc
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("timezone required")
    return {
        "time_utc": when.astimezone(timezone.utc).isoformat(),
        "actor": fields["user"],
        "action": fields["action"],
    }


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    permissions: frozenset[str]


@dataclass(frozen=True)
class Report:
    report_id: str
    tenant: str
    owner: str
    classification: str


def can_read(principal: Principal, report: Report) -> bool:
    """Pure illustrative authorization policy, not a verified identity provider."""
    if principal.tenant != report.tenant:
        return False
    if report.owner == principal.subject:
        return "report:read-own" in principal.permissions
    return (
        "report:read-org" in principal.permissions
        and report.classification == "organization"
    )


def detection_metrics(tp: int, fp: int, fn: int, tn: int) -> dict[str, float | None]:
    counts = (tp, fp, fn, tn)
    if any(type(n) is not int or n < 0 for n in counts):
        raise ValueError("counts must be nonnegative integers")
    return {
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def _normalized_event(raw: bytes, *, line: int) -> tuple[str, str, str, str, str]:
    obj = _strict_object(raw)
    fields = {"event_id", "source", "timestamp", "actor", "action"}
    if set(obj) != fields:
        raise ValueError(f"line {line}: incorrect event fields")
    if any(type(obj[k]) is not str for k in fields):
        raise ValueError(f"line {line}: expected string fields")
    for field in ("event_id", "source", "actor"):
        if not 1 <= len(obj[field]) <= 64:
            raise ValueError(f"line {line}: bad {field}")
    if obj["action"] not in ("login_failure", "login_success"):
        raise ValueError(f"line {line}: invalid action")
    try:
        when = datetime.fromisoformat(obj["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {line}: invalid timestamp") from exc
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError(f"line {line}: timezone required")
    return (
        obj["source"], obj["event_id"],
        when.astimezone(timezone.utc).isoformat(),
        obj["actor"], obj["action"],
    )


def import_synthetic_jsonl(
    path: Path, connection: sqlite3.Connection, *, max_records: int = 1000
) -> int:
    """All-or-nothing sample import into a caller-owned SQLite connection.

    - A table is created before the import transaction.
    - Any malformed/duplicate record raises and rolls back all imported rows.
    - The connection lifecycle belongs to the caller.
    - Pre-existing records remain untouched after failure.
    """
    if type(max_records) is not int or not 1 <= max_records <= 100_000:
        raise ValueError("invalid record limit")
    connection.execute(
        """CREATE TABLE IF NOT EXISTS auth_events (
            source TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_time_utc TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            PRIMARY KEY (source, event_id)
        )"""
    )
    connection.commit()
    count = 0
    with connection:
        with path.open("rb") as stream:
            while True:
                raw = stream.readline(8193)
                if not raw:
                    break
                if len(raw) > 8192:
                    raise ValueError(f"line {count + 1}: too many bytes")
                if not raw.strip():
                    continue
                count += 1
                if count > max_records:
                    raise ValueError("record limit exceeded")
                record = _normalized_event(raw, line=count)
                connection.execute(
                    "INSERT INTO auth_events VALUES (?, ?, ?, ?, ?)", record
                )
    return count


if __name__ == "__main__":
    policy = parse_login_policy(
        b'{"enabled":true,"max_attempts":5,"user":"alex"}'
    )
    print("Validated policy:", policy)
    print("Local log:", parse_toy_log(
        "time=2026-01-01T17:00:00+07:00 user=alex action=login_failure"
    ))
    print("Toy metrics:", detection_metrics(8, 9, 2, 81))
