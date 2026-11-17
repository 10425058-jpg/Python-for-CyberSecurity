# Deep Dive 08 — Concurrency, asyncio, operating systems and safe automation

> **Hands-on:** [Chapter 08 Guided Lab](../lab-manual/08-GUIDED-LAB.md) · [100 numbered worked answers](../solutions/by-exercise/README.md). Complete the lab's negative tests before moving on.

**Level:** intermediate → advanced · **Estimated study:** 9–13 hours.

## Scenario
You must perform approved health checks against a list of services on **your own lab machine**, but you need to avoid overwhelming it. You also want to inventory files and run fixed subprocess commands. This requires knowledge of CPU vs I/O work, cancellation, timeouts, privileges and race conditions.

## Masterclass — bounded concurrency and correct failure propagation

**Deep idea:** rate-limiting *active* workers is not enough if you create 100,000 pending tasks in memory. Backpressure means the producer must stop enqueueing when a bounded queue is full. Moreover, when a worker fails, the system must cancel its siblings and producer rather than hang forever waiting on `queue.join()`.

In Python 3.11+, `asyncio.TaskGroup` creates a structured lifetime for related tasks. If a worker raises a non-cancellation exception, the task group cancels the others and reports an `ExceptionGroup`. This is a better base for a fail-fast pipeline than manually gathering tasks and swallowing exceptions.

**Runnable offline example (no sockets, only synthetic integers):**

```python
# MASTERCLASS_RUNNABLE
import asyncio

async def transform(value: int) -> int:
    await asyncio.sleep(0)  # yield control; no network call
    if type(value) is not int or value < 0:
        raise ValueError("invalid synthetic task")
    return value * value

async def process(items: list[int], workers: int = 3) -> list[int]:
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("invalid workers")
    queue = asyncio.Queue(maxsize=4)
    results: list[int | None] = [None] * len(items)

    async def producer():
        for index, value in enumerate(items):
            await queue.put((index, value))
        for _ in range(workers):
            await queue.put(None)

    async def consumer():
        while True:
            work = await queue.get()
            try:
                if work is None:
                    return
                index, value = work
                results[index] = await transform(value)
            finally:
                queue.task_done()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer())
        for _ in range(workers):
            tg.create_task(consumer())
    return [v for v in results if v is not None]

assert asyncio.run(process([1, 2, 3, 4])) == [1, 4, 9, 16]
failed = False
try:
    asyncio.run(process([1, -1, 2]))
except* ValueError as errors:
    failed = True
    assert any("invalid synthetic task" in str(e) for e in errors.exceptions)
assert failed
```

**Trace the two paths.** For valid input, the producer fills at most four queued entries, three workers transform items, and one sentinel per worker ends consumption. Results preserve input order using the index, irrespective of scheduling. For an invalid item, `transform` raises; `TaskGroup` propagates the error and cancels other tasks. There is no `queue.join()` call that could wait indefinitely after the consumer died.

**What this does *not* bound:** the input list and result list are still O(N) memory. A truly streaming collector must limit the entire pipeline—including output retention, task count, open sockets and retries—and use a designed cancellation/flush policy. A bounded queue is only one resource control.

**Your challenge:** change the producer to receive an async generator with 100,000 records, then write results to a staged local file without retaining all records. Describe what happens if disk writes fail after processing an alert. How will you signal incomplete output and ensure cleanup? Do not hide `CancelledError` or substitute `except Exception: pass`.


## 1. Concurrency versus parallelism

- **Concurrency:** multiple tasks can make progress over a period of time by interleaving work.
- **Parallelism:** tasks execute at the same instant on distinct processors.
- **Threads:** share memory; useful for blocking I/O; lock shared mutable state.
- **Processes:** separate address spaces; good for CPU-heavy workloads when overhead is justified.
- **Asyncio:** cooperative I/O; a task runs until it awaits or yields control.

The CPython GIL's behavior depends on interpreter build/version. Do not claim Python threads can never run Python code in parallel in all builds, or that adding threads always improves CPU throughput.

## 2. Safe local asyncio example

```python
import asyncio

async def check_loopback(port: int, timeout: float = 1.0) -> bool:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid port")
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", port),
            timeout=timeout,
        )
    except (OSError, TimeoutError):
        return False
    try:
        return True
    finally:
        writer.close()
        await writer.wait_closed()

async def check_many(ports: list[int], max_parallel: int = 3):
    semaphore = asyncio.Semaphore(max_parallel)
    async def worker(port):
        async with semaphore:
            return (port, await check_loopback(port))
    return await asyncio.gather(*(worker(port) for port in ports))

# asyncio.run(check_many([8000, 8080, 8443]))
```

