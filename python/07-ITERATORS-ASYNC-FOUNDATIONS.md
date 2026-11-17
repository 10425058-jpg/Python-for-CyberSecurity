# 07 — Iterators, generators, context managers and decorators
> **Expanded textbook (Beginner → Advanced):** This chapter now includes a first-principles lesson, a runnable local program, a reasoning trace, failure cases and graduated exercises. For additional specialized lessons, see: [collections complexity streams](../course/03-COLLECTIONS-COMPLEXITY-STREAMS.md) · [concurrency async os automation](../course/08-CONCURRENCY-ASYNC-OS-AUTOMATION.md).



## Extended textbook 07 — Lazy execution, resources and the iteration protocols

### 7.1 An iterable is not the same as an iterator

An **iterable** supplies an iterator through `iter(obj)`. An **iterator** returns successive values through `next(it)` until it raises `StopIteration`. A list is iterable; a generator object is both iterable and its own iterator. A generator function containing `yield` *suspends* execution and preserves local state between requests for the next value.

This matters for security data: a 10 GB log cannot fit into one Python list on many machines, but a properly bounded streaming reader can process it incrementally. However, if you store every unique actor in a dictionary, overall memory may still grow with the number of distinct keys.

### 7.2 Lazy evaluation is a tradeoff, not automatic safety

Compare `[f(x) for x in data]` with `(f(x) for x in data)`. The first creates a list immediately; the second creates an iterator-like generator expression. Neither guarantees that `f` is pure, that the input is small, or that a partially consumed resource is closed.

A generator that holds an open file may keep it open while suspended. If the consumer stops early, rely on a documented explicit `close()` lifecycle or a context manager instead of assuming prompt garbage collection. A `finally` block is the right place for local resource cleanup.

### 7.3 Implement a generator, an explicit close, and a wrapper

```python
# TEXTBOOK_RUNNABLE
from contextlib import closing, contextmanager
from functools import wraps

cleanup = []

def only_valid_counts(values):
    try:
        for value in values:
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError("bad count")
            yield value
    finally:
        cleanup.append("closed")

def measured_calls(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        # Real timing/metric sinks would be separate and sanitized.
        return function(*args, **kwargs)
    return wrapped

@measured_calls
def total(values):
    return sum(values)

with closing(only_valid_counts([1, 2, 3])) as stream:
    assert next(stream) == 1
assert cleanup == ["closed"]
assert total([1, 2, 3]) == 6
assert total.__name__ == "total"

@contextmanager
def mark_scope():
    cleanup.append("enter")
    try:
        yield "owned-resource"
    finally:
        cleanup.append("exit")

with mark_scope() as label:
    assert label == "owned-resource"
assert cleanup[-2:] == ["enter", "exit"]
print("LAB 07 PASS")
```

**Trace:** Calling `only_valid_counts(...)` creates a generator but does not execute its body. `next(stream)` begins execution and yields one count. Leaving `with closing(...)` calls `close()` on the generator, which triggers its `finally` cleanup even though the loop did not finish. `@wraps` preserves basic function metadata of a decorated function. `@contextmanager` provides a structured entry/exit protocol that also runs cleanup after an exception.

**Important limitation:** a generator that has never started may not have entered its `try` block; cleanup expectations must match actual resource acquisition. Test early return, break, cancellation and exception cases rather than assuming `finally` covers code that never ran.

### 7.4 Context managers and the `with` protocol

`with resource as handle` calls context-manager entry and exit methods around a block. For files, `with open(...) as f` helps close the handle. For database connections, semantics differ: a SQLite connection context manager controls transactions but **does not automatically close** the connection. Always learn the contract of the specific resource type.

### 7.5 Async foundations: what `await` really means

`async def` defines a coroutine function; calling it returns a coroutine object. `await` suspends that coroutine until an awaitable completes, allowing an event loop to run other work. This is cooperative scheduling, not a promise of parallel CPU execution. `async for` and `async with` provide asynchronous iteration and resource management; they require cleanup/cancellation decisions of their own.

A generator yields *data to a synchronous consumer*; an asynchronous generator yields values to an `async for` consumer that can wait on nonblocking I/O between items. Do not start network work in an async example unless its destination and authorization are fixed to your local lab.

### 7.6 Exercises and mastery checks

**Beginner:** Predict the output from calling a generator function, then calling `next` twice, then exhausting it. **Intermediate:** Count 100,000 synthetic event values without converting the generator to a list. Record peak memory and explain why a growing Counter is still O(unique values). **Advanced:** Build an async generator producing synthetic events, consume it with `async for`, then cancel the consumer and verify cleanup without swallowing cancellation.

**Checkpoint:** explain lazy versus eager, iterator exhaustion, `yield` state suspension, `with` and `finally` cleanup, decorators and `functools.wraps`, and why `asyncio` is neither a security boundary nor a substitute for resource caps.

## Iteration protocol
An iterable returns an iterator via `iter()`; an iterator provides successive values via `next()` and raises `StopIteration` at exhaustion. Generator functions use `yield`, suspending between items rather than allocating a complete collection.

```python
from collections.abc import Iterator
from pathlib import Path

def nonblank_lines(path: Path) -> Iterator[str]:
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            value = line.strip()
            if value:
                yield value
```
A generator keeps the file open while iterating and closes it when execution finishes or is finalized; consume promptly or use an explicit resource boundary when ownership matters.

## Context managers
`with` invokes enter/exit protocols; it is crucial for closing sockets, files, locks and temporary artifacts even on exceptions.

```python
from contextlib import contextmanager
from time import monotonic

@contextmanager
def stopwatch():
    start = monotonic()
    try:
        yield
    finally:
        print(f"elapsed: {monotonic() - start:.3f}s")
```

## Decorators
A decorator wraps a function or class. Keep signatures, metadata (`functools.wraps`), exceptions and authorization decisions intact. Do not rely on a decorator as the **only** access-control layer unless its coverage is tested.

## Async iteration
`async for` processes asynchronous iterables; `async with` manages asynchronous resources. They are useful for long-lived network streams but need clear shutdown/cancellation paths.

## Exercises
1. Stream the first 100 malformed lines out of a massive JSONL file.
2. Create a context manager that records duration even if its body fails.
3. Explain lazy vs eager evaluation with memory measurements.
4. Verify an early-terminated generator closes its resources under explicit cleanup.
