# Lab 22 — Strict regex, semantics and ReDoS awareness

**Companion:** [Deep Dive Chapter 22](../course/22-REGEX-UNTRUSTED-TEXT.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

An ingestion parser must not accept an unknown suffix after a legitimate-looking login_failure line.

**Learning goal:** Parse an invented authentication line with whole-string matching and a separate semantic timestamp check.

**Input assumptions:** time=... user=... action=login_failure. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_22.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
from examples.chapter_cases import parse_toy_log

line = "time=2026-01-01T17:00:00+07:00 user=alex action=login_failure"
parsed = parse_toy_log(line)
assert parsed["time_utc"] == "2026-01-01T10:00:00+00:00"
for bad in (line + " suffix", line.replace("user=alex","user="),
            "time=2026-01-01T10:00:00 user=alex action=login_failure"):
    try:
        parse_toy_log(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid log line accepted")
print("PASS: exact grammar and UTC semantics")
```

**Expected terminal result:** `PASS: exact grammar and UTC semantics`.

## Explain the code, not merely the output

1. Input length caps prevent unlimited input being presented to the regex.
2. fullmatch rejects an extra suffix, unlike a permissive substring search.
3. datetime validates actual timestamp meaning and the requirement for a timezone.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Add extra whitespace at the beginning: reject.
2. Use accented usernames and evaluate whether the ASCII-only toy policy is appropriate.
3. Write a threat model explaining catastrophic regex backtracking and a safer parser.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

A regex grammar validates lexical shape; semantic validators check dates/IPs/authorization separately. Correct logging must preserve raw values for evidence.

**Threat model / safety consideration:** A user-controlled regex or unbounded log field can become a CPU exhaustion vector.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_22.py`, a tests file, and `report_22.md` with exact commands, outcomes and limitations.
