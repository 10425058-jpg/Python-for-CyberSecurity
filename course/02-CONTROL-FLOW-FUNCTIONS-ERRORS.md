# Deep Dive 02 — Control flow, functions, errors and designing trustworthy scripts

> **Hands-on:** [Chapter 02 Guided Lab](../lab-manual/02-GUIDED-LAB.md) · [100 numbered worked answers](../solutions/by-exercise/README.md). Complete the lab's negative tests before moving on.

**Level:** beginner → intermediate · **Estimated study:** 6–8 hours.

## Learning goals
Design a script that clearly separates parsing, validation, decision-making and output. Understand branches, loops, scoping, call signatures, exceptions, generators, and the difference between returning an error and printing a message.

## 1. Branches and short-circuit evaluation

A boolean expression can skip the right operand. For example, `a and b` evaluates `b` only if `a` is truthy; `a or b` evaluates `b` only if `a` is falsy. This can avoid expensive or unsafe operations **only if the left condition is correctly designed**.

```python
def allowed_actor(actor: object) -> bool:
    return isinstance(actor, str) and 1 <= len(actor) <= 64 and actor.isascii()

assert allowed_actor("alice")
assert not allowed_actor(None)
assert not allowed_actor("a" * 100)
```

If the `isinstance` guard did not come first, `len(None)` would raise. Security code should make branch order explicit.

### The "fail-open" problem
```python
# BAD: invalid values might default to allowed.
# if not policy.get("blocked"):
#     grant_access()

# Better: define and validate the complete policy schema.
def policy_permits(policy: dict) -> bool:
    if set(policy) != {"enabled", "blocked"}:
        raise ValueError("incomplete policy")
    if type(policy["enabled"]) is not bool or type(policy["blocked"]) is not bool:
        raise ValueError("wrong policy types")
    return policy["enabled"] and not policy["blocked"]
```

A security-sensitive policy should not silently choose permissive values when fields are absent or malformed.

## 2. `for`, `while`, `break`, `continue`, `else`

A `for` loop consumes an iterable (not necessarily a list). `while` repeats until its condition becomes false; it must have a provable termination path or deadline. `break` exits the loop; `continue` advances to the next iteration. The less-familiar `for ... else` block executes if the loop finishes *without* `break`.

```python
def has_forbidden_marker(lines: list[str], marker: str) -> bool:
    for line in lines:
        if marker in line:
            break
    else:
        return False
    return True
```

### Resource limits are loop invariants
Never read unlimited lines or decode unlimited nested structures just because your script is "read-only". A local file, API or data feed can be large or deliberately malformed.

```python
def capped_lines(source, max_lines: int = 1000):
    if max_lines < 1:
        raise ValueError("invalid max_lines")
    for index, line in enumerate(source):
        if index >= max_lines:
            raise ValueError("line cap exceeded")
        yield index + 1, line
```

## 3. Functions: inputs, outputs and contracts

A good security-oriented function documents:
- Accepted types, lengths and ranges.
- What it returns on success.
- Which exceptions it raises on failure.
- Whether it performs I/O or modifies external state.
- Resource consumption and permissions.

```python
def fail_ratio(*, failures: int, attempts: int) -> float:
    """Return failure fraction for positive attempts, both integer counts."""
    if type(failures) is not int or type(attempts) is not int:
        raise TypeError("counts must be integers")
    if attempts <= 0 or not 0 <= failures <= attempts:
        raise ValueError("counts out of range")
    return failures / attempts

assert fail_ratio(failures=2, attempts=8) == 0.25
```

The `*` forces keyword arguments, which reduces mistakes when parameters have similar meanings. The docstring is not a substitute for input checks; they serve different purposes.

### Positional-only and keyword-only
`def f(a, /, b, *, c):` means `a` must be positional, `b` may be either, and `c` must be keyword. Prefer explicit names in APIs where swapped parameters would cause significant harm.

### Defaults are evaluated once
```python
# BAD:
def append_actor_bad(actor, actors=[]):
    actors.append(actor)
    return actors

# GOOD:
def append_actor(actor, actors=None):
    if actors is None:
        actors = []
    actors.append(actor)
    return actors
```

The bad version carries mutable state across calls, causing cross-incident contamination.

## 4. Scope and closures: LEGB

Python resolves names in Local → Enclosing → Global → Built-in scopes. A closure captures bindings in its enclosing function. Be wary of the common "late binding" issue: closures created in a loop often read the final loop variable when called later.

```python
rules = []
for threshold in (2, 5, 10):
    rules.append(lambda count, threshold=threshold: count >= threshold)
assert [rule(6) for rule in rules] == [True, True, False]
```

