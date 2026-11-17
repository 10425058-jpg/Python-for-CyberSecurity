# 01 — Python language foundations
> **Expanded textbook (Beginner → Advanced):** This chapter now includes a first-principles lesson, a runnable local program, a reasoning trace, failure cases and graduated exercises. For additional specialized lessons, see: [python runtime and types](../course/01-PYTHON-RUNTIME-AND-TYPES.md) · [control flow functions errors](../course/02-CONTROL-FLOW-FUNCTIONS-ERRORS.md).


**Goal:** read and write small programs confidently without depending on an assistant.


## Extended textbook 01 — A complete mental model of Python syntax and values

### 1.1 Source code as a sequence of evaluations

Start with an **expression** (something Python evaluates into a value), a **statement** (an action such as binding a name), a **block** (indented statements treated together), and a **module** (a Python source file). For example, `2 + 3` is an expression; `result = 2 + 3` is an assignment statement. `result` becomes a **name bound to an integer object**. Assignment does not declare a permanently fixed numeric storage cell.

`print` displays a representation of a value; `return` hands a result back from a function. Mixing the two makes code hard to test: functions that only print are not useful as reusable validation logic.

| Syntax | Plain-English meaning | Important boundary |
|---|---|---|
| `=` | bind a name | not a mathematical equality claim |
| `==` | compare values | not object identity |
| `is` | compare object identity | generally use for `None`, not string equality |
| `/` | true division | returns float for numbers |
| `//` | floor division | floors toward negative infinity |
| `%` | remainder | has sign rules; not always intuitive with negatives |
| `and` / `or` | short-circuit expressions | return operands, not always Boolean objects |
| `in` | membership test | meaning depends on collection |
| `not in` | non-membership | not equivalent to a trust decision |

### 1.2 Numbers, text and booleans: the deceptively simple parts

Python `int` has arbitrary precision in normal use; `float` is usually IEEE-754 binary64, so decimal fractions such as `0.1` cannot always be represented exactly. Use `decimal.Decimal` with documented rounding for financial quantities, and avoid using `float` to represent exact packet-length fields. `bool` is a subclass of `int` in Python; that inheritance is why `True == 1`. At a security JSON boundary, check the *exact semantic type* when integers and flags have different meanings.

Strings are immutable Unicode text, while `bytes` is a sequence of byte values. `len("é")` measures characters in that string (code points, not user-perceived grapheme clusters), whereas `len("é".encode("utf-8"))` measures two encoded bytes. An input byte cap must be applied before decoding, not after.

### 1.3 Control flow you can read aloud

An `if` chooses a branch, `elif` checks another condition, and `else` handles the remaining case. A `for` loop iterates values from an iterable; a `while` loop repeats while a condition is truthy. `break` stops the nearest loop and `continue` skips to the next iteration. A function's `return` exits the function immediately.

**Guard clauses** reject invalid inputs near the start, making the normal path easier to read. Avoid `if payload.get("count") or 5`: valid zero counts are falsy and will be replaced unexpectedly. Test for *presence* and *valid value* as independent decisions.

### 1.4 Build a complete toy rule and trace every state

```python
# TEXTBOOK_RUNNABLE
from typing import Any

ALLOWED = {"login_failure", "login_success"}

def parse_event(value: Any) -> tuple[str, str]:
    if type(value) is not dict or set(value) != {"actor", "action"}:
        raise ValueError("expected exact actor/action fields")
    actor, action = value["actor"], value["action"]
    if type(actor) is not str or not 1 <= len(actor) <= 32:
        raise ValueError("actor must be 1..32 characters")
    if type(action) is not str or action not in ALLOWED:
        raise ValueError("unknown action")
    return actor, action

def count_failures(rows: list[dict]) -> dict[str, int]:
    if type(rows) is not list or len(rows) > 100:
        raise ValueError("input record count exceeded")
    counts: dict[str, int] = {}
    for raw in rows:
        actor, action = parse_event(raw)
        if action == "login_failure":
            counts[actor] = counts.get(actor, 0) + 1
    return counts

records = [
    {"actor": "alex", "action": "login_failure"},
    {"actor": "sam", "action": "login_success"},
    {"actor": "alex", "action": "login_failure"},
]
assert count_failures(records) == {"alex": 2}
for bad in (
    {"actor": "alex", "action": "unknown"},
    {"actor": None, "action": "login_failure"},
    {"actor": "alex"},
):
    try:
        count_failures([bad])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid record accepted")
print("LAB 01 PASS")
```

