# Lab 13 — Evidence manifests and time-zone-correct incident timelines

[Read Chapter 13](../course/13-DFIR-EVIDENCE-AND-TIMELINES.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

Two synthetic authentication logs use Z and +07:00 timestamps, and an investigator wants to order three events without overwriting originals.

**Measurable goal:** Produce a correct UTC timeline and record stable integrity digests of input bytes.

**Input contract:** 10:00Z failure, 17:01+07:00 failure, 10:02Z success. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_13.py` and copy the next complete snippet into it. Run it with `python lab_13.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from datetime import datetime, timezone
from hashlib import sha256

evidence = [
    ("a", "2026-01-01T10:00:00Z", "failure"),
    ("b", "2026-01-01T17:01:00+07:00", "failure"),
    ("c", "2026-01-01T10:02:00Z", "success"),
]
def timestamp(raw):
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)

ordered = sorted(evidence, key=lambda e: timestamp(e[1]))
assert [e[0] for e in ordered] == ["a","b","c"]
manifest_digest = sha256(repr(evidence).encode("utf-8")).hexdigest()
assert len(manifest_digest) == 64
print("PASS: correct UTC order")
```

**Expected result:** `PASS: correct UTC order`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. UTC+07:00 at 17:01 represents 10:01 UTC.
2. Hash here covers serialized synthetic data, not a forensic-grade disk acquisition.
3. The original timestamp must remain alongside the derived UTC time and source reference.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Use 10:00 without a timezone: reject as ambiguous.
2. Corrupt original bytes: digest changes.
3. Write a benign alternative hypothesis for failure-failure-success.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

Correct ordering supports a timeline but does not prove intent, account compromise or authoritative source clocks. Record custody and uncertainty.

**Security analysis:** Avoid confusing an integrity hash with source authenticity or a chain-of-custody record.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
