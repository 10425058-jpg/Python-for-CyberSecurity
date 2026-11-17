# Lab 19 — Cross-OS endpoint event normalization

**Companion:** [Deep Dive Chapter 19](../course/19-ENDPOINT-OS-TELEMETRY.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

A lab has one Linux toy-auth export and one Windows toy-auth export; a single normalized event type must not erase original provider context.

**Learning goal:** Normalize two invented endpoint providers while keeping provider-specific meaning and source references.

**Input assumptions:** synthetic provider-specific events with aware timestamps. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_19.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
from datetime import datetime, timezone

rows = [
    {"provider":"lab-linux","host":"vm-a","timestamp":"2026-01-01T10:00:00Z","kind":"fail"},
    {"provider":"lab-windows","host":"vm-b","timestamp":"2026-01-01T17:01:00+07:00","code":1001},
]
def normalize(row):
    provider = row["provider"]
    if provider == "lab-linux" and row.get("kind") == "fail":
        event_type = "authentication_failure"
    elif provider == "lab-windows" and row.get("code") == 1001:
        event_type = "authentication_failure"  # ONLY the invented provider
    else:
        raise ValueError("unsupported provider/event")
    when = datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
    if when.utcoffset() is None:
        raise ValueError("timezone")
    return {"provider":provider,"host":row["host"],"type":event_type,
            "utc":when.astimezone(timezone.utc).isoformat()}

out = [normalize(r) for r in rows]
assert [x["utc"] for x in out] == [
    "2026-01-01T10:00:00+00:00", "2026-01-01T10:01:00+00:00"
]
print("PASS: cross-source UTC normalization")
```

**Expected terminal result:** `PASS: cross-source UTC normalization`.

## Explain the code, not merely the output

1. Provider+event ID supplies meaning; ID by itself is not globally standardized.
2. Normalize timestamps to aware UTC and preserve original source metadata.
3. Separate verified source-specific mapping from the high-level detection layer.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Change provider to unknown: reject.
2. Add an offset-free timestamp: reject.
3. Explain why PID alone cannot identify a process over long periods.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

Normalized types are derived labels; keep provider/channel/event ID and raw reference for a real investigation.

**Threat model / safety consideration:** Endpoint event contents may expose personal data, credentials and sensitive command lines. Use synthetic exports.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_19.py`, a tests file, and `report_19.md` with exact commands, outcomes and limitations.
