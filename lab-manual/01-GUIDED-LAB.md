# Lab 01 — Python identity, immutable event models, and strict JSON types

**Paired lesson:** [Chapter 01](../course/01-PYTHON-RUNTIME-AND-TYPES.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A policy API accepts an enabled flag, a user and the maximum authentication failures allowed. Invalid JSON types must not cause a permissive default.

**By the end:** Prove which objects share memory and reject boolean-as-integer confusion at a JSON trust boundary.

**Input or assumptions:** {"enabled":true,"max_attempts":3,"user":"alex"}

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_01.py` **in a temporary working directory** and run `python lab_01.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Policy:
    enabled: bool
    max_attempts: int
    user: str

def parse_policy(raw: bytes) -> Policy:
    if type(raw) is not bytes or len(raw) > 1024:
        raise ValueError("body type/size")
    value = json.loads(raw.decode("utf-8", "strict"))
    if type(value) is not dict or set(value) != {"enabled","max_attempts","user"}:
        raise ValueError("schema")
    if type(value["enabled"]) is not bool:
        raise ValueError("enabled")
    if type(value["max_attempts"]) is not int or not 1 <= value["max_attempts"] <= 10:
        raise ValueError("attempts")
    if type(value["user"]) is not str or not 1 <= len(value["user"]) <= 64:
        raise ValueError("user")
    return Policy(**value)

assert parse_policy(b'{"enabled":true,"max_attempts":3,"user":"alex"}').max_attempts == 3
try:
    parse_policy(b'{"enabled":true,"max_attempts":true,"user":"alex"}')
except ValueError:
    print("PASS: bool rejected as attempt count")
else:
    raise AssertionError("accepted bool")
```

**Expected terminal signal:** `PASS: bool rejected as attempt count`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. The input is bytes, not a Python dict; cap its size before decoding.
2. JSON true becomes Python True, which is also an instance of int; exact type guards avoid coercion.
3. Construct the frozen domain object only after validated fields. A frozen class alone cannot enforce types.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Replace attempts with 0 and 11: expect ValueError.
2. Replace enabled with 1 and user with null: each must fail.
3. Use a shared nested list inside a frozen dataclass; document that frozen does not deeply freeze.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

The decisive guard is type(value['max_attempts']) is int, not isinstance(..., int). Empty and missing values must fail explicitly; a fallback default would hide malformed policy.

### Security review

Missing or malformed policy must not silently become permission to authenticate indefinitely.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
