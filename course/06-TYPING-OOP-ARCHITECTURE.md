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


## 10. A fully traceable detection engine: interfaces and unit-test doubles

Your goal: replace a one-file script that reads logs, calculates risk, writes to a database and posts alerts, with a design whose **decision logic is pure** and whose side effects are independently testable.

### Design first: input, output, and responsibility

| Layer | Input | Output | Side effects allowed |
|---|---|---|---|
| Reader | path / approved API | raw records | file/network read |
| Validator | raw record | verified `AuthEvent` | none |
| Rule | verified event | `Finding` or `None` | none |
| Storage | finding | confirmation/status | database write |
| Presenter | findings | redacted report | stdout/file |

The rule should never directly disable a user or call an external service. The data model can state invariants that the validator must actually enforce at runtime.

### Reference design with a test double

```python
from dataclasses import dataclass
from typing import Protocol, Iterable

@dataclass(frozen=True)
class AuthEvent:
    event_id: str
    actor: str
    action: str

@dataclass(frozen=True)
class Finding:
    event_id: str
    description: str

class ReadPort(Protocol):
    def read(self) -> Iterable[AuthEvent]: ...

class WritePort(Protocol):
    def save(self, finding: Finding) -> None: ...

class FailureRule:
    def evaluate(self, event: AuthEvent) -> Finding | None:
        if event.action == "login_failure":
            return Finding(event.event_id, "failed login observed")
        return None

class DetectionService:
    def __init__(self, reader: ReadPort, writer: WritePort):
        self.reader = reader
        self.writer = writer
        self.rule = FailureRule()

    def run(self) -> int:
        count = 0
        for event in self.reader.read():
            finding = self.rule.evaluate(event)
            if finding is not None:
                self.writer.save(finding)
                count += 1
        return count

class FakeReader:
    def read(self):
        yield AuthEvent("e1", "alex", "login_failure")
        yield AuthEvent("e2", "alex", "login_success")

class FakeWriter:
    def __init__(self):
        self.saved = []
    def save(self, finding):
        self.saved.append(finding)

writer = FakeWriter()
assert DetectionService(FakeReader(), writer).run() == 1
assert writer.saved[0].event_id == "e1"
```

**Why this architecture matters:** A unit test can reproduce the scenario without files, cloud access or secrets. A broken storage adapter does not change rule logic. In production, however, you still need a transactional delivery contract: if `writer.save` fails after several successful writes, your program must record *partial completion*. This example does not provide exactly-once delivery.

## 11. The hidden danger in type hints

A `Protocol` describes what methods an object should implement to a type checker. At runtime, another object might still return malicious or malformed data. A `dataclass(frozen=True)` documents immutability but does not validate values on construction and does not freeze mutable nested objects.

### Trust boundary placement
- Network payload → runtime validator → `AuthEvent`.
- Internal rule → typed `Finding` → output schema validator.
- Persistent storage → schema/permissions checks before rendering.
- Vendor SDK → validate responses despite "trusted" source.

A safe architecture never assumes "it has a Python type annotation, therefore it is safe."

## 12. Exercise: failure semantics and testing

1. **Break the sink:** make `FakeWriter.save` raise on its second call. Describe which findings were persisted and why "0 findings" would be misleading.
2. **Make rules pluggable:** inject a `Rule` protocol instead of constructing `FailureRule` inside `DetectionService`. Test with a `AlwaysNoneRule` and an `AlwaysFindingRule`.
3. **Add validation:** create a factory that verifies event ID (1–64 chars), actor (1–128) and action membership before building `AuthEvent`.
4. **Test import safety:** ensure importing the module does not contact the network or write files.
5. **Discuss transactions:** should findings be written all-or-nothing per batch? Describe SQLite transaction use and when streaming partial processing is acceptable.

**Answer guide:** (1) one record may already be saved; a thrown exception does not roll back other systems; (2) composition lets tests substitute behavior; (3) type hints alone are insufficient; (5) choose atomicity explicitly according to operational requirements.

**Architecture quality gate:** draw where authentication, authorization, validation, retention and audit checks occur. If none of these has a clear owner, the design isn't ready for a real security workload.