Here the explicit default parameter captures each threshold at creation. For security rules, named classes or plain functions can be easier to audit than clever closures.

## 5. Exceptions are part of your API

Parse errors, invalid user input, external I/O failures and programmer bugs should not all be collapsed into `except Exception: return []`.

```python
import json

def parse_object(raw: str) -> dict:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("malformed JSON") from exc
    if not isinstance(obj, dict):
        raise ValueError("a JSON object is required")
    return obj
```

### Exception taxonomy
- `ValueError`: value is the wrong format/range.
- `TypeError`: wrong type.
- `OSError` and subclasses: filesystem/network failures.
- `TimeoutError`: deadline exceeded.
- `KeyError`: required field missing (often translate to validation failure).
- `RuntimeError`: a state/condition prevents progress.

When security-relevant processing fails unexpectedly, use a non-zero exit code and preserve detailed diagnostics in a protected location. Do not print secrets or full attacker-controlled payloads into logs. `finally`/context managers release resources even if an exception occurs.

## 6. Generator-based processing

Generators `yield` results one at a time, which is ideal for large log streams. They are lazy: invalid rows may be encountered only after some output has already been emitted. Design downstream consumers accordingly.

```python
import json

def iter_valid_actions(lines, max_line_chars=8192):
    for line_number, raw in enumerate(lines, 1):
        if len(raw) > max_line_chars:
            raise ValueError(f"line {line_number}: too long")
        if not raw.strip():
            continue
        data = parse_object(raw)
        action = data.get("action")
        if not isinstance(action, str):
            raise ValueError(f"line {line_number}: action missing")
        yield line_number, action
```

If you need all-or-nothing output, validate into an intermediate staging file or transaction first. Do not pretend streaming output is atomic.

## 7. Worked example — separate parser, policy and CLI

```python
import json
from pathlib import Path
from collections import Counter

def parse_action_line(raw: str) -> str:
    data = parse_object(raw)
    action = data.get("action")
    if action not in ("login_success", "login_failure"):
        raise ValueError("unrecognized action")
    return action

def count_actions(path: Path) -> Counter:
    counts = Counter()
    with path.open(encoding="utf-8") as stream:
        for number, raw in enumerate(stream, 1):
            if not raw.strip():
                continue
            try:
                action = parse_action_line(raw)
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
            counts[action] += 1
    return counts

# Reusable functions do not call print() or sys.exit(); a CLI wrapper can.
```

**Review:** the function accepts local paths that the caller is authorized to read, reports line numbers, keeps structured counts and raises on malformed records instead of silently skipping them. For untrusted file uploads, add file/line size caps before using this pattern.

## 8. How to test

```python
import unittest
class PolicyTests(unittest.TestCase):
    def test_allowed(self):
        self.assertTrue(policy_permits({"enabled": True, "blocked": False}))
    def test_missing_key_denied(self):
        with self.assertRaises(ValueError):
            policy_permits({"enabled": True})
    def test_wrong_type(self):
        with self.assertRaises(ValueError):
            policy_permits({"enabled": 1, "blocked": False})
```

Testing needs normal, boundary and error cases. A test named `test_policy` is less informative than names explaining which invariant was checked.

## 9. Pitfalls to recognize

| Pitfall | Example consequence | Remedy |
|---|---|---|
| Exception swallowed | silent loss of incident data | raise with context; alert operator |
| Endless loop | busy CPU / stuck worker | deadlines and bounded retries |
| Mutable default | data leaks across analyses | fresh objects |
| Late-bound closure | wrong detection threshold | explicit capture or classes |
| I/O in business logic | slow, hard-to-test rules | separate pure and impure layers |
| Log raw payload on errors | inadvertent secret disclosure | redact/truncate metadata |

## 10. Practice and answer checks
**1.** Create a function that accepts an integer failure count 0–1000 and returns a string severity. Include five boundary tests. Expected: invalid values raise; never silently coerce floats.

**2.** Turn a list-based parser into a generator and measure memory usage on 100,000 synthetic lines. Expected: generator memory is bounded when downstream does not accumulate events.

**3.** Simulate a missing policy field and ensure access is denied with a clear error. Explain "fail closed" versus "fail open."

**4.** Rewrite a script with `except: pass` to use specific errors and a nonzero CLI status.

**Review questions:** Why use keyword-only arguments? When is an exception more appropriate than returning `None`? What does a generator give up in exchange for low memory?

