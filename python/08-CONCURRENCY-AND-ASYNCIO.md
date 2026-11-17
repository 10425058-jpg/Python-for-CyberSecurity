# 08 — Threads, processes, asyncio and resilient I/O
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [concurrency async os automation](../course/08-CONCURRENCY-ASYNC-OS-AUTOMATION.md).



## Extended textbook 08 — Understand scheduling before adding concurrency

### 8.1 Concurrency is not the same as parallelism

**Concurrency** means several tasks make progress during overlapping periods. **Parallelism** means work executes simultaneously on multiple execution units. For example, while one task waits for a file or network response, another can run—even on one CPU core. The right model depends on whether your workload is mostly I/O-bound or CPU-bound.

| Model | Best starting use | State shared? | Critical caveat |
|---|---|---|---|
| simple serial code | small predictable jobs | ordinary locals | baseline for correctness |
| `threading` | blocking I/O libraries | yes, shared process memory | synchronize shared mutable state |
| `ThreadPoolExecutor` | bounded blocking tasks | yes | futures can accumulate unboundedly |
| `multiprocessing` / process pool | CPU-intensive isolated tasks | not directly, separate processes | serialization/startup overhead |
| `asyncio` | many cooperative nonblocking I/O tasks | same event-loop process state | blocking calls freeze the loop |

In regular CPython builds the Global Interpreter Lock affects CPU-bound Python threads. Free-threaded builds and interpreter versions differ; do not treat "GIL" as a permanent universal Python-language guarantee. Profile the workload and avoid relying on incidental atomic behavior for correctness.

### 8.2 A coroutine only runs when scheduled/awaited

`async def fetch(): ...` defines a coroutine function. Calling `fetch()` creates a coroutine object; it does not run it to completion. `await fetch()` executes through the event loop and may suspend. `asyncio.create_task` schedules a coroutine. `asyncio.run` creates and manages an event loop for a top-level async program; it cannot be nested directly inside a running event loop.

**Blocking mistake:** calling `time.sleep(10)` inside an asynchronous task blocks the event-loop thread. Use `await asyncio.sleep(10)` for demonstration delays, and real async I/O interfaces for production I/O.

### 8.3 Bounded producer-consumer architecture

Concurrency limits must cover both **active workers** and **waiting work**. If you create 100,000 tasks and only put a semaphore around their I/O, you may still keep 100,000 task objects in memory. A bounded `asyncio.Queue(maxsize=N)` applies **backpressure**: the producer waits when the queue is full. In Python 3.11+, `TaskGroup` supervises related tasks and propagates worker errors rather than silently dropping them.

```python
# TEXTBOOK_RUNNABLE
import asyncio

async def square(value: int) -> int:
    await asyncio.sleep(0)  # purely synthetic, yields to event loop
    if type(value) is not int or value < 0:
        raise ValueError("invalid task")
    return value * value

async def bounded_work(items: list[int], worker_count: int = 3) -> list[int]:
    if type(worker_count) is not int or not 1 <= worker_count <= 8:
        raise ValueError("worker cap")
    if type(items) is not list or len(items) > 1000:
        raise ValueError("input cap")
    queue = asyncio.Queue(maxsize=4)
    results: list[int | None] = [None] * len(items)

    async def producer():
        for index, value in enumerate(items):
            await queue.put((index, value))
        for _ in range(worker_count):
            await queue.put(None)

    async def consumer():
        while True:
            task = await queue.get()
            try:
                if task is None:
                    return
                index, value = task
                results[index] = await square(value)
            finally:
                queue.task_done()

    async with asyncio.TaskGroup() as group:
        group.create_task(producer())
        for _ in range(worker_count):
            group.create_task(consumer())
    return [value for value in results if value is not None]

assert asyncio.run(bounded_work([1, 2, 3, 4])) == [1, 4, 9, 16]
failed = False
try:
    asyncio.run(bounded_work([1, -1]))
except* ValueError:
    failed = True
assert failed
print("LAB 08 PASS")
```

