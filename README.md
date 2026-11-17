# Python for Cybersecurity — A Complete Learning Handbook (English)

**From Python zero to defensive security engineering.** This open learning repository teaches the language, software engineering, and Python's applications to cybersecurity through chapters, offline exercises, readable code, local labs, tests, and progressive capstones.

> **Safety:** Operate only on systems, traffic and data you own or have explicit written permission to assess. The repository uses synthetic data and loopback-first examples. Tools are educational, not production-hardened scanners or forensic acquisition systems.

## New: Masterclass Quality Pass — every Deep Dive chapter

**All 22 chapters** now include an individually designed *Masterclass* teaching case: a subtle misconception, an explicit causal model, a concrete comparison table, one **standalone, tested Python example**, and an independent transfer exercise. The new examples focus on correctness **and** what the code does not prove. They cover Python type/key collisions, false all-clears, exact sliding-window alert semantics, bounded parsing, SQL rollback, per-object authorization, mutation tests, TaskGroup failure propagation, DNS/SSRF trust, HMAC replay, SOC base rates, timestamp uncertainty, TCP capture gaps, benign high entropy, incomplete cloud inventories, vulnerability applicability, ML leakage and more.

Read the [Deep Dive Masterclass chapters](course/README.md), then complete the corresponding [guided labs](lab-manual/README.md). Review the [editorial quality and verification rubric](reference/EDITORIAL-QUALITY-STANDARD.md).

## New: complete hands-on learning track

- **[22 guided chapter labs](lab-manual/README.md):** one lab per Deep Dive chapter with runnable code, expected output, failure cases, explanation and grading.
- **[100 worked exercise solutions](solutions/by-exercise/README.md):** full 001–100 numbering, code or technical model, assertions, and security analysis. The [original 100 prompts](reference/100-EXERCISES.md) now include concrete challenges and direct answer links.
- **[Progressive project build path](projects/BUILD-PATH.md):** four tested offline Python tools (integrity inventory, IOC quality, incident timeline and detection evaluation) leading into the Mini-SOC capstone.
- **Automated verification:** the curriculum checker covers 22 chapters, 22 labs and 100 solutions; safe standard-library lab and solution snippets are run in CI, with the optional cryptography examples clearly distinguished.

**Start here:** read one [chapter](course/README.md), complete its linked lab, solve the matching exercise before checking the answer, then build a portfolio stage. All examples use synthetic or explicitly authorized data.

## Start with the **Deep Dive — Expanded Third Edition**

The older `python/` and `security/` pages are **short topic overviews**. The expanded [**22-unit detailed course**](course/README.md) expands them into substantial English lessons with theory, step-by-step explanations, annotated code, security pitfalls, trace tables, self-check questions and worked answer checks.

**Recommended reading order:**

