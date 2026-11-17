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
