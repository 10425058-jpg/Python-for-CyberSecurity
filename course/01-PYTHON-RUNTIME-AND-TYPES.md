# Deep Dive 01 — How Python actually works: objects, types, references, memory and trust

**Level:** beginner → intermediate · **Prerequisites:** terminal and a working Python 3 environment · **Estimated study:** 6–10 hours.

## Learning outcomes
By the end, you can explain the difference between a variable name and an object, predict mutability and aliasing bugs, distinguish bytes from text, understand numeric edge cases, and build input validators that do not silently accept unintended types.

## 1. What happens when you run a Python program?

Suppose you run `python app.py`. The OS starts a Python interpreter process. The interpreter reads the source, compiles it into instructions (usually bytecode in CPython), and executes those instructions. It imports referenced modules as needed. When imported, top-level module statements execute: this is why a network call at module import time is dangerous in library code.

A Python *name* identifies a binding to an *object*. The object knows its type and value. Consider:

```python
a = [1, 2]
b = a
c = a.copy()
b.append(3)

assert a == [1, 2, 3]
assert b is a          # exact same list
assert c == [1, 2]     # independent shallow copy
assert c is not a
```

Walkthrough:
1. `[1, 2]` creates one mutable list object.
2. `a` points at it.
3. `b = a` binds another name to **the same** object.
4. `a.copy()` makes a new list containing references to the same elements. This is *shallow*, not recursive.
5. `b.append(3)` modifies the shared object; anyone pointing at it sees the change.

In cybersecurity, a parser that appends a flag to a shared list could accidentally contaminate future events. Do not confuse rebinding (`b = []`) with mutation (`b.clear()`).

### Mutable versus immutable values
Common immutable objects: `int`, `float`, `bool`, `str`, `bytes`, `tuple` (its members can still be mutable), `frozenset`. Mutable objects: `list`, `dict`, `set`, `bytearray`. Immutability often makes a normalized security event safer to pass across layers, but does **not** automatically make it secret or thread-safe.

```python
coordinates = (["old"], 9)
coordinates[0].append("new")
assert coordinates == (["old", "new"], 9)
```

A tuple's references do not change, but the nested list still can.

## 2. Identity, equality and hashing

`==` means "these values compare equal"; `is` means "these names refer to the exact same object". `hash()` allows immutable, hashable keys in dictionaries and sets, but Python's object hash is **not a cryptographic hash** and may vary between processes. Use `hashlib` for integrity checks.

```python
x = {"role": "analyst"}
y = {"role": "analyst"}
assert x == y and x is not y
assert None is None
```

Do not write `if value is 200:`. CPython may reuse particular integer/string objects, which is an implementation detail and cannot be relied upon.

## 3. Numeric behavior that matters in security

- `int` has arbitrary precision; it will not overflow like a fixed 32-bit unsigned integer. But when converting protocol fields to native sizes, enforce explicit limits.
- `float` stores an approximation of most decimal fractions. Avoid it for financial totals and exact security policy thresholds when exact decimals are required.
- `bool` is a subclass of `int`. As a result, `isinstance(True, int)` is true. For strict port, retry-count or timeout parameters, reject booleans deliberately.
- Division: `/` produces a float; `//` floors; modulo on negative values can surprise beginners.
- Extremely large integer conversions or repeated exponentiation can still consume resources.

```python
def require_port(value: object) -> int:
    if type(value) is not int:
        raise TypeError("port must be an integer (not bool)")
    if not 1 <= value <= 65535:
        raise ValueError("port must be between 1 and 65535")
    return value

for bad in [True, -1, 0, 65536, "443"]:
    try:
        require_port(bad)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(f"accepted {bad!r}")
```

**Security connection:** before using a JSON value as a limit, check its *type*, then its *range*. Python's dynamic coercions can hide invalid assumptions.

## 4. Truthiness is not validation

`if not value` groups together `None`, `False`, `0`, `""`, and empty collections. That is often too broad for security decisions.

```python
def parse_limit(data: dict) -> int:
    if "limit" not in data:             # absent key
        return 100                     # intentional default
    value = data["limit"]              # present; might be 0
    if type(value) is not int or not 1 <= value <= 1000:
        raise ValueError("invalid limit")
    return value
```

An API endpoint that treats `{"limit": 0}` as "no limit" due to a careless falsy check can unintentionally expose large datasets.

## 5. Unicode, text and bytes

A `str` is a sequence of Unicode code points (not always perceived user characters); `bytes` is a sequence of integers in [0,255]. A network protocol transmits bytes; you *encode* text to bytes and *decode* bytes back to text. Unicode characters can be written in different but canonically equivalent sequences: normalization may matter for usernames, file paths and identifiers.