1. [Python internals, types, control flow and data structures](course/README.md#learning-path) — Units 01–03.
2. [Bytes, binary protocols, trusted parsing and SQL](course/04-BYTES-ENCODING-BINARY-PARSERS.md) — Units 04–05.
3. [Architecture, testing, concurrency and OS](course/06-TYPING-OOP-ARCHITECTURE.md) — Units 06–08.
4. [Networking, web/API security and cryptography](course/09-NETWORKING-DNS-TCP-TLS.md) — Units 09–11.
5. [SOC, DFIR, PCAP and malware triage](course/12-SOC-DETECTION-ENGINEERING.md) — Units 12–15.
6. [Cloud, vulnerabilities, endpoint telemetry and capstone](course/16-CLOUD-CONTAINERS-DEVSECOPS.md) — Units 16–19.
7. [Advanced Python internals, anomaly detection and regex](course/20-ADVANCED-PYTHON-PERFORMANCE.md) — Units 20–22.

**New tested examples:** [strict policy validation, tenant authorization, timezone-aware logs, detection metrics and SQLite transactions](examples/chapter_cases.py), with [regression tests](tests/test_chapter_cases.py). Every Deep Dive chapter now includes a further detailed case study and exercise set.

**Full worked answer bank:** [12 complete solutions with reasoning and tests](solutions/WORKED-SOLUTIONS.md).

**Guided, executable workshops:** [binary framing](workshops/01-BINARY-FRAMING.md), [offline mini SOC](workshops/02-MINI-SOC-DETECTION.md), [cryptography](workshops/03-CRYPTOGRAPHY-LAB.md), [incident timelines](workshops/04-INCIDENT-TIMELINE.md). Check [new standard-library examples](examples/strict_frame.py), [atomic mini SOC](examples/mini_soc_pipeline.py) and [their tests](tests/test_deep_examples.py).

## Choose your entry point
| Your background | Begin here | Then |
|---|---|---|
| New to Python | [Start Here](python/00-START-HERE.md) → [Foundations](python/01-LANGUAGE-FOUNDATIONS.md) | Complete all `python/` chapters |
| Know some Python | [Python index](reference/CHAPTER-INDEX.md) | [Security modules](security/00-SAFETY-THREAT-MODELING.md) |
| Know Linux and networking | [Networking with Python](security/01-NETWORKING-AND-SOCKETS.md) | [SOC detection](security/06-LOG-ANALYTICS-SOC-DETECTION.md) |
| Prefer building | [Runnable examples](examples/README.md) | [Labs](labs/README.md) and [capstones](projects/PYTHON-CAPSTONES.md) |
| Need a schedule | [Study plan](reference/LEARNING-PLAN.md) | [Skills checklist](reference/SKILLS-CHECKLIST.md) |

## The handbook
**Python fundamentals:** [01](python/01-LANGUAGE-FOUNDATIONS.md) language, [02](python/02-DATA-STRUCTURES-ALGORITHMS.md) collections/complexity, [03](python/03-FUNCTIONS-MODULES-TYPING.md) functions/typing, [04](python/04-FILES-ENCODING-PARSING.md) files/bytes, [05](python/05-EXCEPTIONS-TESTING-DEBUGGING.md) testing, [06](python/06-OOP-AND-ARCHITECTURE.md) OOP, [07](python/07-ITERATORS-ASYNC-FOUNDATIONS.md) iterators, [08](python/08-CONCURRENCY-AND-ASYNCIO.md) concurrency, [09](python/09-OS-AND-AUTOMATION.md) OS automation, [10](python/10-CLI-PACKAGING-DEPENDENCIES.md) packaging/CLI, [11](python/11-INTERNALS-PERFORMANCE-ADVANCED.md) advanced.

**Cybersecurity:** [00](security/00-SAFETY-THREAT-MODELING.md) threat modeling, [01](security/01-NETWORKING-AND-SOCKETS.md) networks, [02](security/02-PACKET-ANALYSIS-AND-PCAP.md) packets, [03](security/03-WEB-APPLICATION-AND-API-SECURITY.md) web/API, [04](security/04-CRYPTOGRAPHY-PASSWORDS-KEY-MANAGEMENT.md) crypto, [05](security/05-IDENTITY-ACCESS-AND-AUTHORIZATION.md) IAM, [06](security/06-LOG-ANALYTICS-SOC-DETECTION.md) SOC, [07](security/07-DIGITAL-FORENSICS-AND-INCIDENT-RESPONSE.md) DFIR, [08](security/08-MALWARE-TRIAGE-AND-STATIC-ANALYSIS.md) malware triage, [09](security/09-THREAT-INTELLIGENCE-AND-OSINT.md) intelligence, [10](security/10-CLOUD-CONTAINERS-AND-DEVSECOPS.md) cloud, [11](security/11-VULNERABILITY-MANAGEMENT-AND-FUZZING.md) vulnerabilities, [12](security/12-SECURE-SDLC-AND-PYTHON-THREATS.md) secure SDLC, [13](security/13-WINDOWS-LINUX-ENDPOINT-TELEMETRY.md) endpoints, [14](security/14-DATABASES-DATA-PIPELINES-AND-SIEM.md) pipelines, [15](security/15-ADVANCED-DEFENSE-RESEARCH.md) research.

**Reference:** [Full index](reference/CHAPTER-INDEX.md), [Python/security library map](reference/LIBRARY-MAP.md), [glossary](reference/GLOSSARY.md), [100 exercises](reference/100-EXERCISES.md), [learning plan](reference/LEARNING-PLAN.md), [skills checklist](reference/SKILLS-CHECKLIST.md), [verified starting references](reference/REFERENCES.md).

**Practice:** [Step-by-step labs](labs/README.md), [code examples](examples/README.md), [synthetic fixtures](fixtures/), [tests](tests/), [capstone specifications](projects/PYTHON-CAPSTONES.md).

## Run the examples
```bash
git clone https://github.com/10425058-jpg/Python-for-CyberSecurity.git
cd Python-for-CyberSecurity
python -m venv .venv
# Activate your venv using instructions in python/00-START-HERE.md
python -m unittest discover -s tests -v
python -m examples.mini_soc_pipeline --input fixtures/synthetic-auth.jsonl --output findings.jsonl
python -m examples.strict_frame
python -m examples.chapter_cases
python tools/verify_curriculum.py
python -m examples.log_detector fixtures/synthetic-auth.jsonl
python -m examples.file_manifest fixtures
python -m examples.indicator_normalizer fixtures/synthetic-indicators.jsonl
python -m examples.local_port_check 8080
```

## What this resource does and does not claim
This repository now contains a **third-edition expansion of 22 in-depth lessons** plus short overviews. Although substantially expanded, it still cannot exhaustively cover every changing Python library, protocol, OS, cybersecurity specialty or attack technique. Advanced production work requires current vendor docs, lab practice, peer review and supervised experience. The exercises are defensive and local-first; example tools are not forensic-grade or production hardened.

## Other learning materials
This repository is exclusively dedicated to Python for Cybersecurity. General cybersecurity material lives separately at [CyberSecurity-](https://github.com/10425058-jpg/CyberSecurity-).


## Contributions
Improve explanations with tested examples, version-aware citations, meaningful exercises, and small PRs. Never commit credentials, proprietary logs, malware samples, stolen data, or live unauthorized targets. Report software vulnerabilities privately to the repository maintainer.
