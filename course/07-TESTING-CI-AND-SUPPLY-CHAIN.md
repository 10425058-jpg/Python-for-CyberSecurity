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


## 11. Advanced testing lab: prove *failure behavior*, not just happy paths

Suppose a parser processes an incident dataset and emits findings incrementally. It encounters invalid JSON after writing its first alert. What is the contract? Does a report contain partially valid rows? Does a CLI return a successful exit code? Does a human reviewing the output think the scan was complete?

For a safety-oriented educational pipeline, **stage the report and commit it only after complete successful parsing**. This is a stronger guarantee than merely asserting a function returns the right number of alerts.

### Test an invariant rather than implementation details

```python
import tempfile
import unittest
from pathlib import Path
from examples.mini_soc_pipeline import write_findings_atomic

GOOD = b'{"timestamp":"2026-01-01T00:00:00Z",' \
       b'"actor":"a","action":"login_failure"}\n'
BAD = b'not-json\n'

class AtomicityTest(unittest.TestCase):
    def test_bad_source_does_not_replace_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            report = Path(directory) / "report.jsonl"
            report.write_text("previous complete report\n", encoding="utf-8")
            source.write_bytes(GOOD + GOOD + GOOD + BAD)
            with self.assertRaises(ValueError):
                write_findings_atomic(source, report, threshold=3)
            self.assertEqual(
                report.read_text(encoding="utf-8"),
                "previous complete report\n",
            )
```

**What it proves:** a known malformed input prevents replacement of the existing report in this scenario. **What it does not prove:** crash durability under power loss, resistance to malicious filesystem races, correct triage decisions on real data, or absence of other bugs.

## 12. Threat-model the CI pipeline itself

| Threat | Risk | Example mitigation | Verification |
|---|---|---|---|
| PR modifies workflow | job gains secrets | minimal token scopes, protected environments | inspect workflow diff |
| Third-party action compromised | malicious code on runner | pin reviewed action commit SHA; monitor advisories | provenance review |
| Dependency typosquatting | install executes untrusted code | audited locked requirements, trusted index | dependency review |
| Cache poisoning | malicious artifact reused | restrict cache sharing, isolate trust levels | CI configuration test |
| Credentials printed in failure | token disclosure | protected secret flow, redacted logging | safe log test |
| CI cannot access network | tests break for wrong reasons | offline deterministic unit tests | run without network |

Tests should not require connecting to production services. For deployment integrations, use limited scoped test accounts and explicit permissions.

### Verification commands

```bash
python -m unittest discover -s tests -v
python -m compileall -q examples tests
python -m examples.strict_frame
```

Optional maintained tools include `ruff`, `mypy`, `pip-audit` and `bandit`. Each has limitations; do not equate "no findings" with "secure."

## 13. Mutation testing as a thought experiment

Take a threshold rule `if count >= 3`. Change it intentionally to `if count > 3`. If all tests still pass, your tests missed an **inclusive-boundary requirement**. Good tests target invariants:
- Exactly 2 failures: no alert.
- Exactly 3: alert.
- A fourth within window: behavior according to suppression policy.
- Third exactly 300 seconds from first: include if policy is inclusive.
- A failure at 301 seconds: first event expires.
- Duplicates: count according to explicit ID policy.
- Corruption after valid rows: fail visibly and avoid false "all clear."

## 14. Exercise ladder with answer checks

**A:** Write a test for `parse_event` rejecting duplicate JSON keys. A reliable parser should not silently choose a value.

**B:** Introduce a wrong timestamp offset and demonstrate how an apparently passing test could produce the wrong incident order.

**C:** Mock a `datetime.now` dependency by injecting a clock function; do not patch global system time.

**D:** Define two integration tests for SQLite write transactions and rollback after an invalid record.

**E:** Design a regression test for a bug discovered in production. Describe how sanitized synthetic fixtures avoid exposing private user data.

**Evaluation rubric:** each test should state the invariant, data conditions, expected error/return type and why it matters for security. Maintain a small "known limitations" section for properties that tests do not establish.
