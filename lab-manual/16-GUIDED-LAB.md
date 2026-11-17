# Lab 16 — Mock cloud inventory and incomplete-page reporting

[Read Chapter 16](../course/16-CLOUD-CONTAINERS-DEVSECOPS.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A compliance inventory receives four of five expected pages. A tool must not call the account compliant without full coverage.

**Measurable goal:** Audit toy storage policy and explicitly flag incomplete inventory.

**Input contract:** Two synthetic storage assets and pagination 4/5. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_16.py` and copy the next complete snippet into it. Run it with `python lab_16.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Storage:
    name: str
    encrypted: bool
    public_block: bool

def evaluate(item):
    reasons = []
    if not item.encrypted:
        reasons.append("ENCRYPTION")
    if not item.public_block:
        reasons.append("PUBLIC_ACCESS")
    return reasons

assets = [Storage("lab-a",True,True), Storage("lab-b",False,True)]
finding = {item.name:evaluate(item) for item in assets}
assert finding == {"lab-a":[],"lab-b":["ENCRYPTION"]}
pages_expected, pages_received = 5, 4
status = "INCOMPLETE" if pages_received != pages_expected else "COMPLETE"
assert status == "INCOMPLETE"
print("PASS: finding and explicit incomplete inventory")
```

**Expected result:** `PASS: finding and explicit incomplete inventory`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. The evaluator is pure and can be unit-tested without cloud credentials.
2. Provider booleans are simplifications of effective access/encryption state.
3. Partial pagination must not be converted into a clean or complete result.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Set a second asset to public_block=False and verify two independent policy findings.
2. Simulate missing fields; reject instead of assigning compliant defaults.
3. Describe minimal IAM permissions needed for read-only metadata, not object contents.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

Separate policy evaluation from authorized SDK adapters and any change/remediation executor. Real cloud semantics depend on account, region, inheritance and effective policies.

**Security analysis:** CI secrets, container host mounts and overly broad cloud permissions can make even a 'read-only' tool dangerous.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
