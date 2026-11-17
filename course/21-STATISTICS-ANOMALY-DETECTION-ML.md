# Deep Dive 21 — Statistics, anomaly detection and machine-learning pitfalls in cybersecurity

> **Hands-on:** [Chapter 21 Guided Lab](../lab-manual/21-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Test realistic error conditions before proceeding.

**Level:** intermediate → advanced · **Estimated study:** 12–18 hours.

## Goal
Understand what a Python anomaly detector can and cannot prove. You will create a baseline from toy activity counts, compute standardized deviations, and evaluate predictions with a confusion matrix. The core lesson: a statistically unusual event is not automatically malicious.

## 1. Base rates are decisive

Suppose only 1 in 1,000 authentication sessions are truly malicious. A detector with 90% recall and a 5% false-positive rate sounds good, but among 1,000 sessions:
- Expected true positives: 0.9.
- Expected false positives: 0.05 × 999 = 49.95.
- Most alerts are still false positives.

This is the **base-rate fallacy**. A high recall alone does not ensure that alerts are operationally useful. Estimate prevalence, cost of false positives and consequence of misses.

## 2. Descriptive statistics

For observations `x_1, ..., x_n`:
\[
\bar{x}=\frac{1}{n}\sum_i x_i
\]
Population standard deviation:
\[
\sigma=\sqrt{\frac{1}{n}\sum_i(x_i-\bar{x})^2}
\]
Sample standard deviation uses denominator `n-1` and requires n>=2.

```python
from statistics import mean, pstdev

hourly_events = [10, 12, 11, 13, 12, 10, 60]  # intentionally toy data
baseline = hourly_events[:-1]
mu = mean(baseline)
sigma = pstdev(baseline)
z = (hourly_events[-1] - mu) / sigma if sigma > 0 else float("inf")
print(round(mu, 2), round(sigma, 2), round(z, 2))
```

This code is only a pedagogical anomaly-score illustration. A z-score assumes something about the distribution and comparability of measurements. Counts can be bursty, skewed, seasonal or strongly autocorrelated, making a naive z-score misleading.

### Median and robust measures
Outliers can raise the mean and standard deviation. For skewed populations, median and median absolute deviation (MAD) can be more robust, but need careful handling of zero MAD and discrete count distributions.

## 3. Time-of-day and seasonal baselines

A service might have normal 9 AM spikes and 3 AM quiet periods. Comparing a 9 AM peak against a 24-hour average generates false alerts. Separate relevant contexts (weekday/weekend, workload release windows, service, user behavior) while avoiding overfitting.

A baseline must be built from a credible, representative period. Poisoned or compromised baselines can normalize malicious activity and lead to false negatives.

## 4. Evaluation metrics

Let TP = correct positive, FP = incorrect positive, FN = missed positive, TN = correct negative.

\[
\mathrm{Precision}=\frac{TP}{TP+FP}
\]
\[
\mathrm{Recall}=\frac{TP}{TP+FN}
\]
\[
\mathrm{F1}=\frac{2TP}{2TP+FP+FN}
\]

```python
def scores(tp: int, fp: int, fn: int, tn: int) -> dict:
    values = (tp, fp, fn, tn)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("confusion-matrix values must be nonnegative integers")
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}

assert scores(15, 5, 5, 95)["f1"] == 0.75
```

We choose zero as the empty-denominator convention for this exercise; real reporting should explicitly document when a metric is undefined instead of obscuring it with a fabricated percentage.

## 5. Training/test leakage and time-series splits

Security events often have time-based correlations. Randomly splitting near-identical events across training and test sets lets a model "memorize" duplicated context, overstating generalization. Prefer time-based validation where appropriate and ensure data from the same campaign/entity does not leak in ways that violate the intended deployment scenario.

Labels in security are frequently imperfect. An analyst calling an event "benign" may simply not have found evidence of compromise. Record how labels were obtained and quality-reviewed.

## 6. Supervised versus unsupervised methods

- **Supervised classification:** train on labeled benign/malicious examples. Requires representative ground truth and good generalization.
- **Unsupervised anomaly detection:** identify statistical deviations without explicit attack labels. Outputs are anomaly scores, not threat proof.
- **Rules + ML hybrid:** use interpretable rules as a baseline, then ML to rank or enrich alerts, with careful evaluation.

Algorithms to understand conceptually: logistic regression, decision trees, random forests, gradient boosting, Isolation Forest, clustering and sequence models. Use established libraries (e.g. scikit-learn), not improvised security-critical math when better-vetted implementations exist.

## 7. Feature engineering and privacy

Potential features: failure count over five minutes, first-seen device, login hour deviation, distance between claimed geolocations, endpoint process execution rates. Risks:
- Location claims may be wrong due to VPN/proxy and privacy settings.
- Identifiers may be personally identifying.
- Aggregation can hide events or imply false precision.
- Malicious activity can intentionally shape features.
- Model training data and inference logs need access controls/retention.

Design features with clear purpose and a way for an analyst to explain alerts.

## 8. Threshold choice and operations

A lower anomaly threshold generally increases the number of flagged events. You must measure:
- Precision/recall, especially on rare events.
- Alerts per analyst per day and expected triage time.
- Confidence calibration and drift.
- False positive reasons by population.
- Explainability for high-impact conclusions.
- Latency, model failure and fallback behavior.

No automated model should disable user accounts solely because an uncalibrated score is unusual.

## 9. Lab — toy detection evaluation

1. Construct 20 labeled toy scenarios: 5 suspicious, 15 benign.
2. Make a rule `count >= 5` for a synthetic feature.
3. Count TP/FP/FN/TN by hand.
4. Compute metrics using `scores`.
5. Change threshold to 3, then 7, and compare precision/recall.
6. Identify which false positives were caused by ordinary high-volume users.
7. Explain why the toy distribution does not estimate real SOC performance.

**Answer check:** a higher threshold often reduces alerts and may reduce false positives at the cost of more false negatives; it is not universally true for all finite datasets.

## 10. Questions
- What is the difference between "unusual" and "malicious"?
- Why does a 5% false-positive rate create alert fatigue under a very low base rate?
- What can time-based split prevent?
- Why can an attacker poison a baseline?
- Why is a metric undefined when its denominator is zero, and what should an operational report say?
- Which features carry privacy risk?

**References:** [Python statistics](https://docs.python.org/3/library/statistics.html), [scikit-learn user guide](https://scikit-learn.org/stable/user_guide.html), [MITRE ATT&CK](https://attack.mitre.org/).


## 11. A realistic security-statistics example: the base-rate problem

Imagine an identity service processes 100,000 sessions. Your validated reference labels mark **100 malicious sessions** and **99,900 benign sessions**. A detector correctly catches 90 malicious sessions (90% recall) but falsely flags 5% of benign sessions.

Expected confusion-matrix counts:
- TP = 90.
- FN = 10.
- FP = 4,995.
- TN = 94,905.

Precision = `90 / (90 + 4995) ≈ 1.77%`. Despite 90% recall, about **98.23%** of alerts are false positives in this hypothetical scenario. Low base rates matter much more than intuition suggests.

### Calculate the numbers with reproducible Python

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Confusion:
    tp: int
    fp: int
    fn: int
    tn: int

def evaluate(m: Confusion):
    counts = (m.tp, m.fp, m.fn, m.tn)
    if any(type(v) is not int or v < 0 for v in counts):
        raise ValueError("counts must be nonnegative integers")
    precision = m.tp / (m.tp + m.fp) if m.tp + m.fp else None
    recall = m.tp / (m.tp + m.fn) if m.tp + m.fn else None
    false_positive_rate = (
        m.fp / (m.fp + m.tn) if m.fp + m.tn else None
    )
    f1 = (
        2 * m.tp / (2 * m.tp + m.fp + m.fn)
        if 2 * m.tp + m.fp + m.fn else None
    )
    return {
        "precision": precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "f1": f1,
    }

results = evaluate(Confusion(tp=90, fp=4995, fn=10, tn=94905))
assert round(results["precision"], 4) == 0.0177
assert results["recall"] == 0.9
assert results["false_positive_rate"] == 0.05
```

**Why report undefined values?** If no positive predictions exist, precision has denominator zero; setting it to 100% would be misleading. An API may return `None` with explanatory metadata or use a published convention, but the decision must be explicit.

## 12. Build and critique an anomaly baseline

A Python prototype compares an hourly event count with the last six normal hours. The toy baseline is `[10,12,11,13,12,10]`, and the next value is `60`.

```python
from statistics import mean, pstdev
history = [10, 12, 11, 13, 12, 10]
observed = 60
mu, sd = mean(history), pstdev(history)
z = (observed - mu) / sd if sd else None
print("baseline mean:", mu)
print("baseline population stdev:", sd)
print("z score:", z)
```

This is a statistical **deviation** (a large z-score), not evidence of malicious behavior. A release, backup, monitoring change, traffic surge or faulty instrumentation could cause the same observation. Counts may be seasonal, non-Gaussian and correlated; a simple normal-distribution model is inappropriate without testing assumptions.

### Five common forms of leakage or bias

1. **Temporal leakage:** future events influence the training baseline for a past prediction.
2. **Identity leakage:** the same host/account appears in both train/test with nearly identical events.
3. **Label leakage:** a post-incident classification field leaks the answer into a training feature.
4. **Selection bias:** analysts label only previously alerted events, leaving silent misses unmeasured.
5. **Baseline poisoning:** an adversary slowly changes background behavior to appear normal.

A time-ordered evaluation is often more appropriate than a random split when you're forecasting future activity. The correct split depends on deployment and research question.

## 13. Operational evaluation beyond precision and recall

A security model must be evaluated along several dimensions:

| Dimension | Example measure | Why it matters |
|---|---|---|
| Detection quality | precision, recall, PR curve | true versus false signal |
| Alert workload | alerts per 1000 events, analyst time | team capacity |
| Latency | p50/p95 event-to-alert delay | timely response |
| Robustness | performance under missing fields | resilience to sensor errors |
| Drift | feature/label changes by month | aging model |
| Privacy | source data and retention policy | least exposure |
| Explainability | traceable evidence and rule/model version | human review |
| Fairness / coverage | error rates across legitimate populations | avoid systematic misses |
| Resource cost | peak RSS, CPU, API cost | operational feasibility |

**Never** use an uncalibrated anomaly score as sole justification to disable an account. Use human-approved response procedures and independent corroboration.

## 14. Exercises with worked expectations

**A:** With TP=45, FP=5, FN=15, TN=935, calculate precision=0.90, recall=0.75, false-positive rate≈0.00532. Explain why the false-positive rate alone may hide alert volume.

**B:** Increase a synthetic detection threshold and record changes in TP/FP/FN/TN. Describe a real tradeoff, not "higher is always better."

**C:** Generate a dataset with 1% positive labels. Explain why accuracy can be high for a trivial "always benign" classifier while recall is zero.

**D:** Design a time-series split for a monthly stream. Include a gap or entity-level grouping if adjacent windows leak information.

**E:** Write a report that separates anomaly score, model confidence/calibration and confirmed incident status. These are different constructs.

**F:** State what additional evidence would justify escalating an unusually high number of login failures. Examples: successful privileged access after attempts, MFA changes, device identity and validated source provenance.

**References:** [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html), [Python statistics](https://docs.python.org/3/library/statistics.html).