```python
import unicodedata
text = "café"
composed = unicodedata.normalize("NFC", text)
decomposed = unicodedata.normalize("NFD", text)
assert composed != decomposed
assert unicodedata.normalize("NFC", composed) == unicodedata.normalize("NFC", decomposed)
wire = composed.encode("utf-8", errors="strict")
assert wire.decode("utf-8", errors="strict") == composed
```

Do not normalize raw evidence *in place*: preserve the original bytes and store a separately derived canonical field. Do not use `errors="ignore"` when evidence fidelity matters; it silently drops undecodable bytes.

### Bytes as evidence
```python
raw = b"\x00\xffALERT\n"
print(raw.hex())       # 00ff414c4552540a
print(repr(raw))       # shows escapes
assert raw[1] == 255   # indexing bytes returns int
```

## 6. Type annotations are documentation, not runtime protection

`def check(value: int)` does **not** stop Python from accepting `"abc"`. Static type checkers help during development; runtime boundaries still require explicit validation.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class LoginEvent:
    actor: str
    failures: int

def build_event(actor: object, failures: object) -> LoginEvent:
    if not isinstance(actor, str) or not (1 <= len(actor) <= 128):
        raise ValueError("actor must be 1–128 characters")
    if type(failures) is not int or not 0 <= failures <= 10_000:
        raise ValueError("failure count outside allowed range")
    return LoginEvent(actor=actor, failures=failures)
```

`frozen=True` blocks reassignment of top-level fields; it does not deeply freeze nested lists/dicts. Prefer immutables all the way down for normalized records.

## 7. Worked security example — validate an alert event

Input contract: a JSON object with exactly `{"username", "failed_attempts", "source"}`. Username 1–64 chars, count 0–1000, source one of `lab` or `test`. This exercise rejects ambiguous extra keys rather than guessing.

```python
ALLOWED_SOURCES = {"lab", "test"}
FIELDS = {"username", "failed_attempts", "source"}

def validate_alert(payload: object) -> tuple[str, int, str]:
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        raise ValueError("wrong event structure")
    username = payload["username"]
    count = payload["failed_attempts"]
    source = payload["source"]
    if not isinstance(username, str) or not 1 <= len(username) <= 64:
        raise ValueError("invalid username")
    if type(count) is not int or not 0 <= count <= 1000:
        raise ValueError("invalid count")
    if source not in ALLOWED_SOURCES:
        raise ValueError("unsupported source")
    return username, count, source

assert validate_alert({"username": "alex", "failed_attempts": 5, "source": "lab"}) == ("alex", 5, "lab")
```

Why this matters: attacker-controlled JSON may use wrong types, nested objects, oversized fields or unexpected keys. Without a schema, later modules can misinterpret the data, potentially making an incorrect security decision.

## 8. Frequent mistakes and corrections
| Mistake | Why it fails | Better practice |
|---|---|---|
| `is` used for comparing values | identity is not value equivalence | use `==` |
| `if not value` as schema validation | conflates missing/zero/empty | check presence, type, bounds |
| Shared mutable defaults | state leaks across calls | use `None` + fresh object |
| `float` for exact counting/money | rounding error | use integers or Decimal |
| `str(binary_blob)` | generates representation, not decoding | decode with explicit encoding |
| Silently dropping decode errors | corrupts evidence | strict handling and error reports |
| `hash()` for integrity | non-cryptographic and unstable | `hashlib.sha256` |

## 9. Exercises (try before solutions)
**A — Beginner:** Explain why mutating `b` in `a = [[]]; b = a.copy(); b[0].append(9)` also changes `a`. Draw the reference graph.

**B — Intermediate:** Add a `level` field to the alert example. Accept only `{"low", "medium", "high"}` and reject wrong case, `None` and oversized strings. Test each rejected case.

**C — Advanced:** Attack your own validation function using a generated list of wrong types, booleans, empty strings, nested containers and 1 MB text. Your function must raise a predictable exception without large memory allocation.

### Hints / answer checks
A: the outer list is copied, but the inner list is still shared. B: use explicit type and membership checks before accessing. C: enforce maximum serialized/field size at the parse boundary *before* allocating large nested structures.

## Self-check
1. What changes with assignment versus mutation?
2. Why are `True` and `1` a trap in numeric JSON validation?
3. When is normalization good, and when would it destroy forensic fidelity?
4. Does a type hint prevent a malicious value at runtime?
5. Why do we keep original evidence bytes separate from derived strings?

**Further reading:** [Python data model](https://docs.python.org/3/reference/datamodel.html), [built-in types](https://docs.python.org/3/library/stdtypes.html), [Unicode HOWTO](https://docs.python.org/3/howto/unicode.html).