**Trace the loop manually:**

| Iteration | Parsed actor | Action | Counter afterward |
|---|---|---|---|
| 1 | alex | failure | `{"alex": 1}` |
| 2 | sam | success | `{"alex": 1}` |
| 3 | alex | failure | `{"alex": 2}` |

Step 1 ensures the entire payload matches the expected dictionary shape. Step 2 validates values. Step 3 initializes an empty mapping. Step 4 increments a count **only** for failure records. Step 5 returns structured data, which can be independently tested. The validator's exact type checks also reject a dictionary subclass; the chapter's policy is intentionally conservative. Production schemas may need a documented extension mechanism instead.

### 1.5 Variables, aliasing and local state

`left = [1, 2]; right = left` makes two names for the **same list**; `right.append(3)` changes `left` too. `left.copy()` creates only a shallow copy: nested dictionaries remain shared unless separately copied. Strings and integers cannot be mutated in place, though a name can be rebound to a new value.

A function normally searches local names, enclosing-function names, global module names, then built-ins (LEGB). Prefer explicit function arguments over modifying globals. Never assume an annotation such as `x: int` stops Python callers from passing `"not an integer"`: validation remains a runtime responsibility.

### 1.6 Failure-mode clinic

**Case A:** Using `is` instead of `==` for arbitrary equal strings; object identity is not value equality.  
**Case B:** Using a mutable default `def add(x, out=[]):`; that list persists across calls. Use `None` and allocate inside.  
**Case C:** Concatenating untrusted values into shell commands or SQL; avoid interpreting data as program syntax.  
**Case D:** Assuming a successful parser proves a record is authentic; syntax and provenance are different.  
**Case E:** Catching every exception and returning `{}`; incomplete data is not the same as a clean analysis.

### 1.7 Exercises with answer checks

**Beginner:** Predict `7 // 2`, `-7 // 2` and `"é".encode("utf-8")` before running Python. *Check:* 3, -4 and two UTF-8 bytes. **Intermediate:** Write `parse_age(raw: str)` that accepts only ASCII digits and integers from 0 to 120. Add tests for `"0"`, `"120"`, `"-1"` and full-width Unicode digits. **Advanced:** Modify `count_failures` to keep the exact input line number in exceptions while guaranteeing that a malformed third event never produces a successful-looking partial report.

**Mastery gate:** explain the difference between `==` and `is`, why `True` can pass a naïve integer check, how a dictionary grows, how early returns work, and what input validation **does not** prove about attacker intent.


## 1.8 Deep Core I — How Python actually evaluates a statement

The first skill is **simulation by hand**, not memorization. Python reads the source according to a grammar, creates executable code, and evaluates expressions while binding names to objects. Indentation marks suites. Four spaces are conventional; tabs and spaces mixed inconsistently can raise `TabError`. A colon introduces a suite in `if`, `for`, `while`, `def` and similar compound statements. A comment starts with `#` outside a string; a docstring is a string literal used for documenting a module, class or function (it is not a comment).

A variable name is a reference, not a declaration of a fixed storage type. Evaluation order matters: the right-hand side of an assignment is evaluated **before** rebinding the left-hand name.

