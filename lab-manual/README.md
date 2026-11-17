# Guided Lab Manual — 22 chapter companions

Each chapter has a guided lab containing runnable code, explicit inputs and expected outcomes, negative tests, a walkthrough, safety notes, and a rubric. Learn with synthetic/owned resources only.

| Chapter | Lab | Focus |
|---|---|---|
| 01 | [Guided Lab 01](01-GUIDED-LAB.md) | Python identity and strict JSON types |
| 02 | [Guided Lab 02](02-GUIDED-LAB.md) | Control flow and visible failures |
| 03 | [Guided Lab 03](03-GUIDED-LAB.md) | Data structures and burst windows |
| 04 | [Guided Lab 04](04-GUIDED-LAB.md) | Binary parser and framing |
| 05 | [Guided Lab 05](05-GUIDED-LAB.md) | JSONL and SQLite transactions |
| 06 | [Guided Lab 06](06-GUIDED-LAB.md) | Authorization and dependency injection |
| 07 | [Guided Lab 07](07-GUIDED-LAB.md) | Unit testing and CI |
| 08 | [Guided Lab 08](08-GUIDED-LAB.md) | Async backpressure and cleanup |
| 09 | [Guided Lab 09](09-GUIDED-LAB.md) | TCP, DNS and TLS |
| 10 | [Guided Lab 10](10-GUIDED-LAB.md) | Object authorization |
| 11 | [Guided Lab 11](11-GUIDED-LAB.md) | HMAC and key management |
| 12 | [Guided Lab 12](12-GUIDED-LAB.md) | SOC rules and quality |
| 13 | [Guided Lab 13](13-GUIDED-LAB.md) | Incident timelines and custody |
| 14 | [Guided Lab 14](14-GUIDED-LAB.md) | Offline PCAP metadata |
| 15 | [Guided Lab 15](15-GUIDED-LAB.md) | Static file triage and intelligence |
| 16 | [Guided Lab 16](16-GUIDED-LAB.md) | Mock cloud posture audits |
| 17 | [Guided Lab 17](17-GUIDED-LAB.md) | Vulnerability triage and local fuzzing |
| 18 | [Guided Lab 18](18-GUIDED-LAB.md) | Mini SOC integration |
| 19 | [Guided Lab 19](19-GUIDED-LAB.md) | Endpoint normalization |
| 20 | [Guided Lab 20](20-GUIDED-LAB.md) | Python performance and caching |
| 21 | [Guided Lab 21](21-GUIDED-LAB.md) | Anomaly metrics and base rates |
| 22 | [Guided Lab 22](22-GUIDED-LAB.md) | Regex and trust boundaries |

## How to finish one lab

1. Read the corresponding [Deep Dive chapter](../course/README.md).
2. Predict result and error cases before running.
3. Copy the snippet to an isolated working directory with the repository on the Python import path.
4. Run code and record actual output in your lab notes.
5. Add at least three independent tests: normal, boundary, malformed input.
6. Explain data trust, memory limits, a false-positive scenario and any assumption you could not verify.
7. Submit source code, tests and a one-page report.

**Rubric:** correctness 4, negative tests 3, security reasoning 2, reproducibility 1. Pass 8/10 plus all mandatory negative tests.

**Continue:** [100 exercise solutions](../solutions/by-exercise/README.md) · [progressive project builds](../projects/BUILD-PATH.md) · [Mini SOC capstone](../course/18-MINI-SOC-CAPSTONE-BLUEPRINT.md).