The fixed target `127.0.0.1` ensures no remote host scanning. **Do not** turn this into a public-network scanner without a written authorized scope and operational safeguards.

### Why a semaphore matters
Calling `asyncio.gather` on 100,000 unbounded connections can exhaust sockets and memory or disrupt a service. A semaphore limits active work. The example still creates one coroutine per input port; a truly large workload also needs a bounded producer/worker queue.

### Timeouts and cancellation
`wait_for` bounds the connection attempt, but response-reading, cleanup, DNS resolution and an overall job deadline may need separate policies. Cancelled tasks should release resources using `finally`. Some I/O operations are not interruptible in the way you expect; measure and test real runtime behavior.

## 3. Retry is not free

Retries may amplify outages. For a permitted API:
- Retry only transient errors and only when operation semantics allow.
- Set an attempt limit and total deadline.
- Use exponential backoff with jitter for fleets.
- Honor server-provided rate limits and `Retry-After`.
- Log retries without secrets; record final failure.
- Avoid automatic retry of irreversible high-impact operations without idempotency protection.

A timeout does not necessarily mean the remote server failed to execute a write. If you retry blindly, you may perform the action twice.

## 4. Race conditions and shared state

`counter += 1` is not a universal atomic cross-thread operation. Use a lock, queue or single-writer design when shared state must be consistent. For event pipelines, immutable messages and a single-writer SQLite transaction simplify reasoning.

Race conditions also exist in filesystem code:
1. Validate that a path is inside an allowed directory.
2. An attacker changes a symlink target.
3. The program opens a different file.

For high-assurance security tooling, rely on file descriptors and OS-specific directory-relative APIs, not only string path comparisons.

## 5. Subprocess security

`subprocess.run` with an argument list is generally safer than shell string interpolation, but it is not magic: launching a malicious executable, passing dangerous arguments, or inheriting privileged environment variables can still cause harm.

```python
import subprocess, sys

result = subprocess.run(
    [sys.executable, "--version"],
    check=True, capture_output=True, text=True, timeout=5,
)
print(result.stdout or result.stderr)
```

Compare:
```python
# DON'T:
# subprocess.run("some-tool " + user_input, shell=True)
# DO:
# validate the requested operation and parameters,
# choose a trusted executable, pass an argument list,
# set a timeout, minimal environment and least privileges.
```

A common misconception is that `shell=False` alone makes all commands safe. A command may interpret its arguments as options or filenames with powerful effects. Always understand the target program.

## 6. OS security foundations

### Linux
Processes, signals, file modes/ACLs, ownership, sudo/polkit, systemd, journald, namespaces, cgroups, SELinux/AppArmor, auditd and SSH. A tool running as root can change the machine even with one coding mistake. Default to read-only unprivileged commands.

### Windows
Windows tokens, UAC, NTFS ACLs, service accounts, registry, processes, PowerShell logging, event channels/providers and Defender. Local admin rights are not always equivalent to a service token or domain permissions. Event IDs must be interpreted together with provider/channel/version.

### File timestamps
`mtime` is file content modification time; `ctime` has differing semantics across OSs (metadata change on Unix, creation historically on Windows); birth time availability varies. For a forensic timeline, store each source's own timestamp semantics.

## 7. Read-only filesystem inventory

```python
from pathlib import Path
from hashlib import sha256

def digest_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = sha256()
    with path.open("rb") as source:
        while data := source.read(chunk):
            h.update(data)
    return h.hexdigest()

def list_owned_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_symlink() and path.is_file():
            yield path.relative_to(root).as_posix(), digest_file(path)
```

**Limitations:** directory traversal can race with symlink/path changes; files can mutate while hashing; errors can happen halfway; metadata is not chain of custody; traversing device or network-mounted filesystems may have side effects. For evidence-grade acquisition, use specialized procedures and tools.

## 8. Performance and workload design

Before parallelizing, measure:
- Events/sec and tail latency.
- Peak memory, CPU and open file descriptors.
- Number of in-flight requests.
- Error and timeout rates.
- Retry and cancellation behavior.
- Workload fairness and per-source quotas.

Optimization steps: stream files; avoid repeated parsing; add indexes; bound queues; profile; only then introduce threads/processes/async where justified.

## 9. Exercises with expected results
**A:** Open a local `python -m http.server 8765 --bind 127.0.0.1` and run a three-port loopback checker. Expected: 8765 reachable, unused ports usually unreachable; not a vulnerability finding.

**B:** Create 100 simulated tasks that each do `await asyncio.sleep(0.01)`. Compare sequential vs semaphore-bounded concurrency; report times and explain overhead.

**C:** Implement a total deadline around a multi-step local I/O workflow and demonstrate cancellation cleanup. Expect no lingering sockets/files.

