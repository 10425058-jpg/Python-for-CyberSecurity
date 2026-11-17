# Lab 06 — Dependency injection and authorization test doubles

**Paired lesson:** [Chapter 06](../course/06-TYPING-OOP-ARCHITECTURE.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A security report is readable only by its owner with permission, or a tenant auditor for organization-level records.

**By the end:** Separate the authorization decision from I/O so it can be tested without database or network.

**Input or assumptions:** Two toy tenants, reports and permissions

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_06.py` **in a temporary working directory** and run `python lab_06.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
from examples.chapter_cases import Principal, Report, can_read

owner = Principal("alex", "A", frozenset({"report:read-own"}))
auditor = Principal("sam", "A", frozenset({"report:read-org"}))
outsider = Principal("lee", "B", frozenset({"report:read-org"}))
personal = Report("r-1", "A", "alex", "personal")
org = Report("r-2", "A", "alex", "organization")
assert can_read(owner, personal)
assert not can_read(auditor, personal)
assert can_read(auditor, org)
assert not can_read(outsider, org)
print("PASS: cross-tenant access denied")
```

**Expected terminal signal:** `PASS: cross-tenant access denied`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. Principal must come from verified server identity, not user input.
2. Report metadata must come from authoritative storage.
3. A pure function is deterministic and allows negative tests for cross-tenant access.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Remove the tenant comparison in a local copy; show the regression test catches it.
2. Give owner no read permission; owner status alone must not grant access.
3. Create a fake storage adapter and verify that no network calls occur in the policy function.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

Tenant matching must be checked before owner and auditor rules. Authentication, object lookup and report serialization remain separate required layers.

### Security review

A valid login or parameterized SQL query does not authorize access to another tenant's object.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
