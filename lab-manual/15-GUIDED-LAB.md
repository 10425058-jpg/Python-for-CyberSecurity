# Lab 15 — Inert file triage, sample entropy and IOC confidence

[Read Chapter 15](../course/15-MALWARE-TRIAGE-THREAT-INTELLIGENCE.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

Two harmless files have different entropy. The student must not infer malware from an unusual statistic.

**Measurable goal:** Calculate toy entropy and validate an IP indicator while explaining source provenance and expiry.

**Input contract:** b'AAAA', b'ABAB' and reserved documentation IPv6. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_15.py` and copy the next complete snippet into it. Run it with `python lab_15.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from collections import Counter
from math import log2
from ipaddress import ip_address

def entropy(raw):
    if not raw:
        return 0.0
    total = len(raw)
    return -sum((n/total)*log2(n/total) for n in Counter(raw).values())

assert entropy(b"AAAA") == 0.0
assert entropy(b"ABAB") == 1.0
assert str(ip_address("2001:0db8::1")) == "2001:db8::1"
print("PASS: measured entropy, normalized IOC")
```

**Expected result:** `PASS: measured entropy, normalized IOC`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. A byte distribution with only one symbol has entropy zero.
2. A balanced two-symbol sample has entropy 1 bit per byte.
3. High entropy may indicate compression or encryption, not necessarily malware.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Calculate entropy for an empty file: define and test result.
2. Use an invalid IP and assert ValueError.
3. Design an indicator record with source, observed time, expiration and confidence; do not auto-block.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

Statistics and reputation matches are triage context. Report sample size, sampling strategy, origin and alternatives before classification.

**Security analysis:** Never run unknown malware in the ordinary lab; keep static inspection offline and avoid uploading private evidence to public services.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