**Walkthrough:** the queue holds a maximum of four waiting work items. Three consumers process them. A sentinel `None` is sent for each worker to signal completion. The output list preserves input order using indexes, not unpredictable completion order. If a worker raises `ValueError`, `TaskGroup` cancels related work and reports the error via an exception group. This is stronger than `gather(..., return_exceptions=True)` if the caller then ignores returned exception values.

**Limitations:** the example still retains the entire input list and output list; queue capacity alone does not bound total memory for an arbitrary stream. The program is intentionally *not* making network connections. A real service needs deadlines, bounded retries, cancellation-safe resource cleanup and reports that distinguish complete from incomplete processing.

### 8.4 Races, locks and idempotency

Two threads can read the same counter value, compute a new value and overwrite each other's work. A lock serializes a critical section; a queue helps transfer ownership of messages; a database transaction provides a different consistency mechanism. Avoid depending on the current implementation's behavior of a single dictionary operation as if it guaranteed multi-step atomicity.

For event ingestion, **idempotency** means replaying the same source-qualified event ID does not produce a duplicate effect. It requires stable identity, transaction boundaries and careful key retention or expiry. Retrying a non-idempotent operation can accidentally perform it twice.

### 8.5 Timeouts, cancellation and safety policies

A **timeout** is a deadline or maximum wait. A **retry policy** controls when to repeat a failed operation, usually with bounded backoff and jitter. A **circuit breaker** temporarily stops repeated calls to an unhealthy dependency. **Backpressure** prevents work from being accepted faster than it can be processed. These solve distinct failure modes. Cancellation should close streams, release locks, cancel child tasks and produce an incomplete status when necessary.

### 8.6 Exercises

**Beginner:** Time a sequential local delay simulator and a bounded async one; explain why total wall time differs without claiming CPU parallelism. **Intermediate:** Make a worker deliberately raise, then verify siblings are cancelled and no report is falsely declared complete. **Advanced:** Replace the input list and output list with an async iterator and staged file writer; enforce a total event cap, cancellation policy and exactly defined replay semantics.

**Mastery gate:** choose the right concurrency mechanism for a real workload; explain the event loop, queues, tasks, races, GIL/build nuance, deadlines, error propagation and which objects are still stored in memory.

## Choose the right model
- **Threading:** convenient for blocking I/O; shared mutable state requires synchronization.
- **Multiprocessing / ProcessPoolExecutor:** useful for CPU-heavy tasks; inter-process transfer has cost, and worker startup differs across OSs.
- **Asyncio:** cooperative scheduling for many I/O tasks, when using non-blocking APIs.
- **Serial streaming:** often simplest and sufficiently fast for log pipelines.

The CPython GIL and free-threaded builds are version/build dependent; never assume threads automatically speed CPU-bound Python. Measure your workload and interpreter configuration.

```python
import asyncio

async def check_local_service(port: int) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", port), timeout=0.5
        )
    except (OSError, TimeoutError):
        return False
    writer.close()
    await writer.wait_closed()
    return True

async def main():
    for port in (80, 443, 8080):
        print(port, await check_local_service(port))

if __name__ == "__main__":
    asyncio.run(main())
```
This example connects **only** to loopback. For any real network diagnostic, obtain authorization, define specific target bounds, and rate-limit requests.

## Failure and backpressure
Set explicit timeouts; use bounded queues and semaphores, exponential backoff with jitter for allowed APIs, cancellation cleanup, idempotency keys where relevant and graceful shutdown. Concurrency amplifies mistakes (bad retries can cause outages). Never fire unlimited requests or silently swallow task failures.

## Race conditions
Two operations reading/updating shared data can race. Use queues, locks, immutable messages or database transactions. A dictionary operation being individually atomic in one implementation is not a general concurrency contract.

## Exercises
1. Benchmark sequential vs bounded concurrent processing using 100 local delay simulations.
2. Add a semaphore limiting in-flight tasks to three.
3. Simulate cancellation during a local connection attempt and prove cleanup.
4. Explain the difference among timeout, retry, circuit breaker, and backpressure.

References: [asyncio](https://docs.python.org/3/library/asyncio.html), [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html).
