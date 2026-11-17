# 05 — Error handling, tests, debugging and observability
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [testing ci and supply chain](../course/07-TESTING-CI-AND-SUPPLY-CHAIN.md).



## Extended textbook 05 — Learn to trust a failure report

### 5.1 What an exception represents

Exceptions are objects that describe why normal control flow could not continue. `raise ValueError("...")` reports invalid arguments or content; `OSError` commonly represents operating-system failures; `json.JSONDecodeError` represents invalid JSON syntax; `PermissionError` and `FileNotFoundError` are more specific I/O failures. A `try` block guards an operation, `except` catches **specified** failures, `else` runs when no exception was raised, and `finally` performs cleanup regardless of whether the protected code completed normally.

An exception handler should preserve **meaning**, not erase it. Converting a low-level JSON error into a clearly described domain-level error with `raise InvalidInput(...) from exc` is useful. Returning an empty list from every `except Exception` is dangerous: a broken data source looks identical to a clean source.

### 5.2 Three distinct outcomes a diagnostic tool must model

| Outcome | Example | What a user should see |
|---|---|---|
| Valid and zero findings | empty but valid log | completed, zero matching events |
| Valid and one finding | successful full ingest | completed, one review event |
| Incomplete | malformed byte, missing file, DB error | **not a clean result**, visible error |

Treat output completeness and the number of findings as separate dimensions. Do not mark incomplete ingestion successful just because some records were processed.

### 5.3 Tests are executable predictions

A **unit test** exercises one bounded behavior, often without real I/O. An **integration test** checks interactions between components such as a parser and SQLite. A **regression test** records a previous bug so it cannot silently return. A **property test** checks general invariants over many generated inputs, with reproducible seeds and resource limits. `unittest` is built into Python, while pytest and Hypothesis are optional third-party tools.

Every security-sensitive parser should have at least: valid input, malformed syntax, missing/extra fields, wrong types, boundary values, enormous inputs, duplicate keys, Unicode edge cases, and failure propagation. Coverage percentage measures which lines ran, not whether the assertions express the right security invariant.

### 5.4 Full example — errors, assertions, unit tests, and messages

```python
# TEXTBOOK_RUNNABLE
import json
import unittest

class InvalidEvent(ValueError):
    """An untrusted event violates the documented schema."""

def decode_count(raw: bytes) -> int:
    if type(raw) is not bytes or len(raw) > 256:
        raise InvalidEvent("event exceeded the byte limit")
    try:
        event = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidEvent("event encoding or syntax is invalid") from exc
    if type(event) is not dict or set(event) != {"failures"}:
        raise InvalidEvent("event schema is invalid")
    count = event["failures"]
    if type(count) is not int or not 0 <= count <= 20:
        raise InvalidEvent("failures must be a bounded integer")
    return count

class DecoderTests(unittest.TestCase):
    def test_valid_zero(self):
        self.assertEqual(decode_count(b'{"failures":0}'), 0)
    def test_three(self):
        self.assertEqual(decode_count(b'{"failures":3}'), 3)
    def test_bool_not_count(self):
        with self.assertRaises(InvalidEvent):
            decode_count(b'{"failures":true}')
    def test_bad_json(self):
        with self.assertRaises(InvalidEvent):
            decode_count(b'{"failures":')
    def test_oversize(self):
        with self.assertRaises(InvalidEvent):
            decode_count(b"x" * 257)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(DecoderTests)
test_result = unittest.TestResult()
suite.run(test_result)
assert test_result.wasSuccessful() and test_result.testsRun == 5
print("LAB 05 PASS")
```

**How to read a test:** `self.assertRaises(InvalidEvent)` means **this invalid input must fail**; silently accepting it fails the test. Tests run independently, so an unexpected exception is reported by the test runner instead of ignored. `test_result` separates execution status from printed text; a CI job must exit nonzero on failure. The sample intentionally keeps the parser small; a production JSON validator would additionally reject duplicate keys and nonstandard numeric constants.

### 5.5 Debugging: hypotheses, reproduction, inspection

When a script fails: record the exact command and Python version, build the smallest reproducible input, locate the first incorrect assumption, inspect actual variable types and state transitions, add a test, fix the defect, then rerun the whole suite. Use `pdb`, the debugger in your IDE, and `traceback` for local work. A traceback can contain paths, input snippets and secrets: do not copy full production traces into public bug reports.

### 5.6 Logging without leaking secrets

The `logging` module has severity levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`); those levels are **operational priorities**, not a formal incident classification. Prefer structured metadata such as an internal event ID, rule name and sanitized error type. Never blindly log raw passwords, tokens, cookies, entire request bodies or personal data. Logging itself can fail or saturate disk: use bounded retention, careful formatting and error-rate monitoring.

### 5.7 Practice: make an incorrect test fail

**Beginner:** Introduce a wrong function that accepts `True` as an integer and write a test that fails on the exact type boundary. **Intermediate:** Make a parser raise on its third record, then verify that a caller does not return a successful-looking partial list. **Advanced:** Implement a local, staged JSONL report that preserves the existing complete report when ingestion fails after the first finding. Document crash-durability limits.

**Mastery gate:** you can explain the difference between an expected bad input, a program bug and an environmental failure; you can create a regression test for each and show that CI reports failure instead of hiding it.

## Exception design
Use `try` only around the statement that can fail; catch specific exceptions. Preserve stack traces with `raise` and chain causes with `raise NewError(...) from exc` when translating failures. Never return a successful-looking empty result after an unexpected exception.

```python
import json

def parse_record(line: str) -> dict:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON record") from exc
    if not isinstance(obj, dict):
        raise ValueError("expected a JSON object")
    return obj
```

## Testing strategy
1. **Unit tests:** pure functions and validation; no network or filesystem side effects.
2. **Integration tests:** parser + database + local test fixture.
3. **Property/fuzz tests:** many generated valid/invalid inputs; establish invariants.
4. **Regression tests:** add one after every resolved bug.
5. **Security tests:** malformed paths, Unicode, timeouts, authorization edge cases, injection-like strings treated as data.
6. **Performance tests:** memory and response limits for large or adversarial input.

```python
import unittest
class ParseTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse_record('{"ok": true}'), {"ok": True})
    def test_non_object(self):
        with self.assertRaises(ValueError):
            parse_record("[]")
```

## Tooling and quality
- `python -m unittest discover -s tests -v` (stdlib), or pytest for fixture-rich workflows.
- `python -m compileall .` for syntax validation.
- `ruff check .` for lint and `ruff format .` for consistent style.
- `mypy` or pyright for static typing.
- `bandit -r src` for a security-oriented static analysis pass; findings still require human review.
- `pip-audit` for known vulnerable dependencies; absence of findings is not proof of safety.
- CI should fail for test regressions and block publication of secrets.

## Logging and tracing
Use `logging` with structured, contextual metadata; avoid raw credentials, access tokens, session cookies, complete personal identifiers, or entire untrusted payloads. Preserve request correlation IDs where authorized. Rate-limit repetitive errors and monitor false positives. Use `pdb`, IDE breakpoints, and `traceback` locally; sanitize tracebacks exposed to users.

## Exercises
1. Write table-driven tests for a severity classifier.
2. Make a parser robust against a blank line, object/list confusion, and 10 MB fields.
3. Add a log handler and prove no secret token is emitted.
4. Explain expected error vs unexpected programmer error and why broad catches obscure bugs.

References: [unittest](https://docs.python.org/3/library/unittest.html), [logging](https://docs.python.org/3/library/logging.html), [Bandit](https://bandit.readthedocs.io/).
