# Lab 21 — Anomaly evaluation and base-rate effects

**Companion:** [Deep Dive Chapter 21](../course/21-STATISTICS-ANOMALY-DETECTION-ML.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

A detector claims 90% recall and 5% false-positive rate on a very low-prevalence class; management wants to know the analyst burden.

**Learning goal:** Compute confusion-matrix metrics and show why a rare event can produce mostly false alerts.

**Input assumptions:** TP=90 FP=4995 FN=10 TN=94905. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_21.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
from examples.chapter_cases import detection_metrics

measures = detection_metrics(90, 4995, 10, 94905)
assert measures["recall"] == 0.90
assert measures["false_positive_rate"] == 0.05
assert round(measures["precision"] * 100, 2) == 1.77

labels = [1]*100 + [0]*99_900
assert len(labels) == 100_000
print("PASS: precision only 1.77 percent at low base rate")
```

**Expected terminal result:** `PASS: precision only 1.77 percent at low base rate`.

## Explain the code, not merely the output

1. A low prevalence means benign events vastly outnumber suspicious ones.
2. At 5% FPR, false alerts from 99,900 benign sessions dominate the 90 true alerts.
3. Precision and recall must be evaluated on representative labeled data and with clear denominator conventions.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Set TP=FP=0 and verify precision is undefined (None), not 100%.
2. Compare a trivial always-benign classifier for 1% prevalence.
3. Describe time-series train/test leakage and why it inflates reported performance.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

90/(90+4995)=0.017699..., or about 1.77% precision. Operational alert load cannot be inferred from recall alone.

**Threat model / safety consideration:** An anomaly score is not a confirmed threat and must not be the sole trigger for automatic account disabling.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_21.py`, a tests file, and `report_21.md` with exact commands, outcomes and limitations.
