# 11 — Python internals, performance and advanced topics
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [collections complexity streams](../course/03-COLLECTIONS-COMPLEXITY-STREAMS.md) · [concurrency async os automation](../course/08-CONCURRENCY-ASYNC-OS-AUTOMATION.md).



## Extended textbook 11 — Understand Python's machinery, then measure before optimizing

### 11.1 Language semantics vs CPython implementation details

Python specifies the language; CPython is one implementation. A source file is commonly compiled into bytecode instructions executed by a virtual machine. The `dis` module can inspect implementation-specific bytecode, but opcodes may differ across versions and are **not** a public stable API. CPython often manages objects with reference counting plus a cycle collector, but the precise memory strategy is implementation-specific. Code must not rely on immediate destructor timing for safety-critical resource cleanup—use explicit context managers.

### 11.2 Advanced language tools worth understanding

- **Closures:** a nested function can retain access to an enclosing binding. Late binding in loops can make callbacks unexpectedly capture the final loop variable; bind defaults explicitly when suitable.
- **Descriptors and properties:** attributes may execute code on access. Do not treat arbitrary object attributes as inert data when parsing an untrusted plugin.
- **Decorators:** wrap behavior while preserving metadata with `functools.wraps`; ensure exceptions and authorization rules are not accidentally bypassed.
- **Generators and coroutines:** suspend with retained state; they need explicit cleanup and cancellation policy when holding resources.
- **Pattern matching (`match`):** matches structures/patterns; a successful structural pattern is not a complete trust validation.
- **Typing Protocol and generics:** improve correctness and reviewability but do not validate arbitrary JSON or authenticate the caller.
- **Metaclasses:** useful in some frameworks, but usually too complex for a small security tool unless a real requirement justifies them.

### 11.3 Complexity and measurement: where the memory actually goes

`time.perf_counter` measures elapsed wall-clock time. `cProfile` records where Python function execution time occurs. `tracemalloc` tracks many allocations made by Python, but not every native library allocation or total process resident memory (RSS). `sys.getsizeof` reports a shallow object's size, generally excluding referenced nested objects.

A generator avoids a full input list but does not stop the program from storing all unique actor names in a dictionary. For N events and U unique actors, a `Counter` uses approximately O(N) processing and O(U) keys. An input-controlled U can be more dangerous than a very large N with only two repeated values.

### 11.4 Executable performance, caching and cardinality lab

```python
# TEXTBOOK_RUNNABLE
from collections import Counter
from functools import lru_cache
from time import perf_counter
import tracemalloc

def bounded_count(items, *, max_actors: int = 20):
    counts = Counter()
    for actor in items:
        if type(actor) is not str or not 1 <= len(actor) <= 64:
            raise ValueError("invalid actor")
        if actor not in counts and len(counts) >= max_actors:
            raise ValueError("too many distinct actors")
        counts[actor] += 1
    return counts

tracemalloc.start()
start = perf_counter()
counts = bounded_count("alex" if n % 2 else "sam" for n in range(10_000))
elapsed = perf_counter() - start
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
assert counts == {"alex": 5000, "sam": 5000}
assert elapsed >= 0 and peak >= current
try:
    bounded_count((f"user-{i}" for i in range(21)))
except ValueError:
    pass
else:
    raise AssertionError("distinct-actor cap not enforced")

records = {("A", "id1"): "A report", ("B", "id1"): "B report"}
@lru_cache(maxsize=16)
def get_report(tenant: str, report_id: str) -> str:
    return records[(tenant, report_id)]
assert get_report("A", "id1") != get_report("B", "id1")
print("LAB 11 PASS")
```

**Trace:** only two distinct actor keys are retained in the first workload even though 10,000 events are processed. The second workload raises visibly when a twenty-first distinct key is encountered; it does not falsely report a complete scan. The cache keys include tenant as well as report ID, preventing the toy collision where both tenants use `id1`. This **does not** implement authorization: a real cache must respect principal identity, permission changes, tenant scope, expiration and data updates.

### 11.5 Slots, dataclasses and native memory: informed choices

`__slots__` can reduce per-instance memory under certain object layouts, but it restricts dynamic attribute storage and has inheritance nuances; benchmark with your actual workload. A frozen dataclass prevents some accidental mutation but not deep aliasing. `memoryview` can avoid copies when handling slices of byte buffers; its lifetime is tied to the underlying buffer, and it does not validate protocol framing. For heavy numerical tasks, maintained native libraries may be appropriate, but their package provenance and memory safety become part of your threat model.

### 11.6 Long-running defensive tooling

Define **capacity contracts**: maximum open files, bytes per record, distinct actor keys, events per actor, concurrent tasks, retry attempts, wall-clock time and output storage. Add an observable incomplete status whenever a cap prevents full processing. Avoid automatically retrying side-effecting actions without idempotency keys. A background process needs graceful shutdown, a safe restart strategy, privacy-preserving logs and tests for corrupted input in the middle of a batch.

### 11.7 Senior-level exercises

**Beginner:** Explain why two equal tuples can have different object identities and why the exact bytecode of a Python function can change across versions. **Intermediate:** Measure memory for 2 vs 20 distinct actors with a fixed 10,000-event stream; do not compare exact peak bytes from different machines. **Advanced:** Design a bounded streaming parser with a persistent deduplication policy, a transactional report adapter, a cache invalidation strategy and an incident runbook. Write a test showing that hitting a memory cap produces an explicit incomplete result.

**Mastery gate:** you can distinguish language guarantees from CPython behavior, reason about references and GC, interpret profiler outputs, justify a cache key and invalidation policy, and explain how attacker-controlled input shapes both runtime and security risks.

## Language mechanics
Understand scopes (LEGB), closures, descriptors, properties, dunder methods, metaclasses (only when justified), decorators, generators, coroutine state, exception groups, pattern matching, typing protocols, and the import system. Learn how mutable references and garbage collection affect long-running agents.

## Python runtime and memory
Use `sys.getsizeof` only as a shallow indicator. Profile allocations with `tracemalloc`, time with `time.perf_counter` and `cProfile`, and test production-like data volumes. Use streaming parsers, bounded caches, memoryviews and chunked I/O before introducing native extensions. Offload specialized calculations to trustworthy libraries when appropriate.

```python
import tracemalloc
tracemalloc.start()
data = [str(i) for i in range(10_000)]
current, peak = tracemalloc.get_traced_memory()
print({"current_bytes": current, "peak_bytes": peak})
tracemalloc.stop()
```

## Native interfaces and isolation
Learn C extensions, CFFI/ctypes risk, integer bounds across languages, shared libraries, subprocess isolation, FFI calling conventions and serialization boundaries. **Never use ctypes or a native library on untrusted inputs without understanding bounds and memory safety.**

## Robust long-running tools
- Resource caps: memory, CPU, file descriptors, concurrent requests.
- Checkpointing and idempotent replay for telemetry ingestion.
- Structured logging, error budgets, metrics, tracing and health checks.
- Data retention, secure deletion caveats, access control and audit trail design.
- Threat model the tool itself: it may parse malicious packets and adversarial logs.
- Guard plugin loading and supply-chain trust; do not deserialize Python objects from third parties.
- Review cross-platform differences in paths, timestamps, networking and process models.

## Advanced exercises
1. Profile a generator-based log parser vs `readlines()` on a synthetic dataset.
2. Bound memory use in a burst-detection pipeline.
3. Explain why faster code is not always safer and what resource budgets must be tested.
4. Make an import-safe package and verify that importing it does not touch network/filesystem.
