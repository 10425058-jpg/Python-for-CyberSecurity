# Python for Cybersecurity — Deep Dive (Expanded Third Edition)

**All 22 chapters have been expanded with additional executable case studies, trace tables, failure-mode discussion, exercises and solution cues.** This is the detailed, explanation-first track. The [`python/` modules](../python/README.md) now provide full beginner-to-advanced textbook lessons; the `security/` pages remain quick-reference overviews. The units here contain the deeper conceptual lessons, explanatory traces, annotated Python, security failure modes, worked checks and end-of-unit assignments. Every active exercise is offline or loopback-only, using authorized/synthetic data.

## Applied practice with 22 labs and 100 answers

Every chapter now links to its own [step-by-step guided lab](../lab-manual/README.md). The [100-solution answer bank](../solutions/by-exercise/README.md) expands all original exercise prompts into runnable or defensible answers, and the [project build path](../projects/BUILD-PATH.md) provides tested starter programs for integrity monitoring, IOC quality, evidence timelines and detection evaluation.

## Masterclass — a deeper way to study each chapter

Each of the 22 chapters has an early **Masterclass** section aimed at the hardest conceptual mistake in that topic. This is different from simply adding another introduction: it presents a causal explanation, a concrete input/output or decision table, a reproducible defensive Python example, its precise limitations, and an independent extension question.

**Suggested 30-minute teaching loop:** first predict the result without executing; run the code; alter one boundary condition; explain why the code rejects it or changes output; write one new assertion; then teach the concept in plain English without code. This is followed by the longer chapter explanation, the [matching Guided Lab](../lab-manual/README.md), and the [100 worked-answer exercises](../solutions/by-exercise/README.md).

Masterclass code blocks are marked with `# MASTERCLASS_RUNNABLE`. The [test harness](../tests/test_masterclass_chapters.py) **executes all 22 tagged examples** on each tested Python version, rather than relying on syntax checks alone. The [editorial standard](../reference/EDITORIAL-QUALITY-STANDARD.md) documents requirements and acknowledges remaining limitations; passing tests is not a blanket claim of security.

## How to learn efficiently

For each unit:
1. Read the problem scenario and learning objectives. Predict what the code will do.
2. Type each example yourself and run it. Change one input at a time and explain the resulting behavior.
3. Draw a data-flow diagram: identify input, trust boundary, parser, validated model, side effects and output.
4. Complete the questions **before** reading the hints and answer checks.
5. Write a minimum of three tests: normal case, boundary case and malformed/adversarial data.
6. Record exact Python version, commands, expected/observed output and limitations in your notes.
7. Do not move ahead simply because a script runs: explain why the algorithm and security constraints are appropriate.

### Prerequisites
- Python 3.11+ for examples and standard-library tests (a maintained version is preferable).
- Git, an editor, a terminal, a virtual environment.
- Basic network knowledge before the packet/TLS modules.
- Access only to owned/explicitly authorized systems for any network/OS work.

### Self-study quality gate
For every unit, be able to explain **what, why, how, failure modes and how to prove correctness**. An excellent project is not just more code: it is **evidence that assumptions and boundaries were understood**.

## Learning path

