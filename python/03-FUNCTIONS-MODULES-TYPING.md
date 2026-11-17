# 03 — Functions, modules, typing, and API design
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [control flow functions errors](../course/02-CONTROL-FLOW-FUNCTIONS-ERRORS.md) · [typing oop architecture](../course/06-TYPING-OOP-ARCHITECTURE.md).



## Extended textbook 03 — Functions as reliable contracts, modules as boundaries

### 3.1 Function parameters: positional, keyword, defaults, and return values

A function definition specifies a reusable operation. Calling it evaluates arguments, binds them to local parameter names, executes its body and returns either the value supplied with `return` or `None` if it ends without a return. Use positional parameters for natural inputs, keyword-only parameters for options, and explicit defaults for stable behavior.

A signature such as `def decide(count: int, *, threshold: int = 3) -> bool` means `threshold` must be passed by name. The type annotation helps readers and static checkers but Python does not automatically enforce the type at runtime.

**Mutable default trap:** `def save(event, history=[]):` uses one shared list across separate calls. Instead use `history=None` and allocate a new list when no history was supplied. Do not confuse "default argument" with "default security policy": a missing authorization field may need to be rejected, not filled in.

### 3.2 Designing clear failure contracts

Before coding, answer four questions: (1) what input type and range are accepted? (2) what output type and interpretation are promised? (3) which malformed inputs raise an exception? (4) does the function read files, send requests, or mutate state?

Compare `return None` (no finding **after complete valid processing**) with `raise ValueError` (the input is invalid) and `raise OSError` (the environment failed). They must not silently collapse into one "zero results" state.

### 3.3 Dataclasses, protocols and dependency injection in one small app

```python
# TEXTBOOK_RUNNABLE
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Event:
    source: str
    actor: str
    failures: int

class EventSink(Protocol):
    def store(self, event: Event) -> None: ...

class MemorySink:
    def __init__(self) -> None:
        self.events: list[Event] = []
    def store(self, event: Event) -> None:
        self.events.append(event)

def validated_event(source: object, actor: object, failures: object) -> Event:
    if type(source) is not str or not 1 <= len(source) <= 40:
        raise ValueError("invalid source")
    if type(actor) is not str or not 1 <= len(actor) <= 64:
        raise ValueError("invalid actor")
    if type(failures) is not int or not 0 <= failures <= 1000:
        raise ValueError("invalid count")
    return Event(source, actor, failures)

def analyze(event: Event, sink: EventSink, *, threshold: int = 3) -> bool:
    if type(threshold) is not int or not 1 <= threshold <= 1000:
        raise ValueError("invalid threshold")
    sink.store(event)
    return event.failures >= threshold

sink = MemorySink()
event = validated_event("toy-idp", "alex", 3)
assert analyze(event, sink, threshold=3)
assert sink.events == [event]
try:
    validated_event("toy-idp", "alex", True)
except ValueError:
    pass
else:
    raise AssertionError("bool count accepted")
print("LAB 03 PASS")
```

**Why the design works:** `Event` is a compact domain model; `validated_event` enforces the runtime input contract before constructing it. `EventSink` says what any storage adapter must provide; `MemorySink` is a test double, so this example needs no database. `analyze` is a domain decision that receives its dependency as an argument. **Note:** `@dataclass(frozen=True)` does not validate types and cannot guarantee deep immutability for nested mutable values.

### 3.4 Modules, packages and imports

A **module** is generally one `.py` file; a **package** groups modules (modern namespace packages are also possible). When Python imports a module, its top-level statements execute. Therefore expensive connections, file writes, privilege changes, and command-line parsing should generally happen under `if __name__ == "__main__":` or through a tested entry point.

Typical project boundary:

```text
toyapp/
  __init__.py
  models.py       # validated domain types
  parser.py       # untrusted input -> domain types
  rules.py        # pure decisions
  adapters.py     # files, database, network
  cli.py          # argparse and exit codes
tests/
  test_parser.py
  test_rules.py
```

Imports are a **code execution boundary**, not a way to safely inspect unknown modules. Avoid shadowing standard-library names by creating files named `json.py`, `typing.py` or `socket.py` in your project.

### 3.5 Scope and closures

The LEGB rule searches Local, Enclosing, Global, Builtins. In a nested function, `nonlocal` rebinds an enclosing function's name; `global` rebinds a module-level name. Prefer passing state through objects, arguments and return values so tests can set up independent conditions. A closure captures referenced variables, not a frozen snapshot of all mutable objects.

### 3.6 Exercise ladder

**Beginner:** Convert a function that prints findings into one that returns a typed result, then print only in the CLI layer. **Intermediate:** Replace `MemorySink` with a stub that raises `OSError` and decide how the caller reports incomplete state. **Advanced:** Define a reader `Protocol` and build a full `parse → validate → analyze → report` pipeline with typed errors and cross-tenant authorization checks. Explain why annotation and dependency injection alone do not enforce identity or access policy.

**Review gate:** Given an arbitrary function, identify its contract, side effects, test seams, exception types and what the caller must guarantee before calling it.

## Good function boundaries
A function should have one clear responsibility, documented inputs/outputs, predictable failures, and no unnecessary hidden I/O. Separate **parse → validate → analyze → report** so that each stage can be tested independently. Prefer dependency injection to global state.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Alert:
    subject: str
    count: int
    severity: str

def decide_alert(subject: str, count: int, threshold: int = 5) -> Alert | None:
    if not subject or count < 0 or threshold < 1:
        raise ValueError("invalid alert parameters")
    if count < threshold:
        return None
    return Alert(subject=subject, count=count, severity="review")
```

**Python type annotations do not enforce runtime validation.** Use checks at trust boundaries and a dedicated validation layer when schemas are complex. Common constructs: `list[str]`, `dict[str, int]`, `str | None`, `Iterable`, `Protocol`, `TypedDict`, `Literal`, generics, narrowing, `Callable`, and `TypeVar`.

## Modules, packages, namespaces
`import module` is preferable when namespace clarity matters. `if __name__ == "__main__":` prevents executing CLI work on import. Organize modules by business responsibility: `parsers.py`, `models.py`, `detection.py`, `cli.py`. Avoid import-time network calls, mutable global registries, circular imports, and shadowing the standard library (e.g. naming your file `json.py`).

## Functional tools and closures
Understand `map`, `filter`, generators, comprehensions, `functools.partial`, decorators, closures, and `functools.lru_cache`. Cache only pure computations or carefully scoped data; caching credentials or authorization outcomes can introduce privacy and consistency bugs.

```python
from functools import wraps
from time import perf_counter

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {perf_counter() - start:.6f}s")
        return result
    return wrapper
```

## Security-oriented design
- Parse first; validate field types, lengths, ranges, and allowed values.
- Raise specific exceptions for invalid data; preserve original causes where appropriate.
- Keep secrets out of arguments shown in process listings and out of logs.
- Use immutable values for normalized, verified records where possible.
- Return structured results; avoid implicit printing inside reusable functions.
- Be explicit about timezone-aware timestamps and identifier canonicalization.

## Exercises
1. Convert a monolithic log parser into four independently testable functions.
2. Add precise typing and docstrings; run a static checker.
3. Design a dataclass for an alert and reject invalid severity/count values.
4. Explain why annotations alone do not block a string sent to an `int` argument.

References: [typing](https://docs.python.org/3/library/typing.html), [dataclasses](https://docs.python.org/3/library/dataclasses.html).