```python
# DEEP_CORE_RUNNABLE
left = [10, 20]
right = left
left = left + [30]        # constructs a new list and rebinds left
assert left == [10, 20, 30]
assert right == [10, 20]
assert left is not right
left = right
left += [40]              # list in-place addition mutates the shared list
assert right == [10, 20, 40]
assert left is right
print("D01-A: rebind and mutate are different")
```

| Step | `left` refers to | `right` refers to | Why |
|---|---|---|---|
| `left=[10,20]` | list A | unbound | construct list |
| `right=left` | A | A | alias, no copy |
| `left=left+[30]` | new list B | A | evaluate addition, then bind |
| `left=right` | A | A | alias again |
| `left += [40]` | A, now three items | A | list supports in-place extension |

**Crucial subtlety:** an augmented assignment asks the object to perform an in-place operation if available; the actual result depends on its type. `x += y` is not always interchangeable with `x = x + y` when objects are mutable. For tuples with nested mutable elements, augmented assignment can even mutate a contained list *before* a later tuple-item assignment fails—avoid clever one-liners when preserving forensic state.

**Practice:** predict list aliasing after `a[:]=[1]`, `a=a+[1]`, and `a.extend([1])`. Show which operations change aliases and which change only a binding. Explain why copying a list of dictionaries with `list.copy()` still aliases the inner dictionaries.

## 1.9 Deep Core II — Numbers: precision, ranges and Boolean traps

`int` expresses integers without a fixed machine-word size exposed by Python's language semantics; practical size is limited by available memory and sometimes string-conversion protections. `float` usually uses binary floating-point. Most decimal fractions have no finite representation in base two. Therefore:

- `0.1 + 0.2 == 0.3` is generally `False` for ordinary Python float values.
- `round` is not a replacement for an exact accounting specification.
- `Decimal("0.1")` constructs an exact decimal value for its literal text, whereas `Decimal(0.1)` imports the existing approximation.
- Numeric comparisons to non-finite values require explicit `math.isfinite` checks when policy requires finite values.
- `bool` inherits from `int`, so `isinstance(True, int)` is true. Validate semantic types at trust boundaries.

```python
# DEEP_CORE_RUNNABLE
from decimal import Decimal
import math

assert 0.1 + 0.2 != 0.3
assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
assert True == 1 and type(True) is bool
assert -7 // 2 == -4       # floor, not truncation toward zero
assert -7 % 2 == 1         # a == (a//b)*b + (a%b)
assert (-7 // 2) * 2 + (-7 % 2) == -7

def bounded_byte(value: object) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError("expected an unsigned byte")
    return value

for bad in (True, -1, 256, 3.5, "42", None):
    try:
        bounded_byte(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"invalid byte accepted: {bad!r}")
assert bounded_byte(255) == 255
assert not math.isfinite(float("nan"))
print("D01-B: numeric and type boundaries")
```

A network packet's length should be a *validated integer measured in bytes*, not a float. A probability field might accept a finite float in [0,1], but still reject a Boolean. The two fields have different contracts even if Python supports mathematical comparisons between their objects.

**Worked prediction:** Evaluate `-7 // 2` and `-7 % 2`. Floor division chooses the greatest integer ≤ -3.5, so the quotient is -4; the remainder is +1 because `-7 = (-4)*2 + 1`. A novice who assumes all languages truncate division toward zero would predict -3 and -1; that would be incorrect for Python here.

**Failure questions:** Why does `if not value` reject a valid zero? Why is `type(value) is int` stricter than `isinstance(value,int)`? Why is `Decimal("0.1")` preferable to `Decimal(0.1)` for a decimal input? Verify each with a test.

## 1.10 Deep Core III — Truth values, short-circuiting and precedence

Every object has a truth value (`bool(value)`), using `__bool__` or `__len__` where defined. False-like values include `None`, `False`, numeric zero, empty strings and empty collections. This does **not** mean they have the same *meaning*. A missing policy value, a deliberately zero threshold and an empty permitted-user list may require different responses.

