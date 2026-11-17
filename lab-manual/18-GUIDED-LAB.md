# Lab 18 — Mini-SOC integration: ingest, detect, evaluate, report

**Companion:** [Deep Dive Chapter 18](../course/18-MINI-SOC-CAPSTONE-BLUEPRINT.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

A security analyst receives synthetic JSONL and must produce explainable review candidates without automatically disabling any account.

**Learning goal:** Run the existing offline mini SOC as a full artifact pipeline and verify incomplete-ingest behavior.

**Input assumptions:** fixtures/synthetic-auth.jsonl and local output in a temporary directory. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_18.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
import json
import tempfile
from pathlib import Path
from examples.mini_soc_pipeline import write_findings_atomic

with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    src = folder / "events.jsonl"
    dst = folder / "alerts.jsonl"
    src.write_bytes(
        b'{"source":"lab","event_id":"a","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"login_failure"}\n'
        b'{"source":"lab","event_id":"b","timestamp":"2026-01-01T10:01:00Z","actor":"alex","action":"login_failure"}\n'
        b'{"source":"lab","event_id":"c","timestamp":"2026-01-01T10:02:00Z","actor":"alex","action":"login_failure"}\n'
    )
    assert write_findings_atomic(src, dst, threshold=3) == 1
    alert = json.loads(dst.read_text().strip())
    assert alert["classification"] == "review"
    print("PASS: 1 review candidate in an atomic report")
```

**Expected terminal result:** `PASS: 1 review candidate in an atomic report`.

## Explain the code, not merely the output

1. Generate stable synthetic evidence and keep input separate from output.
2. Use strict bounded parsing and event-time processing; duplicate source-qualified IDs are tracked.
3. The report only commits after complete processing; it is an analyst triage aid.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Append `not-json` and prove the previous report is left intact.
2. Add a duplicate ID and see that it does not increment failures.
3. Add an earlier timestamp after a later one: detect ordering error.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

End-to-end correctness includes parsing failure semantics, report atomicity, rule assumptions, and a testable quality metric—not simply finding an alert.

**Threat model / safety consideration:** A triage candidate does not prove an account compromise; no autonomous containment.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_18.py`, a tests file, and `report_18.md` with exact commands, outcomes and limitations.
