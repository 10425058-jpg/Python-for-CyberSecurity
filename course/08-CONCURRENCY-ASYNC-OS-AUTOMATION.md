# Deep Dive 08 — Concurrency, asyncio, operating systems and safe automation

**Level:** intermediate → advanced · **Estimated study:** 9–13 hours.

## Scenario
You must perform approved health checks against a list of services on **your own lab machine**, but you need to avoid overwhelming it. You also want to inventory files and run fixed subprocess commands. This requires knowledge of CPU vs I/O work, cancellation, timeouts, privileges and race conditions.

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
