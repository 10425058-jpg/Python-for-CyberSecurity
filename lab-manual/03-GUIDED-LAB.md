# Lab 03 — Data structures, queue boundaries, and burst correlation

**Paired lesson:** [Chapter 03](../course/03-COLLECTIONS-COMPLEXITY-STREAMS.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** An offline detector flags three failures for a single actor within 60 seconds without loading an entire log.

**By the end:** Implement an event-time rolling window with inclusive boundaries and bounded actor cardinality.

**Input or assumptions:** (0,alex), (30,alex), (60,alex), (61,alex)

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_03.py` **in a temporary working directory** and run `python lab_03.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
from collections import deque

def crossing_times(records, threshold=3, span=60, max_actors=100):
    if threshold < 1 or span < 1 or max_actors < 1:
        raise ValueError("bounds")
    windows = {}
    active = set()
    previous = -1
    for timestamp, actor in records:
        if type(timestamp) is not int or timestamp < previous:
            raise ValueError("out-of-order time")
        previous = timestamp
        if actor not in windows:
            if len(windows) >= max_actors:
                raise ValueError("actor cap")
            windows[actor] = deque()
        q = windows[actor]
        while q and timestamp - q[0] > span:
            q.popleft()
        if len(q) < threshold:
            active.discard(actor)
        q.append(timestamp)
        if len(q) >= threshold and actor not in active:
            active.add(actor)
            yield actor, timestamp

assert list(crossing_times([(0,"alex"),(30,"alex"),(60,"alex"),(61,"alex")])) == [("alex",60)]
print("PASS: single crossing at inclusive 60-second limit")
```

**Expected terminal signal:** `PASS: single crossing at inclusive 60-second limit`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. Deque append and popleft each occur at most once per timestamp.
2. An event at t=60 keeps t=0 when the boundary is inclusive.
3. State latching suppresses repeated alerts until the active count falls below threshold.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Submit t=40 followed by t=20: reject out-of-order input.
2. Set max_actors=1 and send a new actor: reject.
3. Identify why per-actor queues still need an upper bound during high-rate attacks.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

Use timestamp - oldest > span for inclusive windows. Key complexity is O(N) processing, but memory can still grow without per-actor queue caps and actor expiration.

### Security review

An adversary can exhaust a detector with many distinct synthetic names unless cardinality and queue memory are bounded.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
