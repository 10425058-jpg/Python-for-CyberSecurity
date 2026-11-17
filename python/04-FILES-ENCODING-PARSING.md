# 04 — Files, binary data, parsing and evidence hygiene
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [bytes encoding binary parsers](../course/04-BYTES-ENCODING-BINARY-PARSERS.md) · [files json sql trust boundaries](../course/05-FILES-JSON-SQL-TRUST-BOUNDARIES.md).


> **More detail:** [Regex, Unicode and hostile log-text parsing](../course/22-REGEX-UNTRUSTED-TEXT.md).


## Extended textbook 04 — From a byte on disk to a trustworthy parsed record

### 4.1 Files have bytes; text is an interpretation

A filesystem stores byte sequences and metadata. When you use `open(path, "rb")`, Python yields raw bytes; when you use `open(path, "r", encoding="utf-8")`, Python decodes bytes into Unicode text. A **codec** is the rule for conversion. `"ignore"` and `"replace"` error handling can destroy exact forensic evidence, so use strict decoding and keep a reference to the original bytes.

A **path** names a possible filesystem object; it is not evidence the file exists, is a regular file or is safe to read. `Path.is_file()` can change between checking and opening, and symlinks can redirect access. In adversarial environments, filesystem safety requires carefully scoped roots and often OS-specific handle-based protections. In our exercises, use only owned temporary directories.

| Mode | Input/output type | Intended use | Pitfall |
|---|---|---|---|
| `"rb"` | `bytes` | hashes, packets, evidence | decode is separate |
| `"r"` | `str` | validated UTF-8 text | encoding must be explicit |
| `"wb"` | `bytes` | generated binary artifacts | truncates existing file |
| `"x"` | text file | create without overwrite | still requires safe path policy |
| `"a"` | text file | append | not a cross-process transaction |

### 4.2 Read in bounded chunks, not unlimited lines

`read()` without a size can allocate memory equal to the entire file. `readline(max_bytes + 1)` in binary mode lets you detect an oversized record before loading an unbounded line. You need limits at several layers: overall file size, individual line size, JSON nesting/field lengths, number of distinct identities, output size and elapsed time.

The hash of the original bytes supports **integrity comparison** only against a trusted reference; it does not prove who created a file. The same report should record acquisition method and original input reference.

### 4.3 JSON, CSV and binary headers are different grammars

**JSON** can encode objects, arrays, strings, numbers, booleans and null. Python's `json.loads` is convenient but its defaults accept duplicate keys by retaining the last value, and it accepts `NaN` and `Infinity` in some cases. A security-oriented schema may need to reject these. **CSV** requires quoting rules; simple `line.split(",")` fails when quoted fields contain commas or newlines. **Binary protocols** use byte offsets, endianness and declared payload lengths; a decoded length is not trustworthy until checked against a cap and the actual buffer.

### 4.4 Complete lab — strict JSONL, original hashes and safe failure

```python
# TEXTBOOK_RUNNABLE
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json

MAX_LINE_BYTES = 512

def no_duplicate_keys(pairs):
    found = {}
    for key, value in pairs:
        if key in found:
            raise ValueError(f"duplicate key: {key}")
        found[key] = value
    return found

def reject_non_json_constant(value):
    raise ValueError(f"nonstandard numeric constant: {value}")

def validated_record(raw: bytes) -> dict:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_LINE_BYTES:
        raise ValueError("line byte cap")
    try:
        data = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=no_duplicate_keys,
            parse_constant=reject_non_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed encoded JSON") from exc
    if type(data) is not dict or set(data) != {"actor", "failures"}:
        raise ValueError("schema mismatch")
    if type(data["actor"]) is not str or not 1 <= len(data["actor"]) <= 40:
        raise ValueError("invalid actor")
    if type(data["failures"]) is not int or not 0 <= data["failures"] <= 100:
        raise ValueError("invalid failures")
    return data

def read_complete(path: Path) -> tuple[list[dict], str]:
    digest = sha256()
    collected = []
    with path.open("rb") as source:
        while True:
            raw = source.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            if len(raw) > MAX_LINE_BYTES:
                raise ValueError("oversized line")
            digest.update(raw)
            collected.append(validated_record(raw))
            if len(collected) > 100:
                raise ValueError("too many records")
    return collected, digest.hexdigest()

with TemporaryDirectory() as temporary:
    path = Path(temporary) / "auth.jsonl"
    path.write_bytes(b'{"actor":"alex","failures":3}\n')
    events, original_hash = read_complete(path)
    assert events == [{"actor": "alex", "failures": 3}]
    assert len(original_hash) == 64
    for wrong in (
        b'{"actor":"a","failures":true}',
        b'{"actor":"a","failures":2,"failures":3}',
        b'{"actor":"a","failures":NaN}',
        b"\xff",
    ):
        try:
            validated_record(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid record accepted")
print("LAB 04 PASS")
```