**D:** Identify three privilege risks in a tool using `sudo` and design a least-privilege read-only replacement.

**E:** Explain why filesystem checks before opening cannot guarantee safety against concurrent symlink changes.

**References:** [asyncio](https://docs.python.org/3/library/asyncio.html), [subprocess](https://docs.python.org/3/library/subprocess.html), [concurrent futures](https://docs.python.org/3/library/concurrent.futures.html).


## 10. Detailed concurrency scenario: high traffic does not justify unbounded workers

A security script that checks 10,000 authorized endpoints might be tempted to start 10,000 tasks simultaneously. That can exhaust file descriptors and saturate the network. On a machine with only hundreds of available sockets, **concurrency can become a denial-of-service risk against your own monitoring infrastructure**.

### A bounded worker queue with no external network access

To isolate concurrency mechanics, simulate service checks with `asyncio.sleep` rather than contacting a real host:

```python
import asyncio

async def simulated_check(item: int) -> tuple[int, str]:
    await asyncio.sleep(0.005)
    return (item, "ok")

async def bounded_pipeline(inputs: list[int], workers: int = 4):
    if type(workers) is not int or not 1 <= workers <= 16:
        raise ValueError("workers must be between 1 and 16")
    q = asyncio.Queue(maxsize=8)
    results = []

    async def producer():
        for item in inputs:
            await q.put(item)
        for _ in range(workers):
            await q.put(None)  # explicit sentinel

    async def worker():
        while True:
            item = await q.get()
            try:
                if item is None:
                    return
                results.append(await simulated_check(item))
            finally:
                q.task_done()

    tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    prod = asyncio.create_task(producer())
    try:
        await prod
        await q.join()
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    return results

assert len(asyncio.run(bounded_pipeline(list(range(25))))) == 25
```

**Walkthrough:** the producer blocks when eight items occupy the queue (backpressure); four workers make progress concurrently; each processed item calls `task_done()`; sentinels let workers exit; cancellation in `finally` prevents abandoned tasks under normal error handling. A production pipeline must additionally propagate worker failures immediately and cancel the producer to avoid a deadlock if workers exit before the queue drains; this particular example assumes `simulated_check` does not fail.

### Race conditions: the same ID used twice

Two workers might both check "event not in database" before either inserts it, then both write. In-memory sets and the GIL are not a valid cross-process transaction guarantee. A SQLite `PRIMARY KEY` or unique constraint and a documented conflict policy is stronger, with transactions surrounding a batch.

### Security checklist for an asynchronous client
- Limit **outstanding tasks** as well as active connections.
- Set per-step and overall deadlines.
- Respect rate limits from target services.
- Avoid infinite retries; distinguish transient versus permanent failures.
- Close streams/sessions when cancelled.
- Bound response body size before decoding.
- Do not log bearer tokens in exception messages.
- Handle `asyncio.CancelledError` correctly so shutdown is not hidden.

## 11. OS permissions and command execution: concrete design review

Suppose a privileged agent accepts a string naming a directory and starts a shell command built from it. This crosses two dangerous boundaries: user-controlled path → command arguments, and unprivileged request → privileged process.

Instead:
1. Require a read-only, allowlisted operation.
2. Use `pathlib` or stable APIs for file handling.
3. If an external executable is necessary, use an explicitly trusted binary and argument array.
4. Provide no shell interpolation, minimal environment, exact parameter validation, timeout, and restricted identity.
5. Log only sanitized identifiers and action outcomes.
6. Test paths with spaces, Unicode, dashes, symlinks and bad permissions.

**Even `shell=False` does not make an arbitrary executable safe**. Commands can interpret leading-dash filenames as options, or read privileged paths if given sufficient access.

## 12. Exercises and answer logic

1. **Backpressure:** set `maxsize=1` and compare completion time with `maxsize=100`. How do results and memory differ? Depends on workload; bounded queue caps in-flight waiting items.
2. **Worker failure:** make `simulated_check` raise on item 10. Observe the hang/cleanup risk; redesign with a task group or explicit failure propagation, and test it.
3. **Timeout:** wrap the *whole* local pipeline in a single deadline and verify resources close if cancelled.
4. **Idempotency:** specify how an event ID should be handled if received twice after retry; explain why a simple `if id not in seen` is insufficient across processes.
5. **Privilege audit:** identify every permission an inventory script needs. Read-only file metadata access should not imply admin-level remediation rights.

**Further reading:** [asyncio queues](https://docs.python.org/3/library/asyncio-queue.html), [task cancellation](https://docs.python.org/3/library/asyncio-task.html), [subprocess](https://docs.python.org/3/library/subprocess.html).