`and` and `or` **return one of their operands**; they do not necessarily return a Boolean. Evaluation short-circuits once the result is determined. `not` always returns a Boolean. For critical authorization expressions, prefer explicit parentheses and independent named predicates.

| Expression | Evaluated value | Reason |
|---|---|---|
| `0 or 5` | `5` | first is falsy |
| `"" or "anonymous"` | `"anonymous"` | empty text is falsy |
| `"alice" and 7` | `7` | first is truthy, returns second |
| `False and (1 / 0)` | `False` | second not executed |
| `1 < 2 < 3` | `True` | chained comparisons |
| `[1] == [1]` | `True` | equal values |
| `[1] is [1]` | `False` for distinct list literals | different objects |

```python
# DEEP_CORE_RUNNABLE
def normalize_limit(payload: dict) -> int:
    if type(payload) is not dict or "limit" not in payload:
        raise ValueError("limit missing")
    value = payload["limit"]
    if type(value) is not int or not 0 <= value <= 20:
        raise ValueError("invalid limit")
    return value

assert normalize_limit({"limit": 0}) == 0
assert (0 or 5) == 5
assert ("alice" and 7) == 7
assert (False and (1 / 0)) is False
assert (1 < 2 < 3) is True
for bad in ({}, {"limit": None}, {"limit": True}):
    try:
        normalize_limit(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("missing/invalid limit accepted")
print("D01-C: presence is not truthiness")
```

**Security application:** do not write `allow = user.is_admin or policy.get("allow")` without validating the value returned from `policy`. An absent or malformed permission cannot be treated as a harmless default if the policy is fail-closed. Do not assume a complex Boolean expression authenticates the original source data.

## 1.11 Deep Core IV — Text is Unicode; protocols send bytes

Python `str` represents Unicode code points; `bytes` is a byte sequence. A user-visible "character" may consist of multiple code points (for example, a base letter plus a combining accent), while UTF-8 may use multiple bytes per code point. Therefore "length in characters", "length in code points" and "length in encoded bytes" are three different specifications.

`repr(value)` is especially useful for debugging whitespace, control characters and escape sequences; it is not a safe replacement for sanitizing logs containing secrets. `str.encode("utf-8")` and `bytes.decode("utf-8", "strict")` cross between representations. Strings are immutable; string concatenation creates a result, while `bytearray` allows mutable byte buffers.

```python
# DEEP_CORE_RUNNABLE
import unicodedata

composed = "\u00e9"
decomposed = "e\u0301"
assert composed != decomposed     # different code point sequences
assert len(composed) == 1 and len(decomposed) == 2
assert unicodedata.normalize("NFC", composed) == unicodedata.normalize("NFC", decomposed)
assert len(composed.encode("utf-8")) == 2
assert len(decomposed.encode("utf-8")) == 3
wire = "logon:alex".encode("utf-8")
assert wire.decode("utf-8", "strict") == "logon:alex"
try:
    b"\xff".decode("utf-8", "strict")
except UnicodeDecodeError:
    pass
else:
    raise AssertionError("invalid UTF-8 accepted")
print("D01-D: code points differ from bytes")
```

**Identity policy warning:** normalization is not automatically correct for account IDs. Two visually similar identities can be distinct according to an authoritative identity provider. Never apply arbitrary `lower()`, `casefold()` or Unicode normalization when making access decisions without a documented policy and migration/testing strategy. Store original event evidence and separately derived canonical values.

**Exercise:** Compare `len("🇻🇳")`, `len("👨‍👩‍👧")` and their UTF-8 byte lengths. Explain why neither answer necessarily equals the number of user-perceived grapheme clusters. Do not truncate arbitrary UTF-8 buffers at a fixed byte index and then assume they can be decoded.

## 1.12 Deep Core V — Slices, unpacking and comprehensions