**Walkthrough:** The binary line reader bounds allocations *before* decoding. UTF-8 decoding is strict. JSON rejects ambiguous duplicate keys and non-standard constants. The schema verifies exact keys, types, length and number range. Only validated objects are added to the returned list. The hash covers exact line bytes encountered. **Important limitation:** the example keeps up to 100 records in memory and hashes no lines after a validation failure; it is a teaching parser, not a complete acquisition system.

### 4.5 Time is another parsing boundary

`datetime.fromisoformat` parses ISO-like timestamps, but a timestamp without an explicit offset should not silently be interpreted as UTC. Convert aware timestamps using `astimezone(timezone.utc)` while preserving the original string. **Event time** (source claim) and **ingest time** (collector observation) are separate. Clock skew means even normalized UTC values can be uncertain.

### 4.6 Safe output and atomicity

Do not overwrite a complete report while still parsing an incomplete file. For local files, one strategy is to write a temporary file **in the destination directory**, flush and optionally fsync as required, then atomically replace the destination on supported filesystems. Atomic rename is not a guarantee of full crash durability, transactionality across several files or preserved permissions. Database transactions provide a different boundary; review both.

### 4.7 Exercises and reasoning prompts

**Beginner:** Explain why `len("é")` and `len("é".encode("utf-8"))` differ. Draw a six-byte binary header with big-endian length. **Intermediate:** Write a CSV reader that rejects missing columns and demonstrates quoted commas; write an oversized JSONL test. **Advanced:** Refactor `read_complete` to stream without retaining all records, use staged output, and prove a bad record after valid events cannot publish a complete report.

**Checkpoint:** distinguish original evidence vs normalized output, exact bytes vs visible characters, lexical parsing vs semantic validation, and a hash comparison vs proof of source authenticity.

## File handling
Use `pathlib.Path` and context managers. Text and bytes are different: `read_text(encoding="utf-8")`, `read_bytes()`, streaming with `open(..., encoding="utf-8")`. Ensure you have permission and avoid modifying originals when processing forensic artifacts.

```python
from pathlib import Path
import hashlib

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()
```
A digest supports integrity checks but **does not by itself prove who created the file**, nor whether it is malicious.

## Structured formats
- JSON / JSON Lines: `json.loads`, `json.dumps`. Validate expected keys and types; avoid loading unbounded files into memory.
- CSV: `csv.DictReader` with explicit encoding and newline handling. CSV formula injection is a concern when exporting data for spreadsheets; escape cells that start with formula-like prefixes according to consumer requirements.
- INI: `configparser`; TOML: `tomllib` (read-only); XML: use hardened parsers when handling untrusted XML and heed entity/expansion risks.
- YAML: if using PyYAML, `yaml.safe_load` instead of loading arbitrary Python objects. Even safe parsers require size/depth limits.
- Archives: beware zip-slip path traversal, symlinks, decompression bombs, and file-name ambiguity. Do not blindly extract third-party archives.

## Reading timestamps
Log timestamps may have missing offsets, daylight-saving ambiguity, or inconsistent clocks. Convert aware times to UTC, retain source timezone/precision, and record collection time separately.

```python
from datetime import datetime, timezone
when = datetime.fromisoformat("2026-01-05T12:00:00+07:00")
utc = when.astimezone(timezone.utc)
assert utc.utcoffset().total_seconds() == 0
```

## Bytes and binary analysis
`bytes`, `bytearray`, `memoryview`, `struct.pack/unpack`, `int.from_bytes`, Base64, hex, endianness and offsets are foundational for packets, executables and artifacts. Base64 is **encoding, not encryption**.

```python
import struct
header = struct.pack("!HI", 443, 1024)  # network-endian unsigned short + int
port, length = struct.unpack("!HI", header)
assert (port, length) == (443, 1024)
```

## Reliable parser checklist
1. Restrict maximum file size and record length.
2. Parse without executing data.
3. Check types and bounds.
4. Normalize only when doing so preserves intended semantics.
5. Record malformed rows separately, without silently discarding evidence.
6. Emit structured reports with hashes and tool versions.
7. Test empty, corrupt, truncated, duplicated and hostile inputs.

## Exercises
- Hash a 1 GB synthetic file using constant memory.
- Stream JSONL records, count parse errors, retain line numbers.
- Parse a simple 6-byte binary header and reject truncated headers.
- Explain why file hash, timestamp, custody record, and source metadata play different roles.
