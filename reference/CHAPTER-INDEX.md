# Full curriculum index

> **The expanded third-edition course has its own comprehensive index:** [22 deep-dive lessons with annotated code and worked exercises](../course/README.md). The chapters below are quick-reference companions, not the main long-form lessons.

## Part I — Programming foundations (12 chapters)
| Chapter | Key competencies | Practice artifact |
|---|---|---|
| [00 Start](../python/00-START-HERE.md) | safe setup and goals | lab notebook |
| [01 Language](../python/01-LANGUAGE-FOUNDATIONS.md) | values, expressions, branching, functions | classifier |
| [02 Data structures](../python/02-DATA-STRUCTURES-ALGORITHMS.md) | mappings, sets, queues, complexity | counters |
| [03 Type design](../python/03-FUNCTIONS-MODULES-TYPING.md) | API contract, typing, modules | typed rule |
| [04 Parsing](../python/04-FILES-ENCODING-PARSING.md) | text, bytes, safe parsing, hashes | inventory |
| [05 Tests](../python/05-EXCEPTIONS-TESTING-DEBUGGING.md) | tests, debug, logging | parser tests |
| [06 Architecture](../python/06-OOP-AND-ARCHITECTURE.md) | classes, composition, protocols | rule engine |
| [07 Lazy iteration](../python/07-ITERATORS-ASYNC-FOUNDATIONS.md) | generators, contexts, decorators | streaming reader |
| [08 Concurrency](../python/08-CONCURRENCY-AND-ASYNCIO.md) | bounded async, cancellation | local diagnostic |
| [09 OS scripting](../python/09-OS-AND-AUTOMATION.md) | filesystem, subprocess, least privilege | file manifest |
| [10 Packaging](../python/10-CLI-PACKAGING-DEPENDENCIES.md) | CLI, dependencies, CI | packaged tool |
| [11 Advanced](../python/11-INTERNALS-PERFORMANCE-ADVANCED.md) | profiler, runtime, resource controls | performance report |

## Part II — Python for cybersecurity (16 chapters)
| Chapter | Focus | Artifact |
|---|---|---|
| [00 Ethics](../security/00-SAFETY-THREAT-MODELING.md) | scope, threat models, safeguards | threat model |
| [01 Networking](../security/01-NETWORKING-AND-SOCKETS.md) | TCP/UDP, DNS, TLS, sockets | local checker |
| [02 Packets](../security/02-PACKET-ANALYSIS-AND-PCAP.md) | offline PCAP and flows | flow report |
| [03 Web/API](../security/03-WEB-APPLICATION-AND-API-SECURITY.md) | validation, SQL, auth, SSRF | secure local API |
| [04 Crypto](../security/04-CRYPTOGRAPHY-PASSWORDS-KEY-MANAGEMENT.md) | AEAD, HMAC, password hashing | encryption demo |
| [05 Identity](../security/05-IDENTITY-ACCESS-AND-AUTHORIZATION.md) | RBAC/ABAC, tokens, sessions | policy tests |
| [06 Detection](../security/06-LOG-ANALYTICS-SOC-DETECTION.md) | telemetry, thresholds, triage | log detector |
| [07 DFIR](../security/07-DIGITAL-FORENSICS-AND-INCIDENT-RESPONSE.md) | evidence, timeline, response | incident report |
| [08 Malware triage](../security/08-MALWARE-TRIAGE-AND-STATIC-ANALYSIS.md) | file magic, entropy, binary basics | static report |
| [09 Intelligence](../security/09-THREAT-INTELLIGENCE-AND-OSINT.md) | indicator normalization, STIX | enrichment |
| [10 Cloud](../security/10-CLOUD-CONTAINERS-AND-DEVSECOPS.md) | IAM, containers, CI | audit policy |
| [11 Vulnerabilities](../security/11-VULNERABILITY-MANAGEMENT-AND-FUZZING.md) | advisories, fuzzing, triage | findings report |
| [12 Secure SDLC](../security/12-SECURE-SDLC-AND-PYTHON-THREATS.md) | code review, boundary checks | review notes |
| [13 Endpoints](../security/13-WINDOWS-LINUX-ENDPOINT-TELEMETRY.md) | Linux/Windows logs | normalized schema |
| [14 Databases](../security/14-DATABASES-DATA-PIPELINES-AND-SIEM.md) | SQL, SIEM, pipeline | ingest pipeline |
| [15 Advanced research](../security/15-ADVANCED-DEFENSE-RESEARCH.md) | analytic rigor and specialization | mini SOC |

## Part III — Build, test, reflect
- [Labs](../labs/README.md), [code](../examples/README.md), [100 exercises](100-EXERCISES.md), [capstones](../projects/PYTHON-CAPSTONES.md).
- [Tools and libraries](LIBRARY-MAP.md), [references](REFERENCES.md), [schedule](LEARNING-PLAN.md), [checklist](SKILLS-CHECKLIST.md).

## Learning objectives and assessment
A **beginner** can explain syntax and write/tests a small program. An **intermediate practitioner** safely handles files, APIs, concurrency, security telemetry and failures. An **advanced practitioner** designs resource-bounded, observable, threat-modeled systems and evaluates detections with meaningful evidence. Real expertise requires professional feedback and experience in live operational contexts.

## Third-edition executable case studies
- [Validated policy, toy auth log, authorization, metrics and SQLite importer](../examples/chapter_cases.py) with [regression tests](../tests/test_chapter_cases.py).
- [22 in-depth chapters](../course/README.md) now contain more trace-based explanations and chapter-level exercises.

## New: practical curriculum
- [All 22 guided labs](../lab-manual/README.md) linked to the corresponding chapters.
- [All 100 numbered worked answers](../solutions/by-exercise/README.md).
- [Offline portfolio build path with four tested tools](../projects/BUILD-PATH.md).

## Worked answers
- [12 fully solved representative exercises](../solutions/WORKED-SOLUTIONS.md) with code, tests and security rationale.

## Fully guided practical workshops
- [Binary parser and negative tests](../workshops/01-BINARY-FRAMING.md)
- [Offline mini SOC detector](../workshops/02-MINI-SOC-DETECTION.md)
- [Cryptography with correct primitives](../workshops/03-CRYPTOGRAPHY-LAB.md)
- [DFIR timeline with UTC and hashes](../workshops/04-INCIDENT-TIMELINE.md)