A sequence uses zero-based positions. The slice `seq[start:stop:step]` includes `start` (when in range), excludes `stop` and supports negative indices/steps. A slice creates a **shallow** copy for built-in lists, not a recursively independent structure. Unpacking `a, b = pair` binds multiple names and validates the number of values. A starred assignment `head, *middle, tail = seq` collects a new list of the middle values.

Comprehensions transform/collect values. List comprehensions build an eager list; generator expressions produce values lazily. A nested comprehension can become hard to audit, and materializing millions of user-controlled items can exhaust memory.

```python
# DEEP_CORE_RUNNABLE
events = ["a", "b", "c", "d"]
assert events[1:3] == ["b", "c"]
assert events[::-1] == ["d", "c", "b", "a"]
head, *middle, tail = events
assert (head, middle, tail) == ("a", ["b", "c"], "d")
counts = [0, 3, 5, 1]
flagged = [n for n in counts if n >= 3]
assert flagged == [3, 5]
lazy = (n * 2 for n in counts)
assert next(lazy) == 0
assert list(lazy) == [6, 10, 2]
nested = [{"tags": ["auth"]}]
copy = nested[:]
copy[0]["tags"].append("review")
assert nested[0]["tags"] == ["auth", "review"]
print("D01-E: shallow copies preserve inner aliases")
```

**Security consequence:** a "redacted copy" made by slicing a list of dictionaries may still mutate original evidence. Use a deliberate schema-based transformation to produce a separate representation, with tests proving no confidential field leaks; do not assume `copy.deepcopy` fixes authorization.

**Study checkpoint:** Describe one situation where comprehensions improve readability and another where a plain loop with explicit error handling is safer.



## 1.13 Deep Core VI — Scope, arguments, closures and safe defaults

Python's name lookup normally follows **LEGB**: Local, Enclosing, Global, Builtins. Defining a function creates a function object; calling it creates a new local namespace. Arguments are passed as references to objects (sometimes described as *call by sharing*). When a function mutates a list argument, callers observing that list see the mutation; rebinding the local parameter name alone does not change the caller's binding.

Default arguments are evaluated **once when the `def` statement executes**, not on each call. That is why `def record(item, history=[]): ...` can share one list across invocations. A closure may retain access to an enclosing variable; a loop-created lambda often captures the *same binding* and observes its final value later.

```python
# DEEP_CORE_RUNNABLE
def unsafe_default(value, bucket=[]):
    bucket.append(value)
    return bucket

assert unsafe_default("a") == ["a"]
assert unsafe_default("b") == ["a", "b"]  # demonstrate the trap, not a pattern to copy

def safe_default(value, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(value)
    return bucket

assert safe_default("a") == ["a"]
assert safe_default("b") == ["b"]

late = [lambda: i for i in range(3)]
fixed = [lambda i=i: i for i in range(3)]
assert [fn() for fn in late] == [2, 2, 2]
assert [fn() for fn in fixed] == [0, 1, 2]

def append_one(items: list[int]) -> None:
    items.append(1)
data: list[int] = []
assert append_one(data) is None
assert data == [1]
print("D01-F: defaults, closures, and mutation")
```

| Mechanism | Object changed? | Binding changed? | Lesson |
|---|---|---|---|
| `a.append(x)` | usually yes (list) | no | caller sees mutation |
| `a = a + [x]` | creates new list | yes, local | caller keeps original |
| `return a` | none by itself | caller decides | make data flow explicit |
| default `bucket=[]` | one list persists | same default object | avoid accidental shared state |
| closure capturing `i` | sees enclosing binding | variable can change | bind values explicitly when needed |

**Scope exercise:** Write a closure-based counter with `nonlocal`. Then rewrite it as a small class. Which version has clearer state ownership and is easier to reset for unit tests? Avoid mutable global state in a detector that needs reproducible evaluation.

## 1.14 Deep Core VII — Decisions with `if`, `match`, loops and exception paths

