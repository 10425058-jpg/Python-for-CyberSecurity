# Deep Dive 07 — Tests, property-based thinking, CI and Python supply-chain security

**Level:** intermediate · **Estimated study:** 10–14 hours.

## 1. A security tool needs evidence of correctness

"Runs without throwing" is not a meaningful quality guarantee. A defensive detector may silently miss incidents, misread time zones or turn one malformed event into hundreds of false alerts. We need tests for properties and failure modes, not merely for output formatting.

### Build a test pyramid
- **Unit:** pure validation, calculation, detection thresholds.
- **Integration:** parser + SQLite + local test adapters.
- **Contract:** API request/response fields, allowed error behavior.
- **End-to-end:** fixture file → normalized events → alerts → report.
- **Security:** oversized inputs, wrong types, malformed UTF-8, path boundaries and authorization denials.
- **Performance:** bounded memory and time under realistic volume.
- **Fault injection:** database unavailable, timeout, duplicate events, killed process.

Each category answers a different question. A 100% line-coverage number by itself does not establish safety.

## 2. Arrange / Act / Assert

```python
import unittest

def failed_ratio(failures: int, total: int) -> float:
    if type(failures) is not int or type(total) is not int:
        raise TypeError("integer counts only")
    if total <= 0 or not 0 <= failures <= total:
        raise ValueError("invalid counts")
    return failures / total

class FailedRatioTests(unittest.TestCase):
    def test_normal_case(self):
        actual = failed_ratio(2, 8)
        self.assertEqual(actual, 0.25)

    def test_zero_denominator(self):
        with self.assertRaises(ValueError):
            failed_ratio(0, 0)

    def test_boolean_is_not_count(self):
        with self.assertRaises(TypeError):
            failed_ratio(True, 1)
```

**Arrange:** choose input and expected result. **Act:** call the code. **Assert:** verify the property. Name tests by behavior (e.g. `rejects_boolean_count`), not by function alone.

## 3. Boundary value analysis

For a port parameter accepted in [1, 65535], test -1, 0, 1, 2, 65534, 65535, 65536, a string, a float, a bool, NaN if numerical coercion is supported, an enormous integer, `None` and negative zero textual forms if parsing strings.

Why? Most bugs appear at boundaries: inclusive vs exclusive thresholds, empty input, 1-byte truncation, overflow into native code or an implicit zero value.

## 4. Property-based thinking

A property is an invariant that should hold for many inputs. Examples:
- A normalized valid IP remains parseable.
- `decode(encode(text)) == text` for valid Unicode and chosen encoding.
- Adding a benign event cannot reduce a count of failures.
- A parser either returns a valid structured object or raises a documented exception.
- A file hash is stable when the file is unchanged (under the same algorithm and bytes).

```python
import random
rng = random.Random(2026)  # reproducible test data, NEVER for credentials

for _ in range(200):
    failures = rng.randint(0, 100)
    total = rng.randint(max(1, failures), 100)
    ratio = failed_ratio(failures, total)
    assert 0 <= ratio <= 1
```

For sophisticated generation/shrinking, [Hypothesis](https://hypothesis.readthedocs.io/) is worth learning. In tests, deterministic seeds aid reproduction; production secrets require `secrets`, not `random`.

## 5. Fuzzing and resource safety

Fuzzing sends many mutated inputs to a *local parser you control*. Establish CPU and memory budgets and capture crashes, unexpected exceptions, pathological runtime and wrong acceptance decisions. Do not direct an unlimited fuzzer at public services. Malformed data need not contain "exploit text" to reveal bugs; length, nesting and type confusion are enough.

### Test a binary frame
Use [Deep Dive 04](04-BYTES-ENCODING-BINARY-PARSERS.md)'s toy frame parser. Assert:
1. All frames shorter than six bytes fail.
2. Magic mismatch fails.
3. Version mismatch fails.
4. Declared length >1024 fails.
5. Truncated and extra bytes fail.
6. Non-UTF-8 or invalid JSON fails.
7. Exactly one well-formed frame succeeds.

## 6. Mocking: replace external effects, not security policy

Use `unittest.mock` or explicit in-memory fakes to replace filesystem operations, API clients and time. Do not mock the *function under test* and then call that a unit test. A fake network client proves your code calls a certain method, but it does not prove that real certificates are verified or that a cloud SDK handles pagination correctly.

```python
from unittest.mock import Mock

client = Mock()
client.fetch_events.return_value = [{"action": "login_failure"}]
assert client.fetch_events() == [{"action": "login_failure"}]
client.fetch_events.assert_called_once()
```

## 7. CI pipelines as an attack surface

GitHub Actions / other CI workers can access repository tokens, caches, secrets and deployment identities. Treat workflows as privileged code.

- Restrict `permissions: contents: read` unless more is required.
- Do not expose production secrets to untrusted PRs.
- Review workflow changes and third-party action provenance.
- Prefer pinned action SHAs for higher-assurance workflows.
- Keep build/deploy identities separate from read-only test identities.
- Audit artifact storage, logs and retention.
- Prevent poisoned caches from crossing trust boundaries.
- Run tests before publishing packages or deploying changes.

Example minimalist (illustrative):
```yaml
name: offline-checks
on: [push, pull_request]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python -m unittest discover -s tests -v
```

For production, evaluate SHA pinning, branch policies and runner trust. A workflow example does not itself guarantee secure deployment.

## 8. Software supply-chain security

Installing a Python dependency introduces code you did not write. Threats include typosquatting, malicious maintainers/build backends, dependency confusion, compromised releases and vulnerable transitive packages. A Python `venv` isolates package versions but **is not an execution sandbox**.

### Practical workflow
1. Start with standard library if possible.
2. Inspect package source/release channel, provenance and maintenance.
3. Use explicit version constraints/lockfiles; for reproducibility, use hashes when supported.
4. Generate a dependency inventory/SBOM for larger projects.
5. Audit vulnerability advisories with tools such as `pip-audit` and review findings.
6. Test upgrades in CI and deploy staged.
7. Keep an inventory of affected production deployments and patch ownership.
8. Document rollback and emergency compromise response.

**Caveat:** no reported known vulnerability does not imply a package is safe; scanners only know disclosed issues and their advisory databases.

## 9. Case study — a passing test that still misses a bug

A function returns empty alerts if parsing fails:
```python
# BAD
def scan_events(path):
    try:
        return parse_all(path)
    except Exception:
        return []
```

A naive test asserting "the result is a list" passes. But a corrupted log produces "zero alerts" — a dangerous false negative. Better design: raise a parse failure, record the source and do not misreport a complete scan.

Test cases must assert **correct rejection**, not merely that no crash occurred.

## 10. Exercises and answer keys

**A:** Write at least 12 tests for `failed_ratio`, including types and boundaries. Expected: wrong types throw `TypeError`, invalid ranges throw `ValueError`.

**B:** Add a malformed JSON fixture; assert your CLI returns non-zero and does not announce "0 threats". Expected: failure visible to operator.

**C:** Write a short CI threat model: attacker-controlled PR edits, secrets, build artifacts, workflow privileges. Map three controls to three concrete threats.

**D:** Create a dependency review for an imaginary `security-utils==1.0.0` package. What evidence would you need before trusting it? Avoid relying solely on popularity.

**E:** Design an end-to-end offline test for the log detector including malformed input, duplicates and time skew. Explain what it cannot establish about a live SOC.

**References:** [unittest](https://docs.python.org/3/library/unittest.html), [Python packaging](https://packaging.python.org/), [pip-audit](https://github.com/pypa/pip-audit), [GitHub Actions security](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions).
