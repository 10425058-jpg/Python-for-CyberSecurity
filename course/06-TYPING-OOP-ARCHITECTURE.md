# Deep Dive 06 — Typing, OOP, dependency injection and designing security software

**Level:** intermediate · **Estimated study:** 8–10 hours.

## Why architecture matters in cybersecurity

A 50-line script can be easy to inspect. A 5,000-line security tool needs understandable contracts so that a failed parser cannot unexpectedly mutate a database and a compromised enrichment API cannot trigger high-impact actions. Your design should make **trust boundaries and side effects visible**.

## 1. Types: static guidance versus runtime enforcement

`list[str]`, `dict[str, int]`, `Literal`, `Protocol`, `TypedDict`, `Callable` and generics improve communication and editor tooling. Type annotations are *not* runtime validators. When untrusted data enters the system, validate explicitly.

```python
from dataclasses import dataclass
from typing import Literal

Severity = Literal["info", "low", "medium", "high"]

@dataclass(frozen=True)
class Finding:
    event_id: str
    severity: Severity
    reason: str

def parse_finding(data: dict) -> Finding:
    if not isinstance(data, dict) or set(data) != {"event_id", "severity", "reason"}:
        raise ValueError("invalid finding fields")
    if data["severity"] not in ("info", "low", "medium", "high"):
        raise ValueError("unsupported severity")
    if not isinstance(data["event_id"], str) or not data["event_id"]:
        raise ValueError("invalid ID")
    if not isinstance(data["reason"], str) or len(data["reason"]) > 500:
        raise ValueError("invalid reason")
    return Finding(**data)
```

Check exact types when booleans might be mistaken for integers. For complex nested validation, use a maintained schema library and still set resource limits.

## 2. Composition over deep inheritance

Object-oriented design allows behavior to live alongside state. **Composition** means a detector *has* a parser, a clock and a repository; it does not need to subclass ten base classes.

```python
from typing import Protocol, Iterable

class EventSource(Protocol):
    def fetch(self) -> Iterable[dict]: ...

class OutputSink(Protocol):
    def write(self, finding: Finding) -> None: ...

class DetectionRule(Protocol):
    def evaluate(self, event: dict) -> Finding | None: ...

class DetectionService:
    def __init__(self, source: EventSource, sink: OutputSink, rule: DetectionRule):
        self.source, self.sink, self.rule = source, sink, rule

    def run(self):
        for event in self.source.fetch():
            finding = self.rule.evaluate(event)
            if finding is not None:
                self.sink.write(finding)
```

The protocol defines expected behavior without forcing inheritance. A test can substitute a memory-based source/sink, avoiding network and filesystem access.

## 3. Dependency injection for testability

A global variable such as `API_CLIENT = connect_to_prod()` inside a module is difficult to test and makes import unsafe. Prefer passing a client object to the constructor/function. For clock-dependent rules, inject a time provider rather than calling `datetime.now()` deep inside the rule.

```python
class MemorySource:
    def __init__(self, events):
        self.events = list(events)
    def fetch(self):
        return iter(self.events)

class MemorySink:
    def __init__(self):
        self.findings = []
    def write(self, finding):
        self.findings.append(finding)
```

You can now unit test `DetectionService` without even importing a cloud SDK. This does not automatically mean the live integration is correct; still write integration tests with safe test accounts.

## 4. Layered architecture with trust boundaries

A simple modular design:
```text
CLI / HTTP adapter
   ↓ raw, untrusted input
Validation and normalization layer
   ↓ verified domain objects
Pure detection logic
   ↓ findings (no high-impact actions)
Reporting and persistence adapters
   ↓ audited output
Human response decision
```

### Responsibilities
- **CLI:** parse flags, select files, return exit codes, no security decisions.
- **Parser:** JSON, CSV, PCAP or raw evidence into bounded structures.
- **Validator:** enforce schema and permitted values.
- **Domain:** detection policies, risk scoring, alert object creation.
- **Repository:** persistence behind an interface; parameterize queries.
- **Adapters:** make authorized API calls with timeouts and least privilege.
- **Presenter:** emit logs/reports while redacting sensitive fields.

A design smell: the same function opens a production database, parses a log, decides an alert severity, disables a user account and prints a success banner. Split observations from remediation.

## 5. Exception and retry policies by layer

A parser should raise a clear parse error. A repository adapter may translate a network/database timeout into a retriable operational error. A CLI turns failures into a nonzero exit status and sanitized diagnostic. Do not catch `Exception` everywhere and return empty data.

Distinguish transient failures (e.g. 503, temporary lock) from permanent validation failures (malformed record). Retry only safe/idempotent operations and apply bounded exponential backoff; retries must have a global budget and jitter when used across many clients.

## 6. SOLID as guidance, not ceremony
- Single Responsibility: each unit has one reason to change.
- Open/Closed: new rules should not require editing the ingestion pipeline.
- Liskov substitution: adapters honor the same contract.
- Interface Segregation: small, purpose-specific protocols.
- Dependency Inversion: core domain logic depends on interfaces, not vendor SDKs.

Overengineering is also harmful. A 20-line one-off analysis does not need a plugin system. Expand architecture when complexity or risk justifies it.

## 7. Configuration and security defaults

Use environment variables or deployment configuration for endpoints and non-secret options, secret managers for credentials, and explicit versions for schemas. Configuration itself may be untrusted. Separate permissions: inventory read-only identity should not be able to remediate infrastructure.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    max_records: int = 100_000
    timeout_seconds: float = 3.0

    def __post_init__(self):
        if type(self.max_records) is not int or not 1 <= self.max_records <= 1_000_000:
            raise ValueError("max_records out of range")
        if type(self.timeout_seconds) not in (int, float) or not 0 < self.timeout_seconds <= 30:
            raise ValueError("timeout out of range")
```

This illustrates configuration validation; for stricter deployments also reject NaN/infinity and ensure values are finite.

## 8. Worked exercise: add an independent rule

Implement `FailedLoginRule`:
- Accept a validated event.
- Return `Finding(event_id=..., severity="low", reason="login failure observed")` on `login_failure`.
- Return `None` otherwise.
- Never call network APIs or mutate external accounts.
- Test with `MemorySource` and `MemorySink`.

**Answer sketch:**
```python
class FailedLoginRule:
    def evaluate(self, event: dict) -> Finding | None:
        if event.get("action") != "login_failure":
            return None
        return Finding(str(event["event_id"]), "low", "login failure observed")
```

This rule assumes `event_id` and `action` were already validated. If exposed directly to untrusted input, validate internally or make the validated event type part of the interface.

## 9. Review checklist
- No import-time network/file writes.
- Domain rules contain no hidden side effects.
- All untrusted data validated at its boundary.
- Clock, API clients and repositories can be substituted in tests.
- Configuration and secrets separated.
- Retries are bounded; writes are authorized.
- Alerts are evidence-based and never silently trigger high-impact actions.

**Reading:** [typing](https://docs.python.org/3/library/typing.html), [dataclasses](https://docs.python.org/3/library/dataclasses.html), [dependency injection discussion (Python guide)](https://docs.python-guide.org/writing/structure/).