Use `if/elif/else` for Boolean conditions, and `match/case` (Python 3.10+) when matching structures or variants. A match pattern binds names and may match even when fields are the wrong semantic type; it does **not** replace schema validation. Bare variable names in `case` patterns can be **capture patterns**, not equality comparisons to existing variables. Literal and qualified constant patterns have different behavior.

A loop may have an `else` block that runs when iteration completes without `break`. This is useful for "search completed without finding a match" but easy to misunderstand. `continue` starts the next iteration and `break` exits the loop only; neither exits the containing function.

```python
# DEEP_CORE_RUNNABLE
def normalized_action(raw: object) -> str:
    match raw:
        case {"action": "login_failure", "actor": actor} if type(actor) is str and actor:
            return "failure"
        case {"action": "login_success", "actor": actor} if type(actor) is str and actor:
            return "success"
        case _:
            raise ValueError("unsupported event shape or fields")

assert normalized_action({"action": "login_failure", "actor": "alex"}) == "failure"
assert normalized_action({"action": "login_success", "actor": "sam"}) == "success"
for bad in ({"action": "login_failure", "actor": None}, {"action": "other"}):
    try:
        normalized_action(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid event matched")

def first_seen(values: list[str], target: str) -> int | None:
    for index, value in enumerate(values):
        if value == target:
            return index
    else:                          # loop exhausted, no break
        return None

assert first_seen(["a", "b"], "b") == 1
assert first_seen(["a", "b"], "missing") is None
print("D01-G: matching is not full schema validation")
```

**Important limitation:** mapping patterns accept dictionaries with additional keys; the sample does not enforce an exact schema or prohibit subclasses. If a real API requires exactly `actor` and `action`, validate key sets separately (as demonstrated earlier in this chapter). Always test one missing field, one extra field, one wrong type, and one unknown enum value.

## 1.15 Deep Core VIII — Iteration tools and data-shape assumptions

`range(start, stop, step)` defines a lazy arithmetic sequence with an exclusive stop. `enumerate(iterable, start=...)` pairs each value with an index; this is a useful way to report input line numbers. `zip` combines streams until the shortest ends by default, which can silently drop unmatched records. Python 3.10+ supports `zip(..., strict=True)` to raise `ValueError` when lengths differ. `sorted` creates a sorted list and leaves the input alone; `list.sort` mutates the original list in place. Python's sort is stable, which helps preserve source order for tied timestamps.

```python
# DEEP_CORE_RUNNABLE
sources = ["idp-A", "idp-B"]
ids = ["e1", "e2"]
pairs = list(zip(sources, ids, strict=True))
assert pairs == [("idp-A", "e1"), ("idp-B", "e2")]
assert list(enumerate(["ok", "failed"], start=1)) == [(1, "ok"), (2, "failed")]
assert list(range(2, 8, 2)) == [2, 4, 6]
try:
    list(zip(sources, ["e1"], strict=True))
except ValueError:
    pass
else:
    raise AssertionError("mismatched input lengths silently truncated")

events = [(10, "a"), (9, "b"), (10, "c")]
assert sorted(events, key=lambda item: item[0]) == [(9, "b"), (10, "a"), (10, "c")]
assert events[0] == (10, "a")  # original order unchanged
print("D01-H: strict zip and stable sorting")
```

**Security connection:** if one file contains source names and another contains corresponding event IDs, ordinary `zip` can silently drop trailing IDs. A parser should reject length mismatches or document the policy, rather than quietly producing an incomplete-but-successful report.

## 1.16 Deep Core IX — String formatting, representations and safely displaying data

`str(x)` is intended to be readable; `repr(x)` is intended to expose a Python-oriented representation that often makes escapes visible. Neither guarantees HTML/SQL/shell safety. An f-string is an expression and can execute normal Python expressions; do not evaluate user-supplied f-string source or use `eval` on untrusted data.

