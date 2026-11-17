# Deep Dive 05 — Files, JSONL, SQL, timestamps and data trust boundaries

**Level:** intermediate · **Estimated study:** 9–12 hours.

## Scenario
A security operations team exports several JSONL files every morning. Each file includes authentication events, but records may be duplicated, corrupted, truncated or timestamped in different zones. You need to build an ingest process that preserves meaning, provides error evidence and does not run unsafe operations.

## 1. Treat external data as hostile until validated

A trust boundary exists whenever data crosses from an uncontrolled source into logic you rely on: disk → parser; API → JSON model; user input → SQL; database → HTML; log record → shell invocation. A familiar file extension does **not** make content safe. Applying a parser is not validation.

Write a contract *before* code:
- Maximum file size / record length.
- Expected encoding (UTF-8, strict).
- Expected document shape (a JSON object per line).
- Required fields and allowed types/ranges.
- Timestamp format and timezone requirement.
- Allowed actions and identifier lengths.
- Error policy (reject whole file, quarantine row, or partial ingest with audit).
- Confidentiality classification and retention.

## 2. Streaming files with context managers

```python
from pathlib import Path

def iter_lines(path: Path, *, max_chars: int = 16_384):
    if max_chars < 1:
        raise ValueError("invalid line limit")
    with path.open("r", encoding="utf-8", errors="strict") as source:
        for line_number, line in enumerate(source, 1):
            if len(line) > max_chars:
                raise ValueError(f"line {line_number}: exceeds cap")
            if line.strip():
                yield line_number, line
```

**Important nuance:** this checks the line *after the file iterator reads it*; Python may already allocate a giant line. If processing adversarial huge files, use a bounded `readline(max_chars + 1)` loop on a binary stream and enforce per-record byte length before decoding. UTF-8 character length and byte length differ.

```python
def bounded_utf8_lines(path: Path, max_bytes: int = 16_384):
    with path.open("rb") as stream:
        number = 0
        while True:
            chunk = stream.readline(max_bytes + 1)
            if not chunk:
                return
            number += 1
            if len(chunk) > max_bytes or not chunk.endswith(b"\n"):
                raise ValueError(f"line {number}: too long or no terminator")
            try:
                yield number, chunk.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise ValueError(f"line {number}: invalid UTF-8") from exc
```

This simplified strict format requires every record (including the last) to end in a newline. Such a constraint may be desirable for a controlled log exchange but must be documented; otherwise intentionally allow a final unterminated line with a separate bounded rule.

## 3. JSON and JSONL parsing

JSON stores values such as strings, numbers, booleans, arrays, objects and null. JSON does not automatically enforce schemas. Duplicate keys can occur in raw JSON text; Python's default `json.loads` keeps the last key, which can mask ambiguous input.

```python
import json

def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key!r}")
        result[key] = value
    return result

def parse_strict_json_object(raw: str) -> dict:
    value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("top-level object required")
    return value

assert parse_strict_json_object('{"ok":true}') == {"ok": True}
```

JSON parsers also need limits on nesting, recursion, length and time. Parsing extremely deep data may fail with `RecursionError`; handle resource budgets externally, not only in schema code.

### Normalize events without discarding originals
```python
from datetime import datetime, timezone

def normalize_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError("timestamp must be text")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO8601 timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)

assert normalize_timestamp("2026-01-01T07:00:00+07:00").isoformat() == "2026-01-01T00:00:00+00:00"
```

Keep `timestamp_original`, `timestamp_utc` and `ingest_timestamp_utc` as distinct fields. Clock drift, delayed delivery and daylight-saving transitions complicate incident timelines.

## 4. CSV handling and spreadsheet-formula injection

`csv.DictReader` handles quoting and commas but does not enforce type/length. When exporting data for users who may open it in spreadsheet applications, cells beginning with formula prefixes such as `=`, `+`, `-` and `@` may be interpreted as formulas. Escaping strategy depends on the target consumer; prepend an apostrophe or otherwise use a trusted exporter policy, and test with the actual application. Simply quoting a CSV cell does not always prevent formula evaluation.

