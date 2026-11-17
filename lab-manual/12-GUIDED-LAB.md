# Lab 12 — SOC detection thresholds and measured false positives

[Read Chapter 12](../course/12-SOC-DETECTION-ENGINEERING.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A detector flags repeated failed logins, but most alerts may be benign. The analyst needs reproducible evidence and a confusion matrix.

**Measurable goal:** Calculate precision/recall from labeled synthetic data and review a burst rule without auto-remediation.

**Input contract:** TP=8, FP=9, FN=2, TN=81. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_12.py` and copy the next complete snippet into it. Run it with `python lab_12.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from examples.chapter_cases import detection_metrics
from examples.mini_soc_pipeline import parse_event, detect_bursts

def item(t, uid):
    raw = ('{"source":"lab","event_id":"%s",'
           '"timestamp":"2026-01-01T10:%02d:00Z",'
           '"actor":"alex","action":"login_failure"}' % (uid,t))
    return parse_event(raw.encode(), line_number=t+1, default_source="lab")

alerts = list(detect_bursts(iter([item(0,"a"), item(1,"b"), item(2,"c")])))
assert len(alerts) == 1
metrics = detection_metrics(8, 9, 2, 81)
assert round(metrics["precision"], 3) == 0.471
assert metrics["recall"] == 0.8
print("PASS: review alert with measured performance")
```

**Expected result:** `PASS: review alert with measured performance`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. Event-time UTC sequence is sorted; the three unique IDs reach the threshold.
2. An alert is a review candidate, not evidence of a hostile actor.
3. Precision answers what fraction of alerts are true, recall what fraction of true cases are found.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Replay an identical source+event ID; dedup should prevent double-counting.
2. Make an event arrive out of time order: pipeline rejects.
3. Compute metrics when TP+FP=0; undefined precision should not be silently called 100%.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

For 8 TP and 9 FP, precision = 8/17; recall = 8/10. Low prevalence can overwhelm an analyst with benign alerts.

**Security analysis:** Never automatically lock out accounts from one weak rule; an attacker could trigger denial of service against real users.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
