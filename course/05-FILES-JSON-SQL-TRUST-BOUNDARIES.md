# Deep Dive 05 — Files, JSONL, SQL, timestamps and data trust boundaries

> **Hands-on:** [Chapter 05 Guided Lab](../lab-manual/05-GUIDED-LAB.md) · [100 numbered worked answers](../solutions/by-exercise/README.md). Complete the lab's negative tests before moving on.

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


## 10. Detailed ingestion case study: source data, validation and a transaction

Consider a source that sends the following synthetic lines:

```json
{"event_id":"A1","timestamp":"2026-01-01T10:00:00Z","actor":"alice","action":"login_failure"}
{"event_id":"A2","timestamp":"2026-01-01T17:01:00+07:00","actor":"alice","action":"login_success"}
```

A robust pipeline distinguishes five stages: **bytes → decoded text → parsed JSON → validated event → committed database record**. Each stage can fail for different reasons, so the program must not report success when the input was only partially processed.

### A streaming and transactional example

```python
from pathlib import Path
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

MAX_LINE = 8192

def bounded_records(path: Path):
    with path.open("rb") as stream:
        number = 0
        while True:
            raw = stream.readline(MAX_LINE + 1)
            if not raw:
                break
            number += 1
            if len(raw) > MAX_LINE:
                raise ValueError(f"line {number}: too many bytes")
            try:
                record = json.loads(raw.decode("utf-8", "strict"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"line {number}: bad JSON/UTF-8") from exc
            if type(record) is not dict:
                raise ValueError(f"line {number}: object required")
            yield number, record

def validated_event(row: dict) -> tuple[str, str, str, str]:
    required = {"event_id", "timestamp", "actor", "action"}
    if set(row) != required:
        raise ValueError("exact schema required")
    if any(type(row[k]) is not str for k in required):
        raise ValueError("all fields must be strings")
    if not 1 <= len(row["event_id"]) <= 64:
        raise ValueError("bad event id")
    if not 1 <= len(row["actor"]) <= 64:
        raise ValueError("bad actor")
    if row["action"] not in ("login_failure", "login_success"):
        raise ValueError("unsupported action")
    when = datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("timezone required")
    return (row["event_id"], when.astimezone(timezone.utc).isoformat(),
            row["actor"], row["action"])

def import_events(path: Path, connection: sqlite3.Connection):
    with connection:  # rollback all writes if any row fails
        connection.execute("""CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL
        )""")
        for line_number, raw in bounded_records(path):
            try:
                values = validated_event(raw)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"line {line_number}: invalid event") from exc
            connection.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?)", values
            )
```

The example intentionally aborts on the first malformed row. An existing duplicate ID also aborts the transaction with a SQLite integrity error; it does *not* silently overwrite prior evidence. The caller owns the connection and must close it. A real service also needs total record caps, parser nesting controls, access control, preservation of original bytes, and an idempotent replay policy.

**Subtle point:** the `with connection:` context manager handles transaction commit/rollback but does not close the connection. Use `contextlib.closing` or an explicit lifecycle.

## 11. Source authenticity and ambiguity

Even impeccably parsed JSON may be false evidence. An attacker could place text in the actor field, alter clocks, or cause a legitimate process to log a misleading message. Therefore:
- Preserve a source identifier and checksum of original input.
- Record both source-event time and ingestion time.
- Normalize schema fields without silently changing identity meaning.
- Track rejected rows and duplicates.
- Validate who is authorized to submit data; a valid JSON payload is not an authenticated event.

A **valid** record is not the same as a **true** record.

### Broken assumptions checklist

| Mistaken assumption | Why it fails | Mitigation |
|---|---|---|
| "JSON means safe" | data types and nesting may be hostile | bounded strict schema |
| "UTF-8 characters = bytes" | multibyte encodings | cap raw bytes |
| "CSV quoting prevents formulas" | spreadsheets may evaluate formula cells | consumer-specific export |
| "Path within root is secure" | symlink/TOCTOU races | file-descriptor-based controls |
| "SQLite transaction closes connection" | it does not | explicit close |
| "A unique event ID proves provenance" | IDs may be attacker-controlled | source qualification and authentication |

## 12. Exercise set with verification

**A:** Create a three-line file where the third line is malformed. Import it into an empty SQLite connection. A correct all-or-nothing transaction should leave no event rows after rollback (table creation timing may depend on schema handling).

**B:** Introduce a byte-order-mark at the beginning of a UTF-8 file. Decide explicitly whether your format allows BOM; test `utf-8` versus `utf-8-sig` behavior and document why arbitrary normalization can change evidence.

**C:** Add a source-qualified key `(source,event_id)` rather than global `event_id`. Explain why two logging systems could legitimately reuse local IDs.

**D:** Extend the example to store `original_timestamp` and `ingest_time_utc`. Prove that timestamps from +07:00 and Z can represent the same instant.

**E:** Write a test for an array or bool where a dictionary was required. Ensure you get a clear error rather than a silent skipped record.

For more on current input-validation principles, read [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).