```python
def neutralize_for_spreadsheet(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("expected text")
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return "'" + value
    return value
```

This is an illustrative mitigation, not a universal guarantee across all spreadsheet software and data transformations. The safest route for automated pipelines is a machine-readable output never interpreted as a formula.

## 5. SQL with SQLite: separating data from SQL code

SQL injection occurs when untrusted text changes SQL syntax rather than being treated as a value. Always use placeholders for values. SQL identifiers (table names, column names) cannot generally be parameterized and must come from a small allowlist.

```python
import sqlite3
from contextlib import closing

with closing(sqlite3.connect(":memory:")) as connection:
    with connection:
        connection.execute(
            "CREATE TABLE events (event_id TEXT PRIMARY KEY, actor TEXT, action TEXT)"
        )
        connection.execute(
            "INSERT INTO events VALUES (?, ?, ?)",
            ("e-1", "alice", "login_failure")
        )
    user_supplied = "alice' OR 1=1 --"
    rows = connection.execute(
        "SELECT event_id FROM events WHERE actor = ?", (user_supplied,)
    ).fetchall()
    assert rows == []
```

### Transactions and idempotency
A transaction groups changes so they commit or roll back together. Set a unique `event_id` when stable IDs exist. On replay, choose intentionally whether to ignore duplicate IDs, update records, or retain a duplicate evidence entry. Each policy has tradeoffs and should be documented.

```python
# Deliberate idempotent insert for immutable, trusted event IDs:
# INSERT OR IGNORE INTO events(event_id, actor, action) VALUES (?, ?, ?)
```

Never silently use `INSERT OR REPLACE` for evidentiary originals: it deletes/replaces earlier rows and can destroy provenance.

## 6. Paths, symlinks and archives

`Path.resolve()`, `is_relative_to()` and allowlisted roots help ordinary path validation, but **check-then-open races** remain possible if an attacker can change directories/symlinks. For high-risk operations use platform-specific fd-relative operations, permissions and isolated storage. An attacker-controlled archive may contain `../` names, absolute paths, symbolic links or decompression bombs. Metadata inspection alone does not prove safe extraction.

Use `tempfile` and atomic rename where practical for report files. Avoid overwriting source evidence; store derived artifacts under a separate directory.

## 7. Worked pipeline architecture

```text
untrusted JSONL
   ↓ [limit bytes, strict UTF-8]
parse JSON (reject duplicate keys)
   ↓ [validate exact schema]
normalize times and actor identifiers
   ↓ [append processing decision + original hash reference]
SQLite staging transaction
   ↓ [dedup policy + audit]
detector / query
   ↓ [redacted, structured report]
analyst review
```

**Threats:** malformed input, enormous records, duplicate identities, ambiguous timestamps, sensitive data in errors, partial output, accidental source overwrites, under-scoped privileges. Controls should address each threat individually.

## 8. Lab: compare data quality across batches
1. Copy `fixtures/synthetic-auth.jsonl` to a temporary location.
2. Create controlled mistakes: a duplicate event, an invalid timestamp, an oversized actor and duplicate JSON keys.
3. Decide and document policy for each: reject, quarantine, or accept with flag.
4. Parse into structured events, capture error counts and line numbers.
5. Generate counts and verify no data was silently discarded.
6. Create a read-only output report preserving provenance to each original line.

**Expected outcome:** the same input always generates the same normalized output and error report. The program should never execute input content.

## 9. Questions and answer checks
1. Why does `len(str)` not reliably impose a byte-size cap? *Because UTF-8 code points use varying byte counts.*
2. Why does `DictReader` not validate an event schema? *It parses columns but does not enforce semantic rules.*
3. Why is `actor=?` preferable to concatenating strings? *The database treats the value as data.*
4. Why is `Path.resolve()` not a full defense against malicious concurrent filesystem changes? *Paths can change between checking and opening.*
5. Why preserve the original timestamp? *Normalization may hide source ambiguity and clock errors.*

**References:** [json](https://docs.python.org/3/library/json.html), [csv](https://docs.python.org/3/library/csv.html), [sqlite3](https://docs.python.org/3/library/sqlite3.html), [OWASP Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html).
