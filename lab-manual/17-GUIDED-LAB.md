# Lab 17 — Vulnerability applicability and bounded parser fuzzing

**Companion:** [Deep Dive Chapter 17](../course/17-VULNERABILITIES-FUZZING-RISK.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

A synthetic SBOM has a package version and a toy advisory. The team must review applicability instead of calling every advisory exploitable.

**Learning goal:** Validate toy version identifiers, show a safe parser fuzzing invariant and explain why CVSS alone is not risk.

**Input assumptions:** package=toy-parser, installed=1.10, fixed=1.11; fuzz with local test strings. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_17.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
import random
from string import ascii_letters, digits

def parse_ascii_port(raw):
    if type(raw) is not str or not 1 <= len(raw) <= 5:
        raise ValueError("length/type")
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError("decimal ASCII")
    number = int(raw)
    if not 1 <= number <= 65535:
        raise ValueError("port range")
    return number

rng = random.Random(17)  # reproducible test input, not credential entropy
accepted = 0
for _ in range(1000):
    raw = "".join(rng.choice(ascii_letters + digits) for _ in range(rng.randrange(7)))
    try:
        parsed = parse_ascii_port(raw)
        assert 1 <= parsed <= 65535
        accepted += 1
    except ValueError:
        pass
assert parse_ascii_port("443") == 443
print("PASS: 1000 bounded parser cases; accepted:", accepted)
```

**Expected terminal result:** `PASS: 1000 bounded parser cases; accepted: <nonnegative integer>`.

## Explain the code, not merely the output

1. Limit types and length **before** integer conversion.
2. Generate reproducible inputs; a passing fuzz run samples a finite input space.
3. Compare versions using an appropriate PEP 440 parser, not lexical strings.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Try booleans, Unicode digit strings and 6-digit strings: reject.
2. Write a separate `Version('1.10') > Version('1.2')` check if packaging is installed.
3. Draft a remediation ticket specifying exposure, owner, fix and rollback.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

Fuzzing is an aid to discovering bugs, not proof of safety; a published severity does not establish exploitation in your environment.

**Threat model / safety consideration:** Run fuzzing only against a local pure function with bounded CPU/memory and no external targets.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_17.py`, a tests file, and `report_17.md` with exact commands, outcomes and limitations.
