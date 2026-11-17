# Lab 02 — Control-flow contracts and visible parser failures

**Paired lesson:** [Chapter 02](../course/02-CONTROL-FLOW-FUNCTIONS-ERRORS.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A small SOC script receives untrusted synthetic action records and counts failures by actor. One corrupt line must produce a detectable failure.

**By the end:** Build a batch classifier whose malformed input never becomes an apparent clean result.

**Input or assumptions:** [{"actor":"alex","action":"login_failure"},{"actor":"alex","action":"login_success"}]

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_02.py` **in a temporary working directory** and run `python lab_02.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
from collections import Counter

def summarize(rows):
    if type(rows) is not list or len(rows) > 1000:
        raise ValueError("rows must be a bounded list")
    counts = Counter()
    for line_no, row in enumerate(rows, 1):
        if type(row) is not dict or set(row) != {"actor","action"}:
            raise ValueError(f"row {line_no}: schema")
        if type(row["actor"]) is not str or not 1 <= len(row["actor"]) <= 64:
            raise ValueError(f"row {line_no}: actor")
        if row["action"] not in {"login_failure","login_success"}:
            raise ValueError(f"row {line_no}: action")
        if row["action"] == "login_failure":
            counts[row["actor"]] += 1
    return dict(counts)

assert summarize([{"actor":"alex","action":"login_failure"}]) == {"alex":1}
try:
    summarize([{"actor":"alex","action":"login_failure"}, {"actor":"alex"}])
except ValueError as exc:
    assert "row 2" in str(exc)
    print("PASS: incomplete input is not called clean")
```

**Expected terminal signal:** `PASS: incomplete input is not called clean`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. Validate schema and field types before branching.
2. Raise with the row number and distinguish invalid input from a valid zero-count result.
3. A function can be pure and leave exit-code mapping to the CLI adapter.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Pass a dict instead of a list: reject.
2. Pass unknown action 'restart': reject, not silently skip.
3. Change the exception handler to return {}; explain why that creates a false all-clear.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

The empty dictionary means a complete valid input with no failures; an invalid row is an exception, not a successful empty result. Report completeness separately in a real pipeline.

### Security review

Silent exception suppression can cause serious false-negative security reporting.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