For logging, keep confidential data **out** of the message instead of trying to escape it after it has entered a public sink. Escape text for its eventual output context: HTML text, a URL component, a CSV cell and a shell argument have different encoding rules. SQL queries need parameterized statements, not hand-crafted string escaping.

**Trace a formatting example:**

```python
# DEEP_CORE_RUNNABLE
from html import escape

message = "audit\nfailed"
assert "\\n" in repr(message)
assert "\n" in message
tag = "<script>untrusted</script>"
assert escape(tag, quote=True).startswith("&lt;script&gt;")
name = "alice"
count = 3
assert f"{name}: {count:03d}" == "alice: 003"
print("D01-I: representations are not security sanitizers")
```

**Prompt:** Why is it incorrect to treat HTML escaping as a general sanitizer for a value that later goes into a SQL query? Why is redaction often preferable to logging secrets and trying to hide them in a UI?

## 1.17 Deep Core X — Your first integrated defensive Python program

A beginner project should prove that you can connect the language elements without copying a monolithic solution. Your integrated task is to build an **offline authentication-event summarizer**. It reads synthetic data, validates each record's exact shape and permitted actions, counts events per actor, preserves the distinction between *complete* and *incomplete*, and prints a report only after the full source has passed validation.

**Recommended file layout:**

```text
python-foundations-lab/
  auth_summary.py              # pure functions + explicit CLI
  test_auth_summary.py         # tests from beginner to adversarial
  fixtures/
    valid.jsonl
    invalid-third-record.jsonl
  report.md                    # observed output and limitations
```

| Contract | Requirement | Example negative test |
|---|---|---|
| Read | owned, local file; max 1000 lines and 4096 bytes per line | extra-long line |
| Parse | strict UTF-8 and JSON object, no duplicate keys | `{"actor":"a","actor":"b"}` |
| Schema | exactly actor, action, timestamp, source, event_id | missing source |
| Validate | correct types, length, timezone-aware timestamp | `action=None`, naive time |
| Count | one source-qualified ID per event | duplicate ID |
| Report | complete result or explicit error | corrupt third record |
| Safety | never disable accounts; no live network | absence of outbound requests |

A complete, tested reference implementation is provided in the [Chapter 01 project](../projects/foundations/auth_summary.py) with [unit tests](../tests/test_foundations_projects.py). **Attempt your own implementation first.** The reference intentionally keeps authorization and source authenticity out of scope; it does not establish that the logs are truthful.

## 1.18 Deep Core XI — Exercises are a progression, not an answer to memorize

Work from [Chapter 01 — 25 Independent Exercises](../python/exercises/01-LANGUAGE-FOUNDATIONS-EXERCISES.md). The exercises include prediction, debugging, implementation, testing and explanation. Do not open the [separate solution key](../python/solutions/01-LANGUAGE-FOUNDATIONS-SOLUTIONS.md) until you have written and tested your own answer.

**Suggested pass standard:**
- **Beginner:** all input/output prediction tasks correct and no accidental shared-state bugs.
- **Intermediate:** valid/invalid schema tests and a working self-contained program.
- **Advanced:** explain the threat boundary, demonstrate failure propagation and defend a design decision.
- **Project:** repeatable test command, supported Python version, synthetic fixtures, and a report stating incomplete-input behavior.

## 1.19 Consolidation — Correctness you should be able to explain aloud

| Question | Key reasoning checkpoint |
|---|---|
| How does assignment differ from mutation? | names bind to objects; aliasing reveals in-place changes |
| Why is `bool` an unsafe integer stand-in at a JSON boundary? | `bool` subclasses `int`; domain type matters |
| Can a valid Unicode string have multiple byte encodings? | yes across encodings; UTF-8 gives a specific mapping per code-point sequence |
| Why is truthiness not field presence? | zero and empty values can be present but falsy |
| Why not use `zip` without strict mode for paired audit sources? | it may silently truncate |
| Does a `match` mapping pattern enforce an exact schema? | not by itself; additional keys may be present |
| Do type annotations validate untrusted JSON automatically? | no, runtime validators do that |
| If a parser fails after a valid record, is a partial count a complete report? | no, completeness is separate |


