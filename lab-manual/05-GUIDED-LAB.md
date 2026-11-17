# Lab 05 — Streaming JSONL with SQLite transaction rollback

**Paired lesson:** [Chapter 05](../course/05-FILES-JSON-SQL-TRUST-BOUNDARIES.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A nightly security feed has valid events followed by one malformed row; no partial batch may be committed as complete.

**By the end:** Demonstrate all-or-nothing import and provenance-aware source identifiers.

**Input or assumptions:** Synthetic JSONL with event_id, source, timestamp, actor, action

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_05.py` **in a temporary working directory** and run `python lab_05.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
import sqlite3, tempfile
from pathlib import Path
from examples.chapter_cases import import_synthetic_jsonl

good = b'{"source":"lab","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"login_failure"}\n'
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "events.jsonl"
    conn = sqlite3.connect(":memory:")
    try:
        p.write_bytes(good + b"not-json\n")
        try:
            import_synthetic_jsonl(p, conn)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid batch accepted")
        assert conn.execute("SELECT count(*) FROM auth_events").fetchone()[0] == 0
        p.write_bytes(good)
        assert import_synthetic_jsonl(p, conn) == 1
        print("PASS: atomic import and recovery")
    finally:
        conn.close()
```

**Expected terminal signal:** `PASS: atomic import and recovery`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. A caller-owned connection wraps inserts in a transaction.
2. The malformed second row raises; the earlier insert is rolled back.
3. A subsequent correct batch inserts one row; the primary key prevents accidental replay duplication.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Duplicate an existing (source,event_id); expect sqlite3.IntegrityError.
2. Exceed 8192 bytes on one line; expect ValueError.
3. Use timestamp without offset; expect rejected input.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

A transaction gives all-or-nothing database writes, not input authenticity. Preserve original evidence and report failures visibly.

### Security review

Do not silently overwrite existing rows or call a partially ingested log clean.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