**References:** [Python control flow](https://docs.python.org/3/tutorial/controlflow.html), [exception hierarchy](https://docs.python.org/3/library/exceptions.html), [contextlib](https://docs.python.org/3/library/contextlib.html).


## 11. Detailed failure-handling case: building a defensive event classifier

A fragile program might report "0 suspicious events" after catching `Exception` and discarding parser failures. That is a **false all-clear**: the user cannot tell the difference between a clean dataset and an unreadable dataset.

### Design the function contract first

Input: a list of synthetic event dictionaries, each containing `action` (string) and `actor` (nonempty string). Output: number of failures by actor. Error behavior: reject an invalid row with its index. Side effects: none. Resource policy: at most 1000 events and 100 different actors. A function that satisfies this contract is testable without a database or network.

```python
from collections import Counter

def count_failures(events: list[dict]) -> dict[str, int]:
    if type(events) is not list or len(events) > 1000:
        raise ValueError("expected up to 1000 events")
    totals = Counter()
    for index, event in enumerate(events):
        if type(event) is not dict or set(event) != {"actor", "action"}:
            raise ValueError(f"row {index}: invalid schema")
        actor = event["actor"]
        action = event["action"]
        if type(actor) is not str or not 1 <= len(actor) <= 64:
            raise ValueError(f"row {index}: invalid actor")
        if action not in ("login_failure", "login_success"):
            raise ValueError(f"row {index}: invalid action")
        if action == "login_failure":
            if actor not in totals and len(totals) >= 100:
                raise ValueError("actor cardinality cap exceeded")
            totals[actor] += 1
    return dict(totals)

assert count_failures([
    {"actor":"alice","action":"login_failure"},
    {"actor":"alice","action":"login_success"},
    {"actor":"alice","action":"login_failure"},
]) == {"alice":2}
```

**Explain the order:** validate the container before looping, schema before indexing, actor before using it as a dictionary key, action before branching, and cardinality before inserting a **new** actor. One malformed event invalidates the whole batch. That is a deliberate strict policy; systems using quarantine instead must track rejected rows and completeness.

### Proof obligations and tests

```python
import unittest

class CountingContractTests(unittest.TestCase):
    def test_empty_means_complete_zero(self):
        self.assertEqual(count_failures([]), {})

    def test_bad_record_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "row 0"):
            count_failures([{"actor":"alice"}])

    def test_malformed_type_rejected(self):
        with self.assertRaises(ValueError):
            count_failures([{"actor":None,"action":"login_failure"}])

    def test_unknown_action_rejected(self):
        with self.assertRaises(ValueError):
            count_failures([{"actor":"a","action":"reset-password"}])
```

A return value of `{}` now has a precise meaning: the *valid complete input* contained no failures. It never represents a suppressed parse error.

## 12. Scope, closures and an accidental policy bug

```python
thresholds = [2, 4, 8]
bad_rules = [lambda count: count >= threshold for threshold in thresholds]
print([rule(3) for rule in bad_rules])  # [False, False, False]
```

All closures read the final loop variable when invoked: `threshold==8`. The corrected form captures each value explicitly:

```python
rules = [lambda count, t=t: count >= t for t in thresholds]
assert [rule(3) for rule in rules] == [True, False, False]
```

**Cybersecurity consequence:** detection rules generated using a loop can unintentionally all use the highest threshold, hiding important events. Prefer a named function or a typed policy object for serious security decisions.

## 13. A complete command-line exit policy

Your CLI should distinguish:
- Exit **0**: all requested input processed successfully (even if zero findings).
- Exit **2**: malformed user input, invalid schema or incorrect usage.
- Exit **3**: file I/O or external dependency failure (convention chosen by this program).
- Exit **130**: interrupted by Ctrl+C on many Unix-like shells (platform-specific).

```python
import sys

def run_cli(path, parser):
    try:
        return parser(path)
    except ValueError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"I/O failure: {type(exc).__name__}", file=sys.stderr)
        return 3
```

The contract above treats `parser` as an injected operation whose return value is an integer status; document it or return a typed result object instead. Don't log full untrusted records or secrets. Specific errors are preferred to silently catching every failure.

### Exercise ladder and checks
1. **Predict** the outcome of `if []: ... elif 0: ... else: ...`. Answer: else branch.
2. **Refactor** a function using `except Exception: return []` so failure cannot be confused with a valid empty result.
3. **Test** invalid `action` values, including a dict, a list and a 1 MB string. Enforce overall byte caps before materializing large records.
4. **Analyze** why it is wrong to grant access in a broad exception handler. Answer: exceptions must fail closed at authorization boundaries.
5. **Design** retry behavior when an API write times out. A timeout does **not** prove the server never executed the write: use idempotency keys or read-back validation.

**Discussion:** would skipping one bad row be preferable to failing the entire batch? Either can be appropriate, but the API must explicitly report incomplete processing, quarantine counts and which evidence was discarded.
