# Lab 08 — Async queue backpressure and cancellation

**Paired lesson:** [Chapter 08](../course/08-CONCURRENCY-ASYNC-OS-AUTOMATION.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A monitoring job has 100 local tasks; workers must be limited and results collected while failures are visible.

**By the end:** Process synthetic work concurrently without creating unbounded pending tasks.

**Input or assumptions:** 100 synthetic integers; four asynchronous workers

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_08.py` **in a temporary working directory** and run `python lab_08.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
import asyncio

async def evaluate(item):
    await asyncio.sleep(0)
    return item * 2

async def run_bounded(items, parallelism=4):
    if not 1 <= parallelism <= 16:
        raise ValueError("worker cap")
    queue = asyncio.Queue(maxsize=8)
    output = []
    async def worker():
        while True:
            value = await queue.get()
            try:
                if value is None:
                    return
                output.append(await evaluate(value))
            finally:
                queue.task_done()
    workers = [asyncio.create_task(worker()) for _ in range(parallelism)]
    try:
        for item in items:
            await queue.put(item)
        for _ in workers:
            await queue.put(None)
        await queue.join()
        await asyncio.gather(*workers)
    finally:
        for task in workers:
            if not task.done():
                task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
    return sorted(output)

assert asyncio.run(run_bounded(range(100))) == [2*i for i in range(100)]
print("PASS: 100 bounded tasks complete")
```

**Expected terminal signal:** `PASS: 100 bounded tasks complete`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. The queue holds at most eight pending items, applying backpressure to the producer.
2. Four workers evaluate tasks and call task_done in finally.
3. Clean shutdown sends one sentinel per worker and cancels unfinished tasks.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Try parallelism=17; expect ValueError.
2. Change evaluate to raise once; demonstrate why this teaching implementation can hang without failure propagation.
3. Design a TaskGroup-based, fail-fast variant and test timeout behavior.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

This demonstration assumes no worker failure. Production implementations must propagate failures and cancel producers/consumers as one supervision unit.

### Security review

Unbounded tasks, sockets and retries can cause denial of service against your own monitoring infrastructure.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
