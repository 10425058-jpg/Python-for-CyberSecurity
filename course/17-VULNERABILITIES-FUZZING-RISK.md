# Deep Dive 17 — Vulnerability management, risk and Python parser fuzzing

**Level:** intermediate → advanced · **Estimated study:** 12–16 hours.

## 1. Severity is not the same as organizational risk

A vulnerability may have a high CVSS score but be unreachable in your deployment. Another issue may have a lower score yet affect an Internet-facing critical system. Prioritization should consider:
- Affected software and exact version.
- Whether it is actually deployed and reachable.
- Exposure, privilege requirements and mitigating controls.
- Evidence of active exploitation, exploitability and impact.
- Business criticality and data sensitivity.
- Patch availability, operational constraints and compensating controls.
- Residual risk and owner approval.

Avoid treating a scanner finding as authoritative without confirming applicability.

## 2. CVE, CVSS, SBOM, VEX and advisories

- **CVE:** common identifier for a disclosed vulnerability.
- **CVSS:** standardized severity scoring methodology, with version-specific scoring semantics.
- **SBOM:** list of software components and dependencies in a product.
- **VEX:** machine-readable assertions about vulnerability applicability/exploitability in a product context.
- **Advisory:** vendor/project communication about impact, affected versions and remediation.

A Python dependency audit tool helps compare installed package versions with known advisories. It cannot guarantee the absence of undisclosed vulnerabilities and may not capture unusual packaging configurations.

## 3. Normalizing synthetic findings

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Advisory:
    advisory_id: str
    package: str
    installed_version: str
    fixed_version: str | None
    exposed: bool

def prioritize(advisory: Advisory) -> str:
    if advisory.exposed and advisory.fixed_version is not None:
        return "investigate and plan upgrade"
    if advisory.exposed:
        return "investigate mitigation or exception"
    return "validate impact and track"
```

This example intentionally avoids pretending to compute a universal risk number. A serious program should use approved business context and record each decision's rationale.

## 4. Fuzzing means testing robustness with diverse inputs

Fuzzing supplies many generated or mutated inputs to a **program you own** and checks whether it crashes, hangs or violates expected properties. It is valuable for parsers of logs, binary formats and API payloads. It is not permission to flood a public endpoint.

### Parser under test
```python
def parse_unsigned_port(raw: str) -> int:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 5:
        raise ValueError("invalid length/type")
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError("invalid decimal")
    number = int(raw)
    if not 1 <= number <= 65535:
        raise ValueError("out of range")
    return number
```

Properties:
- Valid outputs are always in [1,65535].
- Input other than ASCII decimal digits is rejected.
- Inputs longer than five characters are rejected without expensive processing.
- The parser has no filesystem/network side effects.
- Malformed input causes a *documented* exception, not a crash/loop.

### Deterministic local input generator
```python
import random
import string

rng = random.Random(2026)
alphabet = string.ascii_letters + string.digits + " -_"
for _ in range(1_000):
    text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(12)))
    try:
        value = parse_unsigned_port(text)
        assert 1 <= value <= 65535
    except ValueError:
        pass
```

This covers random cases but does not prove correctness. Add systematic boundary cases and a property-based tool like Hypothesis for better generation/shrinking. Use `secrets` for production credentials; `random` is correct for reproducible *tests*.

## 5. Memory/time DoS in apparently safe parsers

Parser bugs are not limited to code execution. Consider:
- Huge JSON arrays or nesting, causing memory/recursion limits.
- Very long strings passed through catastrophic-backtracking regex patterns.
- ZIP archives with enormous decompressed size.
- Unbounded distinct user IDs in a dictionary.
- Repeated retries and high task concurrency.
- File formats that declare absurd lengths.
- Sort-and-group operations over attacker-controlled giant datasets.

Defenses: byte caps **before** decoding, nesting/depth limits, finite timeouts, bounded queues, measured profiling, isolation and error reporting. The appropriate caps depend on expected workload.

## 6. Regex DoS at a conceptual level

Some regexes with nested ambiguous repetition may take extremely long on crafted long strings. Prefer unambiguous patterns, input limits and simpler parsers where possible. For complex user-controlled patterns, use a safe regex engine or treat the feature as high-risk. Do not accept arbitrary remote regexes on a production log search endpoint without resource controls.

## 7. Triage and remediation workflow

```text
inventory → advisory ingestion → affected-version check
    ↓
exposure and business-context validation
    ↓
prioritize → assign owner and deadline
    ↓
patch / mitigate / approved exception
    ↓
test deployed fix → record evidence
    ↓
monitor and re-evaluate
```

Write the findings so an engineer can reproduce the affected-version check and the mitigation, not just see a severity color.

## 8. Responsible disclosure

Only test within authorization. If you discover a real vulnerability, document sufficient non-destructive evidence, contact the designated security channel privately, agree on coordination, and avoid exposing user data or deploying disruptive proof-of-concepts.

## 9. Lab: toy parser stress test
1. Implement `parse_unsigned_port` above.
2. Test `"1"`, `"65535"`, `"0"`, `"65536"`, `"-1"`, `"22.0"`, `""`, `"123456"`, `True` and `None`.
3. Run 1,000 reproducible random generated strings.
4. Measure runtime and errors; add assertions for all valid outputs.
5. Extend to your [toy binary frame parser](04-BYTES-ENCODING-BINARY-PARSERS.md).
6. Record crash/hang observations (if none, say none) and limits.
7. Propose a fix based on an observed failure or explicitly document no defects found.

## 10. Questions and checks
- Why does a high CVSS score not automatically mean emergency patching in every organization?
- How do you verify whether a given dependency advisory affects your installed version?
- Why can a parser be dangerous without any `eval` or shell calls?
- What does "reproducible test case" mean?
- Why does "1000 fuzz cases passed" not mean "all inputs safe"?

**References:** [CVE Program](https://www.cve.org/), [FIRST CVSS](https://www.first.org/cvss/), [Hypothesis](https://hypothesis.readthedocs.io/).
