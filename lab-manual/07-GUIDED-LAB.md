# Lab 07 — Unit tests, mutation thinking and CI verification

**Paired lesson:** [Chapter 07](../course/07-TESTING-CI-AND-SUPPLY-CHAIN.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** A novice changes an inclusive threshold from >= to >; only well-designed tests catch the regression.

**By the end:** Test both rejection behavior and correctness of positive boundaries.

**Input or assumptions:** Count thresholds: 2, 3, 4

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_07.py` **in a temporary working directory** and run `python lab_07.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
import unittest

def threshold_reached(count, threshold=3):
    if type(count) is not int or count < 0:
        raise ValueError("invalid count")
    return count >= threshold

class ThresholdTests(unittest.TestCase):
    def test_below(self):
        self.assertFalse(threshold_reached(2))
    def test_equal(self):
        self.assertTrue(threshold_reached(3))
    def test_above(self):
        self.assertTrue(threshold_reached(4))
    def test_invalid(self):
        for bad in (-1, True, 2.0):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                threshold_reached(bad)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(ThresholdTests)
result = unittest.TextTestRunner(verbosity=0).run(suite)
assert result.wasSuccessful()
print("PASS: threshold regression tests")
```

**Expected terminal signal:** `Ran 4 tests ... OK followed by PASS: threshold regression tests`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. A test of only count=4 would pass even with an incorrect > operator.
2. Count exactly equal to the threshold is the essential boundary case.
3. CI must run under least privilege without production tokens.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Change >= to > and verify test_equal fails.
2. Remove input type validation and verify True is rejected by a test.
3. Write an integration test that simulates a corrupt file after valid records.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

Property tests and boundary tests are complementary. A passing test suite demonstrates only the cases and invariants covered.

### Security review

Incorrect green status after malformed input is a dangerous security reporting failure.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
