# Deep Dive 18 — Full mini-SOC capstone blueprint, architecture and acceptance criteria

> **Hands-on:** [Chapter 18 Guided Lab](../lab-manual/18-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Test realistic error conditions before proceeding.

**Level:** advanced project · **Estimated build:** 6–12+ weeks at 10 hours/week, depending on prior experience.

## 0. Project objective

Build an offline **defensive** mini Security Operations Center pipeline that ingests synthetic JSONL events, validates schemas, normalizes timestamps, preserves provenance, correlates failed-login events over windows, emits explainable *review* alerts and measures quality against labeled data.

This is a portfolio-quality software engineering project, not a production SIEM, an EDR agent or an automatic account lockdown service.

## 1. Architecture

```text
synthetic JSONL files (immutable raw inputs)
        ↓
bounded byte reader + strict decoder
        ↓
schema validator (reject or quarantine + count)
        ↓
normalized immutable event models
        ↓
deduplication (source namespace + event ID)
        ↓
bounded event-time window and correlation
        ↓
explainable review findings
        ↓
SQLite state/report adapter + JSONL export
        ↓
analyst review runbook and evaluation report
```

Keep the "core" independent of databases and vendor APIs. Each stage has a typed contract and a failure policy.

## 2. Functional requirements

**FR-01** Ingest one or more synthetic JSONL files without loading the whole files in RAM.

**FR-02** Reject malformed UTF-8, malformed JSON, missing fields, unexpected types and oversized records, with exact source line numbers.

**FR-03** Retain original source reference and original timestamp alongside normalized aware UTC timestamp.

**FR-04** Support event ID deduplication under a documented namespace; record duplicate count.

**FR-05** Support a configurable rolling window with inclusive/exclusive boundary explicitly defined.

**FR-06** Distinguish threshold crossing from repeated notification; document suppression/rearm policy.

**FR-07** Limit memory used by active actors and per-actor queues; return visible incomplete status if caps are exceeded.

**FR-08** Produce alerts with rule ID, version, actor, time window, supporting event IDs and confidence label `review`.

**FR-09** Export valid JSONL/CSV with secrets redacted and external-field sanitation for spreadsheets.

**FR-10** Calculate TP/FP/FN/TN, precision and recall on a labeled synthetic dataset.

**FR-11** Provide an analyst report that describes evidence, false positives, limitations and next steps.

**FR-12** Run offline in CI with no external API accounts or production secrets.

## 3. Nonfunctional requirements

- **Correctness:** error paths explicit; no silent "zero alerts" on broken source files.
- **Security:** all input data treated as untrusted; least privilege; no shell interpolation.
- **Privacy:** only synthetic fixtures in Git; don't expose raw sensitive data in logs.
- **Scalability:** bounded memory by input size/caps, with measured upper bounds.
- **Observability:** ingestion errors, duplicates, accepted records, alert counts and latency.
- **Reproducibility:** pinned dependency versions, fixed seeds for synthetic data, consistent time semantics.
- **Maintainability:** unit, integration and regression tests; stable data contracts.
- **Operation:** cancel safely, deterministic exit codes, no partial success claims after failures.

## 4. Data contract

Input fixture:
```json
{"event_id":"lab-001","source":"toy-idp","timestamp":"2026-01-01T10:00:00Z","actor":"alice","action":"login_failure","src_ip":"192.0.2.5"}
```

Normalized internal object:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AuthEvent:
    event_id: str
    source: str
    time_utc: datetime   # must be timezone-aware, validated at boundary
    actor: str
    action: str
    src_ip: str | None
    source_line: int
```

Document canonicalization rules and how you handle identical event IDs from different sources.

Alert:
```json
{
  "rule_id": "AUTH-BURST-001",
  "rule_version": "1.0",
  "actor": "alice",
  "window_seconds": 300,
  "failure_count": 3,
  "event_ids": ["lab-001","lab-002","lab-003"],
  "classification": "review",
  "confidence": "rule-only"
}
```

This is a **proposed output schema** and must be validated by tests before claiming conformance.

## 5. Delivery milestones

### Phase 1 — contracts and parser
- Architecture diagram, security assumptions, event schema.
- Strict bounded JSONL parser with line numbers.
- Tests: empty file, malformed UTF-8, wrong shape, duplicate keys, huge lines.

### Phase 2 — normalization and state
- UTC time conversion preserving original.
- Source namespace + event ID dedup.
- SQLite in-memory integration test with transactional replay.
- Tests: time-zone equivalence, missing offset, duplicate ID, mixed sources.

### Phase 3 — detector
- Per-actor sliding window.
- Threshold and suppression/rearm semantics.
- Tests: exact boundary, threshold-1, threshold, time gap, out-of-order, actor cap.
- Document time complexity and actor cardinality.

### Phase 4 — evaluation
- Labeled synthetic dataset (benign and suspicious hypotheses).
- Precision/recall/F1 with nonzero denominator rules.
- False-positive review, baselines and confidence labels.
- Charts with clearly stated denominators and sample generation.

### Phase 5 — CLI, storage and CI
- `--input`, `--output`, `--threshold`, `--window-seconds`, `--max-records`, `--strict`.
- Stable stdout/stderr, exit codes and atomic/transactional output where needed.
- Automated tests on supported Python versions; security analysis with human triage.

### Phase 6 — analyst demo and postmortem
- Show valid synthetic incident path and one corrupt data source.
- Demonstrate error handling and no silent data loss.
- Create incident timeline, report and limitations.
- Present why alert generation alone is not proof of compromise.

## 6. Suggested package layout

```text
mini-soc/
├── pyproject.toml
├── README.md
├── src/minisoc/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── normalize.py
│   ├── dedup.py
│   ├── detection.py
│   ├── evaluation.py
│   ├── persistence.py
│   └── cli.py
├── tests/
│   ├── test_parser.py
│   ├── test_normalization.py
│   ├── test_detection.py
│   ├── test_evaluation.py
│   └── test_integration.py
├── fixtures/synthetic-events.jsonl
└── docs/
    ├── architecture.md
    ├── threat-model.md
    ├── analyst-runbook.md
    └── evaluation.md
```

## 7. Threat model

| Threat | Impact | Defense | Verification |
|---|---|---|---|
| Giant JSON line | memory exhaustion | byte cap before decoding | boundary test |
| Fake/duplicate event ID | wrong counting | source-qualified ID + policy | replay test |
| Out-of-order timestamps | false alerts | reject/reorder within policy | late event test |
| One million actor names | memory exhaustion | actor count cap/expiry | stress test |
| Sensitive payload in error | privacy breach | redact, log metadata only | capture logs in test |
| Untrusted CSV cell | formula execution | consumer-specific export escaping | export test |
| Missing source file | false "clean" result | nonzero exit and incomplete status | error path test |
| API credentials in repo | compromise | secret manager + scanning | CI review |

## 8. Data quality metrics

Report counts of accepted records, rejected records, duplicates, out-of-order records, active actors, queue size, emitted alerts and alert suppression. Show resource usage separately (peak RSS/tracemalloc, CPU time, files/sec).

A detector's measured precision and recall are meaningful only relative to *labeled* examples and a stated sampling scheme. A synthetic exercise cannot establish real-world field performance.

## 9. Example evaluation

Suppose a labeled toy dataset contains 25 suspicious and 75 benign scenarios:
- TP=20, FP=10, FN=5, TN=65.
- Precision = 20/(20+10) ≈ 0.667.
- Recall = 20/(20+5) = 0.80.
- F1 ≈ 0.727.
- False-positive rate = 10/(10+65) ≈ 0.133.

Discuss where the FP and FN came from, not only the aggregate score. Increasing a threshold might lower FP but increase FN.

## 10. Definition of done

- All critical tests pass locally and in CI.
- At least one peer reviews authorization, parser and detection logic.
- One lab report includes input hashes, commands and expected vs observed results.
- No live scans, credentials, confidential data or autonomous containment.
- The README clearly distinguishes prototype capabilities and limitations.
- Demonstrate that a malformed source does not produce a false "all clear."
- Explain the architecture to a junior engineer and the limitations to a manager.

## 11. Oral defense questions
1. What happens if an auth event arrives late?
2. How is an actor different from a source IP?
3. Where are the memory limits and why?
4. What is the trust model for event IDs?
5. Why are raw evidence and normalized data both useful?
6. What false positives did you observe?
7. How does your system signal partial failure?
8. Which controls would be required before connecting to a production SIEM?
9. Why must auto-remediation be a separate permission boundary?
10. Which parts are covered by unit tests versus integration and manual review?

**References:** [NIST SP 800-61r3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), [MITRE ATT&CK](https://attack.mitre.org/).


## 12. A complete sprint-level implementation plan with acceptance tests

The capstone specification becomes actionable only when each feature has acceptance criteria and a reproducible demonstration.

### Sprint 1 — strict ingestion (one to two weeks)

**Deliverable:** validated synthetic JSONL → immutable event objects.

**Acceptance tests:**
- A valid one-line record parses and normalizes to UTC.
- Invalid UTF-8, missing required keys and duplicate JSON keys cause clear failure.
- Line numbers appear in errors.
- A line exceeding the byte cap fails before full materialization.
- The CLI never reports "zero suspicious events" after a parsing failure.

**Data contract:** fields, types, time zones, source IDs and event ID rules are documented. Preserve a reference to the original line. Distinguish raw bytes from normalized data.

### Sprint 2 — correlation and retention (one to two weeks)

**Deliverable:** per-actor event-time rolling windows and deduplication.

**Acceptance tests:**
- t=0, t=30, t=60 triggers an inclusive 60-second threshold 3.
- t=0, t=30, t=61 does not use the expired t=0.
- A duplicate `(source,event_id)` does not count twice.
- A global time regression is either rejected or buffered by a documented policy.
- Actor and per-actor queue caps are enforced with clear failures.
- The rule re-arms only when active count falls below the threshold.

**Tradeoff:** exact deduplication forever requires unbounded memory or persistent state. A finite TTL or disk index can bound cost but allows older replays; document scope and limitations.

### Sprint 3 — reports and evidence (one to two weeks)

**Deliverable:** staged, then atomically committed JSONL report with explainable findings.

**Acceptance tests:**
- A malformed record after one valid alert does not replace an existing complete report.
- Finding includes rule version, actor, time, supporting source-qualified IDs and "review" status.
- Sensitive tokens and raw credentials never appear in logs.
- An empty output is accompanied by a completion record (even when zero alerts).
- Database/report errors produce nonzero process status and are visible to operators.

**Important limitation:** filesystem atomic replace is not equivalent to full crash durability, and metadata/permissions may not be preserved.

### Sprint 4 — analyst assessment and evaluation (one to two weeks)

**Deliverable:** labeled toy scenarios, metrics, triage runbook and report.

Use a table of 100 labeled scenarios:
- 10 suspicious, 90 benign (toy labels only).
- TP=8, FN=2, FP=9, TN=81.
- Precision ≈0.471, recall=0.8, F1≈0.593.
Compare thresholds 2/3/5; discuss alert volume and missed slow failures.

**Do not claim** real-world detector performance from this synthetic exercise.

### Sprint 5 — production-readiness gap assessment

Before any connection to real telemetry:
- Asset/data ownership and written collection authorization.
- Privacy and retention policies.
- Authentication, access control, secret management.
- Source provenance, clock synchronization, API rate limits.
- Input/output resource budgets under adversarial scale.
- Runbooks, rollback and human approval for response.
- Regression tests and review across Python versions.
- Threat model for compromised collectors and adversarial log messages.

This is a review checklist, not permission to deploy a lab prototype against someone else's systems.

## 13. Mapping exact source files to architecture

| Stage | Current learning implementation | Next engineering task |
|---|---|---|
| Input | [mini_soc_pipeline.py](../examples/mini_soc_pipeline.py) | separately model source provenance and limits |
| Parsing | `parse_event` and `read_events` | strict schema version and source-aware retention |
| Detection | `detect_bursts` | late event policy, TTL and streaming metrics |
| Reporting | `write_findings_atomic` | typed alerts, completeness receipt and audit |
| Tests | [test_deep_examples.py](../tests/test_deep_examples.py) | fault injection and synthetic load tests |
| Workshop | [Mini SOC lab](../workshops/02-MINI-SOC-DETECTION.md) | student report, boundary tests and peer review |

## 14. Senior-engineer design-review questions

1. If an identity-provider event arrives 10 minutes late, what exactly happens?
2. How does a malicious username containing JSON escape characters affect reporting?
3. What does the service do if it runs out of disk space halfway through export?
4. Are event IDs stable and authenticated, or can a source generate duplicates?
5. Which metrics distinguish sensor outage from "no incidents"?
6. How will you retain raw evidence without making it public?
7. What prevents replayed records from triggering repeated false alerts?
8. Which permissions can your ingestion service actually exercise?
9. What is the chosen overflow policy for actor cardinality?
10. Can you demonstrate graceful shutdown and correct output under fault injection?

**Portfolio requirement:** answers belong in `docs/architecture.md`, `docs/threat-model.md` and `docs/evaluation.md`; claims without tests or evidence are incomplete.

## 15. A worked incident summary template

```text
Case: LAB-2026-001
Scope: Synthetic authentication telemetry; no real accounts touched
Observed: Three unique failures for one actor in inclusive 300-second window
Rule: AUTH-BURST-001, version and threshold recorded
Evidence: source-qualified event IDs, original log references and hashes
Data quality: 0 parse errors, no late events (for this controlled sample)
Interpretation: Review candidate, not proof of unauthorized access
Benign alternatives: password typos, stale device credentials, scheduled test
Needed corroboration: MFA/session/device data and source clock assurance
Response: Analyst review only; no autonomous account action
Limitations: Synthetic input, no live identity-provider data
```

The write-up should explain *why* each observed event supports the hypothesis and what facts would falsify it. Do not present generic SOC jargon as a substitute for a measured experiment.
