# Editorial Quality Standard — Python for Cybersecurity

This is an editorial and engineering rubric for the **22 Deep Dive chapters**. The objective is **accurate transferable understanding**, not page count. A chapter should teach a concept, its assumptions, its failure modes and how a student can verify its behavior.

## Five requirements for a high-quality teaching section

**1. A falsifiable learning outcome.** Write "explain why a replayed source-qualified event does not increment the count" rather than "understand cybersecurity". A student must be able to demonstrate success with an example, test or clear explanation.

**2. A correct causal model.** Separate Python language semantics from contingent CPython implementation details, and separate security observations from incident conclusions. State what is assumed about data provenance, authorization, time and resource budgets.

**3. A worked example with contrasting cases.** Include a byte diagram, state table, decision matrix or concrete input/output trace. Show one passing case and at least two *different reasons* for rejection. An example should not imply real security guarantees its checks do not provide.

**4. An independent transfer task.** Give a new input or changed requirement that requires the learner to reason, not merely copy the worked code. Avoid publishing the full answer immediately beside the task when possible; provide answer *checks* and link to the separate solutions.

**5. Verification and maintenance.** Each chapter's tagged \`# MASTERCLASS_RUNNABLE\` example must be standalone, Python 3.11+ compatible and free of external network/credentials. CI executes it on supported Python versions, while the existing curriculum auditor checks other fenced Python examples for syntax and local Markdown navigation.

## Chapter-specific quality targets

| Area | Explain precisely | Required negative/edge case |
|---|---|---|
| Python runtime/types | identity, equality, mutability and strict types | boolean-as-integer or NaN |
| Control flow/errors | valid-empty vs incomplete processing | malformed input after valid records |
| Data structures | time/space complexity, bounded state | exactly-on-window boundary and replay |
| Binary parsing | header, byte order, framing and data cap | short frame, trailing data, duplicate key |
| Files/SQL | byte limits, transactions, source trust | rollback on corrupt row |
| Architecture | validated models and authorization dependency | unauthorized cross-tenant object |
| Testing/CI | invariant, mutation and supply-chain identity | off-by-one threshold mutant |
| Async/OS | producer/worker lifecycle, cancellation | worker failure and task cleanup |
| Networks/TLS | DNS/connect trust, TCP framing, TLS identity | forbidden destination / redirect |
| API security | authentication vs object permission vs sink encoding | valid login, forbidden resource |
| Cryptography | key lifecycle, replay, nonce and tag semantics | replayed or modified message |
| SOC | source gaps, thresholds, base rates, triage | false positives and incomplete input |
| DFIR | evidence vs inference, clock uncertainty | events whose time intervals overlap |
| PCAP | layers, capture loss, retransmits | missing/overlapping sequence bytes |
| Static triage | metadata vs verdict, benign high entropy | high entropy without malware |
| Cloud | effective policy and coverage | incomplete inventory must not pass |
| Vulnerabilities | advisories, deployment, applicability, risk | unknown exposure vs not affected |
| Capstone | stage contracts and report completeness | corrupt input after first finding |
| Endpoint telemetry | provider/channel/version context | same event number, different source |
| Performance | cardinality, workload measurements | many unique actors |
| ML/statistics | prevalence, leakage, labeling | entity overlap across partitions |
| Regex | lexical vs semantic checks and ReDoS | Unicode digits, suffix input |

## Example reproducibility contract

From the repository root:

```bash
python tools/verify_curriculum.py
python -m unittest tests.test_masterclass_chapters -v
python -m unittest discover -s tests -v
```

The masterclass harness executes only specifically marked, local standard-library blocks. Many other examples in the course may require an optional package or serve as pseudocode. **Syntax validation is not functional verification.** A passing CI matrix is evidence for the tested examples and code paths, not a certification of every possible input or deployment security.

## Editorial review worksheet

For each chapter, answer:
1. Can a beginner state the purpose of each nontrivial function and symbol?
2. Does the input contract say where data comes from and what is trustworthy?
3. Is there at least one complete execution trace, not just a finished output?
4. Can the learner reproduce a failure and identify which check rejects it?
5. Is every security claim bounded by evidence and a threat model?
6. Are exceptions, incomplete input, time and memory limits handled visibly?
7. Are links to the guided lab and original chapter references still valid?
8. Does the exercise test a *new* scenario, rather than restating the code?
9. Does code run without production credentials or unapproved targets?
10. Has another reader checked technical statements and examples after editing?

Score each item 0 (absent), 1 (partial), 2 (complete). Require at least **16/20** and **zero critical factual or safety errors** for a chapter to be considered editorially reviewed. This checklist is aspirational; adding the masterclass does not automatically certify the entire old chapter against all ten items.

## Avoid common low-quality patterns

- Inflating word counts by repeating definitions without adding a new mental model.
- Calling an untested snippet "production secure" because it has type hints.
- Treating a sample hash or indicator match as attribution.
- Claiming cloud compliance after a failed inventory page.
- Equating model accuracy with analyst usefulness in rare-event populations.
- Assuming a passing static analysis check proves absence of vulnerabilities.
- Including public network scanning or real credentials in a beginner lab.

**Revision cadence:** update references and library/version-specific claims when upstream guidance changes. When a defect is discovered, fix the explanation *and* add a regression test if executable. Preserve independent review and clearly record remaining limitations.