## 1. Python's execution model
Python programs are modules of statements; CPython commonly compiles source to bytecode interpreted by its virtual machine. Variables are **names bound to objects**, not fixed-size boxes. Objects have identity, type, and value. Python is dynamically typed, but type annotations can document expected values and aid static checking. Indentation defines blocks.

```python
name = "Ada"                 # str (immutable)
count = 3                    # int, arbitrary precision
ratio = 0.75                 # float, approximate binary number
enabled = True               # bool
missing = None               # sentinel: no value
print(f"{name}: {count * ratio:.2f}")
```

`is` compares identity; `==` compares values. Avoid `is` for integers/strings; `is None` is correct. Mutable objects may share references; rebinding is not mutation. Beware aliasing when passing lists or dicts.

## 2. Expressions and operators
Arithmetic: `+ - * / // % **`. Comparisons: `== != < <= > >=`. Boolean: `and or not` uses short-circuit evaluation; `in` tests membership. Bitwise operations: `& | ^ ~ << >>` for flags, masks and protocol fields. Parenthesize mixed boolean expressions to make security checks auditable. Remember `bool([])`, `bool("")`, and `bool(0)` are false, but a missing value is not always equivalent to an invalid one.

## 3. Strings, bytes and encoding
A `str` is Unicode text; `bytes` is an 8-bit sequence. Network packets and file digests use bytes. Encoding text to UTF-8 and decoding bytes must be explicit; wrong decoding corrupts evidence.
```python
message = "login failed"
wire = message.encode("utf-8")
assert wire.decode("utf-8") == message
assert b"\x00\xff".hex() == "00ff"
```
Know slicing (`s[start:stop:step]`), zero-based indexing, negative indices, string methods, and raw strings for regular expressions. Prefer `repr()` when debugging invisible characters.

## 4. Control flow
```python
severity = 7
if severity >= 8:
    verdict = "critical"
elif severity >= 5:
    verdict = "review"
else:
    verdict = "informational"

for event in ["ok", "fail", "fail"]:
    if event == "fail":
        print("review event")
```
Use `while` when termination depends on a condition, `for` when traversing an iterable. `break` exits a loop; `continue` skips one iteration; `pass` is a placeholder. Python `match` is useful for structural pattern matching, not a substitute for verifying untrusted input.

## 5. Functions and input contracts
```python
def categorize_failed_attempts(count: int) -> str:
    if count < 0:
        raise ValueError("count must be nonnegative")
    return "review" if count >= 5 else "normal"
```
Arguments can be positional, keyword, keyword-only (`*`), or positional-only (`/`). Default parameters are evaluated once at definition time: never use mutable defaults such as `items=[]`; use `None` and initialize inside.

## 6. Common security-relevant mistakes
- Concatenating untrusted input into a shell command, SQL statement, path, or HTML fragment.
- Using `eval()`, `exec()`, or unsafe deserialization on user data.
- Assuming `input()` returns a number; it always returns text and needs validation.
- Using `random` for credentials; use `secrets`.
- Forgetting exceptions and encoding errors when parsing external text.
- Using bare `except:`, which can hide interrupts and programming defects.

## Exercises
1. Write a function that accepts a nonnegative count and returns a severity label; test -1, 0, 4, 5, 100.
2. Convert a Unicode event message to UTF-8 bytes and print its hexadecimal form.
3. Parse a text severity input safely: reject decimals, negatives and extremely long inputs.
4. Explain identity vs equality using two lists with the same contents.
**Checkpoint:** predict output and types of ten short snippets without running them, then confirm experimentally.

References: [official tutorial](https://docs.python.org/3/tutorial/), [language reference](https://docs.python.org/3/reference/).
