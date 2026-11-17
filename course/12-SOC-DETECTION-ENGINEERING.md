# Deep Dive 12 — Build a Python SOC detection pipeline with evidence and measurable quality

> **Hands-on:** [Chapter 12 Guided Lab](../lab-manual/12-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

**Level:** intermediate → advanced · **Estimated study:** 15–22 hours.

## Mission: detect suspicious bursts of failed logins

A Security Operations Center (SOC) transforms telemetry into *reviewable hypotheses*. A rule saying "three login failures occurred in five minutes" is not proof of an attacker. Real users mistype passwords, mobile devices retry automatically, and logs may arrive late.

Build a controlled, testable pipeline with:
- Explicit event schema and source provenance.
- Event-time windows.
- Bounded memory.
- Normalization and deduplication.
- Clear alert suppression policy.
- False-positive and coverage evaluation.
- Analyst triage and response workflow.

## Masterclass — the base-rate trap in SOC alert quality

A SOC rule may detect 90% of true incidents yet waste most analyst time on benign events. The reason is **prevalence**: when true incidents are rare, even a small false-positive rate applies to a very large benign population. You must report recall, false-positive rate and **precision** together.

**Illustrative population:** 100,000 labeled toy sessions: 100 positive and 99,900 benign. Suppose the detector catches 90 positive sessions and wrongly flags 5% of benign sessions.

| Classification | True positive | False positive | False negative | True negative |
|---|---:|---:|---:|---:|
| Count | 90 | 4,995 | 10 | 94,905 |

**Compute rather than guess:**

```python
# MASTERCLASS_RUNNABLE
from dataclasses import dataclass

@dataclass(frozen=True)
class Matrix:
    tp: int
    fp: int
    fn: int
    tn: int

def evaluate(m: Matrix) -> dict[str, float | None]:
    values = (m.tp, m.fp, m.fn, m.tn)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("counts must be nonnegative integers")
    return {
        "precision": m.tp / (m.tp + m.fp) if m.tp + m.fp else None,
        "recall": m.tp / (m.tp + m.fn) if m.tp + m.fn else None,
        "fpr": m.fp / (m.fp + m.tn) if m.fp + m.tn else None,
    }

result = evaluate(Matrix(tp=90, fp=4995, fn=10, tn=94905))
assert round(result["precision"] * 100, 2) == 1.77
assert result["recall"] == 0.90
assert result["fpr"] == 0.05

empty = evaluate(Matrix(tp=0, fp=0, fn=0, tn=100))
assert empty["precision"] is None and empty["recall"] is None
```

**Interpretation:** 5,085 alerts arise from the toy evaluation, but only 90 are labeled true positives. Precision is approximately **1.77%**. A model with high recall can therefore be unusable if its alert burden exceeds analyst capacity. The exact rates depend on sampling and ground truth; synthetic results do not forecast performance on a live enterprise network.

**Evidence quality before metrics:** if a logging source fails, the denominator may be incomplete. If event time is out of order, threshold correlation may be wrong. If labels are assigned only to already-alerted incidents, you cannot measure false negatives reliably. Metrics need dataset coverage, labeling method, clear definition of a *case* and traceable rule/model versions.

**Security operations exercise:** estimate analyst time assuming each alert takes 4 minutes of triage. Compute 5,085 × 4 = 20,340 analyst minutes (~339 hours), *for this toy population*. Suggest a safe workflow to improve precision (contextual corroboration, multi-signal detections, tuning) without suppressing all rare incidents. Why is "automatically disable all flagged accounts" dangerous? Because attackers may exploit weak rules to deny service to legitimate users.


## 1. Data sources and blind spots

| Source | Possible signal | Limits |
|---|---|---|
| App auth log | success/failure, username | may omit proxy IP or be forged |
| Identity provider | MFA outcomes, suspicious sign-ins | coverage only for integrated apps |
| OS event log | local logons, process events | limited retention/privilege |
| VPN/proxy | remote source and traffic | NAT/shared-IP ambiguity |
| DNS | queries and resolutions | encrypted DNS and cache effects |
| EDR | process, file, network detections | sensor blind spots and false positives |

Before writing a rule, confirm which fields exist and how reliable they are. Define retention, legal/privacy basis, and allowed access. Treat attacker-controlled fields as untrusted data.

## 2. Schema for normalized events

```json
{
  "event_id": "toy-001",
  "source": "lab-auth",
  "timestamp": "2026-01-01T10:00:00Z",
  "actor": "alice",
  "action": "login_failure",
  "src_ip": "192.0.2.10",
  "outcome": "failure"
}
```

**Important distinctions:**
- `event_time`: when the source claims the event happened.
- `ingest_time`: when your pipeline received it.
- `source`: where the record came from.
- `event_id`: source-specific stable identity, if available.
- `actor`: a principal (might change case or identity across systems).
- `src_ip`: network clue, not reliable person identity (NAT/proxies/VPN).
- `original_reference`: pointer or digest for re-checking the original evidence.

Normalize UTC timestamps, but retain original strings. Validate field lengths and types. Do not convert usernames to lowercase without checking provider identity semantics.

## 3. Rule hypothesis

> If one validated actor has at least three failed logins in a rolling 300-second event-time window, emit a **review** alert when the threshold is crossed.

This says nothing about the actor being compromised. A lower threshold increases sensitivity and false positives; a higher one may miss slow attempts. Choose values using evidence and documented operational risk.

## 4. Sliding-window logic

For each actor, keep a deque of failure timestamps. On a new failure at time t:
1. Remove timestamps older than t-300 seconds.
2. Append t.
3. If the deque length reaches threshold (and the rule isn't in a suppression state), emit an alert.
4. Attach the actor, event-time range, count, source, and evidence references.

```python
from collections import defaultdict, deque
from datetime import timedelta

def rolling_threshold(events, threshold=3, window_seconds=300):
    window = timedelta(seconds=window_seconds)
    queues = defaultdict(deque)
    for timestamp, actor, action in events:
        if action != "login_failure":
            continue
        q = queues[actor]
        while q and timestamp - q[0] > window:
            q.popleft()
        q.append(timestamp)
        if len(q) == threshold:
            yield actor, timestamp, len(q)
```

This snippet assumes **already validated and globally event-time-sorted events**. It omits deduplication, suppression rearm logic and actor count caps for clarity. Study [the runnable detector](../examples/log_detector.py) for a more complete initial example.

## 5. Work a trace manually

| Time | Actor | Action | Alice's queue after processing | Alert? |
|---|---|---|---|---|
| 10:00 | Alice | failure | [10:00] | no |
| 10:01 | Alice | failure | [10:00,10:01] | no |
| 10:03 | Bob | success | unchanged | no |
| 10:04 | Alice | failure | [10:00,10:01,10:04] | yes |
| 10:10 | Alice | failure | [10:10] | no |
| 10:11 | Alice | failure | [10:10,10:11] | no |
| 10:12 | Alice | failure | [10:10,10:11,10:12] | yes |

A rule firing once when a threshold is crossed needs a **state-reset policy**. If the queue falls below threshold after expiry, it may rearm; if the queue stays above threshold indefinitely, choose whether to suppress repeated notifications for a cooldown period. A suppression policy impacts alert volumes and must be tested.

## 6. Out-of-order events and watermarks

In real systems, a source may deliver an event five minutes late. If a detector assumes timestamps never go backwards, it can miscount or produce false alerts. Options:
- Reject out-of-order data and report ingest quality (simple controlled pipelines).
- Buffer within a configured lateness window, sort before processing (memory/latency tradeoff).
- Use stream-processing watermark semantics to close windows (advanced).
- Recompute historical windows when late events arrive, with explicit correction semantics.

No universal solution exists; the desired behavior depends on business need and data reliability. Do not silently reorder only some sources.

## 7. Deduplication

Duplicates arise from collector retries and multiple forwarding agents. A stable event ID (including source namespace) can support deduplication. If no ID exists, a tuple of fields may be used as a heuristic but can incorrectly collapse distinct real events. Track both raw count and deduplicated count.

**Avoid:** using `hash(tuple(record.values()))` as a long-lived evidence ID. Python's hash is not stable across interpreter runs; mapping order may vary; collisions are possible. If you need a durable content digest, canonicalize a defined set of fields and use SHA-256 with clear provenance.

## 8. Evaluate detection quality

Construct a labeled *synthetic* dataset with:
- 100 benign test cases.
- 20 intentionally suspicious cases as defined by a controlled scenario.
- Known ground-truth labels.

Confusion matrix:
- TP: suspicious and flagged.
- FP: benign but flagged.
- TN: benign and not flagged.
- FN: suspicious but missed.

Metrics:
\[
\mathrm{Precision}=\frac{TP}{TP+FP},\qquad
\mathrm{Recall}=\frac{TP}{TP+FN}
\]
\[
\mathrm{F1}=\frac{2\,\mathrm{Precision}\,\mathrm{Recall}}
{\mathrm{Precision}+\mathrm{Recall}}
\]

Suppose TP=15, FP=5, FN=5, TN=95. Precision = 15/20 = **0.75**, recall = 15/20 = **0.75**, F1 = **0.75**. Specificity is 95/100 = **0.95**. Report denominators and data sampling; never announce accuracy on artificially imbalanced test data without context.

For no predicted positives or no actual positives, document a clear zero-denominator convention rather than accidentally dividing by zero.

## 9. Operational logging and privacy

An alert should carry enough context for investigation but avoid raw passwords, access tokens, cookies, and excessive personally identifying data. Store source pointers and protected evidence separately. Constrain alert payloads and retention. Track false positive reasons; do not blacklist an IP automatically based on one weak signal.

## 10. Triage runbook (defensive, human-approved)
1. **Validate:** check log integrity, clocks, source coverage and parsing errors.
2. **Contextualize:** compare known device/IP, user behavior and operational activity.
3. **Correlate:** look for successful login after failures, MFA changes, impossible travel assumptions, device changes.
4. **Estimate impact:** affected account/data/scope, confidence and alternatives.
5. **Escalate:** notify authorized responder according to severity.
6. **Contain/recover:** require policy approval for account disable or session revocation; record actions and rollback.
7. **Improve detection:** record benign causes and update tests/thresholds.
NIST SP 800-61 Rev. 3 integrates incident response with broader cybersecurity risk management; use the latest organization-approved playbook.

## 11. Hands-on lab: build and evaluate a detector

**Input:** `fixtures/synthetic-auth.jsonl` and your generated labeled dataset.

```bash
python -m examples.log_detector fixtures/synthetic-auth.jsonl --threshold 3 --window-seconds 300
python -m unittest discover -s tests -v
```

Expected: synthetic Alice generates review alerts at threshold crossings based on timestamps and rule state; behavior differs with threshold. Confirm exact outputs by reading the source and testing fixture. A result is a review candidate, not a diagnosis.

### Extend the lab
- Add event IDs and explicit source namespaces.
- Deduplicate a replayed event.
- Introduce a late event and choose error/reorder handling.
- Add a per-actor memory cap and resource limit.
- Add a JSON report with false-positive examples and a timeline.
- Calculate precision/recall on a labeled dataset.

## 12. Practice and answer checks
**A:** Which is preferable for actor identification: IP or identity-provider subject? *Subject is generally more stable for identity; IP is supporting context and may be shared.*

**B:** Why is a five-minute window ambiguous without specifying inclusion, event-time vs ingest-time and late-data policy? *Each choice changes which events are counted.*

**C:** What does a TP/FP/FN/TN matrix tell you that raw alert count does not? *Detection effectiveness relative to labeled ground truth.*

**D:** Name three false positive sources for failed-login bursts. *Forgotten stored password, automated health checks, legitimate shared device/password rotations, or test activity.*

**E:** Design a test showing one actor with 10,000 unique aliases can exhaust in-memory state. Propose a bounded mitigation and its possible false-negative effect.

**References:** [Sigma rule documentation](https://sigmahq.io/), [MITRE ATT&CK](https://attack.mitre.org/), [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), [NIST SP 800-61r3](https://csrc.nist.gov/pubs/sp/800/61/r3/final).


## 13. End-to-end incident simulation: from event ingestion to a review alert

A SOC rule is not just a `Counter`. It is an **operational hypothesis** with data source assumptions, time semantics, suppress/rearm policy, evidence references and measured false positives.

### Define the rule in plain English first

> For each validated account identity, when three unique failures occur in an inclusive rolling 300-second event-time window, emit one review candidate and suppress repeated alerts until the active failure count drops below three.

Before coding, answer:
- Is identity case sensitive?
- What is the stable event ID and source namespace?
- How are delayed or out-of-order records handled?
- Do successes clear the failure window? (Not in this definition.)
- When does suppression rearm?
- What limits event size, actor cardinality and stored event IDs?
- What does "complete" mean if input parsing fails?

### Trace deliberately adversarial toy input

| Time (UTC) | ID | Actor | Action | Unique failures in 300 s | Output |
|---|---|---|---|---|---|
| 10:00 | A | alice | failure | 1 | none |
| 10:01 | B | alice | failure | 2 | none |
| 10:01 | B | alice | failure replay | still 2 | none |
| 10:02 | C | alice | failure | 3 | review |
| 10:03 | D | alice | success | still 3 | none |
| 10:10 | E | alice | failure | 1 | none; rearm |
| 10:11 | F | alice | failure | 2 | none |
| 10:12 | G | alice | failure | 3 | new review |

A basic dedup key is `(source,event_id)`, not just `event_id`. It is still a trust assumption: the source may be buggy or compromised. An actor may be an identity-provider subject rather than a displayed username.

### Run the tested local example

```bash
python -m examples.mini_soc_pipeline \
  --input fixtures/synthetic-auth.jsonl \
  --output findings.jsonl \
  --threshold 3 \
  --window-seconds 300
python -m unittest tests.test_deep_examples.MiniSocTests -v
```

On Windows PowerShell use one line and an appropriate local output path. The tool is designed for **offline synthetic data**, not active scanning or production identity control.

**Warning:** a confidence label of "rule-only" is not a probability that the account is compromised. Treat it as a transparent status explaining the finding came from a rule without corroboration.

## 14. Quantitative effectiveness, with real denominators

For 100 labeled synthetic cases, suppose 10 are suspicious and 90 benign. The detector catches 8 suspicious, misses 2, and flags 9 benign:
- TP = 8
- FN = 2
- FP = 9
- TN = 81
- Precision = 8/(8+9) ≈ **0.471**
- Recall = 8/(8+2) = **0.80**
- False positive rate = 9/(9+81) = **0.10**
- F1 = 16/(16+9+2) ≈ **0.593**

A high recall coexists with mediocre alert usefulness. The **base rate** (how common true incidents are) matters; a detector can overwhelm analysts even with a modest false-positive rate when true incidents are rare.

```python
def metrics(tp: int, fp: int, fn: int, tn: int):
    if any(type(v) is not int or v < 0 for v in (tp, fp, fn, tn)):
        raise ValueError("counts must be nonnegative integers")
    precision = tp/(tp+fp) if tp+fp else None
    recall = tp/(tp+fn) if tp+fn else None
    f1 = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
    return precision, recall, f1

p, r, f1 = metrics(8, 9, 2, 81)
assert round(p, 3) == 0.471
assert r == 0.8
assert round(f1, 3) == 0.593
```

Document undefined denominators rather than inventing precision for a detector that never predicts positives.

## 15. Threat hunting and response quality

An alert should include:
- Rule ID and version.
- Actor and normalized event-time range.
- Supporting source-qualified event IDs.
- Evidence link or reference (protected access).
- Parser error count / input completeness status.
- Time uncertainty, confidence and threshold policy.
- Suggested **verification steps** before any containment.

Never automatically disable accounts based on a weak, uncorroborated rule. It could be weaponized to cause denial of service against legitimate users. OWASP emphasizes monitoring authentication failures while evaluating context and false positives. Refer to the [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

### Exercises
1. Add an explicit duplicate-ID policy to a toy source and test two duplicates.
2. Change time-window boundary from inclusive to exclusive. Predict which events change classification.
3. Create a labeled table and compute precision/recall by hand before coding.
4. Simulate parsing failure after an alert and verify the CLI does **not** claim a complete report.
5. Write a one-page triage runbook covering benign alternatives, corroboration, escalation and analyst sign-off.
6. Design an audit log that is useful while avoiding tokens, raw private data and unnecessary identifying details.

**Answer check:** an alert is a triage input, not evidence of guilt. Report error rates and coverage gaps alongside detection counts.
