# Lab 10 — Object authorization and cross-tenant denial

[Read Chapter 10](../course/10-WEB-API-AUTHORIZATION-SECURITY.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A security dashboard has personal and organization reports. The API must not expose another tenant's report merely because a caller knows its ID.

**Measurable goal:** Demonstrate authorization per object and define tests for GET and DELETE requests.

**Input contract:** Principal and Report objects from examples.chapter_cases. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_10.py` and copy the next complete snippet into it. Run it with `python lab_10.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from examples.chapter_cases import Principal, Report, can_read

alex = Principal("alex", "dept-A", frozenset({"report:read-own"}))
sam = Principal("sam", "dept-A", frozenset({"report:read-org"}))
cross = Principal("lee", "dept-B", frozenset({"report:read-org"}))
personal = Report("r1", "dept-A", "alex", "personal")
org = Report("r2", "dept-A", "alex", "organization")

assert can_read(alex, personal)
assert not can_read(sam, personal)
assert can_read(sam, org)
assert not can_read(cross, org)
print("PASS: object-level policy")
```

**Expected result:** `PASS: object-level policy`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. Authenticate on the server; no user-supplied subject or tenant claim is authoritative.
2. Lookup the specific object, then enforce its tenant, classification and permission.
3. A successful policy check is not an HTML escaping, SQL injection or CSRF defense.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Change classification from organization to personal: auditor denied.
2. Give same-tenant owner no read-own permission: denied.
3. Sketch tests ensuring a read-org permission does not authorize DELETE.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

The tenant comparison is the first gate; an owner still needs read-own permission. A production adapter needs authenticated identities, policy versioning and protected audit logs.

**Security analysis:** Broken object-level authorization is a distinct failure even if SQL is parameterized and TLS is correctly configured.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