| Part | Unit | What you will actually learn |
|---|---|---|
| I | [01 — Python runtime and types](01-PYTHON-RUNTIME-AND-TYPES.md) | name/object model, aliases, Unicode, strict validation |
| I | [02 — Control flow and functions](02-CONTROL-FLOW-FUNCTIONS-ERRORS.md) | contracts, branches, errors, clean CLI design |
| I | [03 — Collections and algorithms](03-COLLECTIONS-COMPLEXITY-STREAMS.md) | complexity, deques, bounded streams, cardinality |
| I | [04 — Bytes and protocols](04-BYTES-ENCODING-BINARY-PARSERS.md) | binary headers, byte order, framing, parser fuzzing |
| I | [05 — Files, JSON and SQL](05-FILES-JSON-SQL-TRUST-BOUNDARIES.md) | trust boundaries, strict parsing, time zones, parameterization |
| I | [06 — Typing and architecture](06-TYPING-OOP-ARCHITECTURE.md) | Protocol, OOP, dependency injection, pure core |
| I | [07 — Testing and CI](07-TESTING-CI-AND-SUPPLY-CHAIN.md) | unit/property tests, supply chain, CI threat model |
| I | [08 — Concurrency and OS](08-CONCURRENCY-ASYNC-OS-AUTOMATION.md) | bounded async, cancellation, subprocess safety, privileges |
| II | [09 — Networks and TLS](09-NETWORKING-DNS-TCP-TLS.md) | TCP framing, DNS, TLS validation, reachability interpretation |
| II | [10 — Web/API security](10-WEB-API-AUTHORIZATION-SECURITY.md) | authorization, injection, CSRF/CORS, SSRF boundaries |
| II | [11 — Cryptography](11-CRYPTOGRAPHY-DEEP-DIVE.md) | hashes, HMAC, secrets, scrypt, AEAD, key management |
| II | [12 — SOC detection](12-SOC-DETECTION-ENGINEERING.md) | rolling windows, false positives, metrics, incident triage |
| II | [13 — DFIR](13-DFIR-EVIDENCE-AND-TIMELINES.md) | evidence handling, timelines, chain of custody, reporting |
| II | [14 — Packet forensics](14-PCAP-AND-PROTOCOL-FORENSICS.md) | offline PCAP, protocol layers, flows, visibility limits |
| II | [15 — Static triage / intelligence](15-MALWARE-TRIAGE-THREAT-INTELLIGENCE.md) | entropy, file magic, benign triage, IOC trust |
| II | [16 — Cloud and DevSecOps](16-CLOUD-CONTAINERS-DEVSECOPS.md) | IAM, mock policy-as-code, container risks, CI boundaries |
| II | [17 — Vulnerabilities and fuzzing](17-VULNERABILITIES-FUZZING-RISK.md) | CVE/CVSS risk, safe local parser fuzzing |
| II | [18 — Mini SOC capstone](18-MINI-SOC-CAPSTONE-BLUEPRINT.md) | complete architecture, contracts, tests, review criteria |
| II | [19 — Endpoint telemetry](19-ENDPOINT-OS-TELEMETRY.md) | Linux/Windows logs, source context, cross-platform normalization |
| III | [20 — Advanced Python and performance](20-ADVANCED-PYTHON-PERFORMANCE.md) | import system, introspection, generators, profiling, caches, native boundaries |
| III | [21 — Security statistics and ML](21-STATISTICS-ANOMALY-DETECTION-ML.md) | base rates, anomaly baselines, confusion matrix, leakage and drift |
| III | [22 — Regex and untrusted text](22-REGEX-UNTRUSTED-TEXT.md) | fullmatch, Unicode, log grammars, ReDoS limits |

## Verified chapter examples

The [shared standard-library demonstration module](../examples/chapter_cases.py) implements strict JSON policy validation, timezone-aware toy log parsing, a tenant-scoped authorization rule, detection precision/recall and a transactional SQLite importer. Its [regression tests](../tests/test_chapter_cases.py) exercise malformed input, cross-tenant denial, false-positive metrics and all-or-nothing imports. Run:

```bash
python -m examples.chapter_cases
python -m unittest tests.test_chapter_cases -v
python tools/verify_curriculum.py
```

**Chapter learning standard:** read the original explanation, then the newly expanded numbered sections toward the end of each chapter. For every code example, predict normal and malformed outcomes, run it, and write an independent test. Python snippets in these chapters are syntax-checked in CI; this is not a claim that every snippet has been functionally proven.

## Worked solutions

Study [12 fully worked answers](../solutions/WORKED-SOLUTIONS.md) for validated input, data structures, SQL, authorization, evidence hashing, AEAD, metrics and time-window detection. Each explains why the solution works and its limits.

## Fully guided workshops and checked code

| Workshop | Topic | Software |
|---|---|---|
| [01](../workshops/01-BINARY-FRAMING.md) | binary protocol parsing + negative tests | [strict_frame.py](../examples/strict_frame.py) |
| [02](../workshops/02-MINI-SOC-DETECTION.md) | offline login correlation + failure handling | [mini_soc_pipeline.py](../examples/mini_soc_pipeline.py) |
| [03](../workshops/03-CRYPTOGRAPHY-LAB.md) | authenticated encryption / integrity | vetted `cryptography` package |
| [04](../workshops/04-INCIDENT-TIMELINE.md) | evidence manifest and incident timeline | standard-library scripts |

## What "deep" means in this edition
The curriculum now explains **assumptions, invariants, data-flow, limitations, edge cases, testing and real-world security implications**. It still cannot replace specialized vendor documentation, forensic-grade procedures or professional operations experience. Real systems, libraries and best practices evolve; verify authoritative sources for the version you deploy.

**Next steps:** finish parts I & II, complete the four guided workshops, add tests to your own solutions, and build the [mini SOC capstone](18-MINI-SOC-CAPSTONE-BLUEPRINT.md). Keep portfolio fixtures synthetic.
