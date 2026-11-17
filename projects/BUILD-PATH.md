# Progressive Build Path — From Python to an Explainable Mini SOC

This roadmap goes beyond reading about tools: every stage has **real code, an input fixture, a reproducible command, tests, a threat model and a graduation condition**. Python 3.11+; offline/synthetic data and authorized paths only.

## Development graph

```text
Strict Python fundamentals (chapters 01–05)
   ↓
P1 — Integrity inventory: bytes → SHA-256 → manifest → diff
   ↓
P2 — IOC quality: bounded JSONL → canonical IP → provenance → expiry
   ↓
P3 — Incident timeline: provider schemas → UTC → source-preserving timeline
   ↓
P4 — Detection evaluator: labels → confusion matrix → quality report
   ↓
P5 — Mini SOC: bounded ingest → dedup → rolling windows → review alerts
   ↓
Production-readiness gap review (not automatic deployment)
```

## Stage 0 — Foundations (1 week, around 10 focused hours)

**Deliverables:** Python 3.11+ environment, full unit test pass, two handwritten validators, and a trust-boundary diagram.

**Required knowledge:** bytes vs Unicode, booleans vs integers, dictionaries, exceptions, context managers, JSON and time zones.

**Gate:** reject invalid JSON, a Boolean in an integer policy, an oversized event and a naive timestamp; explain why silent parse skipping can cause a false all-clear.

## Stage 1 — File Integrity Inventory (1–2 weeks)

**Tool:** [`integrity_inventory.py`](builds/integrity_inventory.py).

```bash
python -m projects.builds.integrity_inventory fixtures --max-files 1000
python -m unittest tests.test_project_builds.IntegrityProjectTests -v
```

**Implementation sequence:** inventory a permitted directory → skip symlinks → hash in chunks → preserve a relative-path manifest → take two snapshots → compare added/removed/changed → document mutable file races.

**Acceptance:** file mutation changes its SHA-256; added/removed reports are deterministic; file count/byte limits reject clearly; all tests pass. **Limits:** not forensic-grade evidence acquisition, not race-proof against adversarial filesystem changes.

**Advanced extension:** save snapshots outside the scanned tree with safe overwrite policy, then add a strict manifest schema validator and atomic report writer.

## Stage 2 — IOC Quality and Lifecycle (1–2 weeks)

**Tool:** [`indicator_quality.py`](builds/indicator_quality.py). **Fixture:** [synthetic IOC feed](../fixtures/project-indicators.jsonl).

```bash
python -m projects.builds.indicator_quality fixtures/project-indicators.jsonl --as-of 2026-01-10T00:00:00Z
python -m unittest tests.test_project_builds.IndicatorsProjectTests -v
```

**Implementation sequence:** bound line length → parse JSON → validate IPv4/IPv6 → retain source/timestamp/confidence → compute expiry → dedup exact records by source/IP → reject conflicting duplicates → emit completeness status.

**Acceptance:** duplicate counts, invalid address/TTL/type rejection, UTC expiry calculation, deterministic output and no network calls. **Limits:** a feed is an allegation, not evidence proving maliciousness; never auto-block an IP solely based on a low-confidence match.

**Advanced extension:** design source confidence and provenance when two feeds report contradictory evidence; preserve each source instead of overwriting.

## Stage 3 — Cross-OS Incident Timeline (2–3 weeks)

**Tool:** [`incident_timeline.py`](builds/incident_timeline.py). Fixtures: [lab Linux](../fixtures/project-linux.jsonl), [lab Windows](../fixtures/project-windows.jsonl).

```bash
python -m projects.builds.incident_timeline fixtures/project-linux.jsonl fixtures/project-windows.jsonl
python -m unittest tests.test_portfolio_stage2.TimelineProjectTests -v
```

**Implementation sequence:** strict provider-specific schema → source file and line → chunked SHA-256 of source bytes → aware UTC conversion → stable sort by event time → original timestamp retention → uncertainty-aware analyst report.

**Expected:** events with `17:01:00+07:00` represent `10:01:00Z`. **Acceptance:** malformed events, duplicate IDs and missing time-zone offsets fail; no false claims of complete timeline after partial failure.

**Limits:** invented provider IDs are not real Windows event IDs; system clocks and log contents are not independently authenticated.

**Advanced extension:** build explicit event-time versus ingest-time fields and a clock-skew uncertainty budget.

## Stage 4 — Detection Quality Evaluator (1–2 weeks)

**Tool:** [`detection_evaluator.py`](builds/detection_evaluator.py). **Fixture:** [labeled toy cases](../fixtures/project-labels.jsonl).

```bash
python -m projects.builds.detection_evaluator fixtures/project-labels.jsonl
python -m unittest tests.test_portfolio_stage2.EvaluationProjectTests -v
```

**Implementation sequence:** validate a unique case ID and exact 0/1 labels → count TP/FP/FN/TN → calculate precision/recall/F1/FPR → handle undefined denominators → evaluate base-rate effects.

**Expected fixture:** TP=2, FP=1, FN=1, TN=2; precision and recall both 2/3. **Acceptance:** duplicate labels, invalid data and oversized records fail; the report distinguishes measured sample quality from real-world effectiveness.

**Advanced extension:** label 100 deterministic synthetic login scenarios, vary thresholds and explain the false-positive workload in analyst-hours.

## Stage 5 — Explainable Mini SOC (6–12+ weeks)

**Starter:** [`mini_soc_pipeline.py`](../examples/mini_soc_pipeline.py). [Full architecture/requirements](../course/18-MINI-SOC-CAPSTONE-BLUEPRINT.md).

```bash
python -m examples.mini_soc_pipeline --input fixtures/synthetic-auth.jsonl --output findings.jsonl
python -m unittest tests.test_deep_examples.MiniSocTests -v
```

**Release R1:** bounded strict parsing, source IDs and incomplete-ingest status.  
**Release R2:** timezone normalization, deduplication, immutable event types and source references.  
**Release R3:** actor windows, suppression and re-arm policy, memory limits, late-event handling.  
**Release R4:** transactionally staged reports, protected evidence references and an analyst runbook.  
**Release R5:** labeled evaluation with false-positive/false-negative analysis and performance profiling.  
**Release R6:** peer review, reproducible demo, threat model and documented production gaps.

**Graduation demo:** corrupt a file *after* three valid failures and show the report is not silently replaced with a partial clean result. Add one intentionally benign burst and explain why no account is locked automatically.

**Not production ready:** credentials, compliance policy, protected logging, source authentication, distributed retry/idempotency, late records, telemetry retention, monitoring and incident-response authority all need a separate engineering review.

## Final engineering review (1 week)

Create an architecture/production-gap report covering authorization, confidentiality, error semantics, resource limits, supply-chain security, storage, telemetry reliability, time synchronization, cost, recovery, data protection and change-control. Keep production credentials and personal data out of the repository.

## Rubric (100 points)

| Category | Score | Evidence |
|---|---:|---|
| Correct behavior and explicit contracts | 25 | tests and expected output |
| Failure handling and completeness | 20 | negative tests and error states |
| Security design and least privileges | 20 | threat model and safe defaults |
| Architecture and reproducibility | 15 | readable code, fixtures, CI |
| Measured performance and quality | 10 | CPU, memory, error rate or detection metrics |
| Reporting and documented limitations | 10 | analyst-style write-up |
| **Total** | **100** | **Pass: ≥80 and all safety gates** |

You can also choose an alternative from the [11 original capstone briefs](PYTHON-CAPSTONES.md). Finish one project before expanding scope; depth and evidence matter more than listing frameworks in a portfolio.
