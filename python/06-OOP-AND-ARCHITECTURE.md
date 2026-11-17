# 06 — Object-oriented design and maintainable security tools
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [typing oop architecture](../course/06-TYPING-OOP-ARCHITECTURE.md).



## Extended textbook 06 — Objects, state and composition without unnecessary complexity

### 6.1 What classes solve

A **class** defines behavior and typically state; an **instance** is one concrete object. `__init__` initializes an instance; `self` is the instance passed to instance methods. Attribute lookup finds an instance attribute, class attribute or descriptor according to Python's rules. **Encapsulation** is designing a narrow interface and maintaining invariants; an underscore prefix (`_internal`) is a convention, **not** protection against malicious callers.

A **dataclass** is convenient for domain records because it generates common methods. `@dataclass(frozen=True)` prevents ordinary field reassignment but does not make nested containers immutable and does not validate type annotations. You still need a boundary validator before creating an object that your security policy trusts.

### 6.2 Prefer composition to deep inheritance

Suppose a monitoring service has a parser, a rule engine and an output sink. Inheritance such as `SecureServiceWithFileAndDatabaseAndHTTP` mixes unrelated concerns. **Composition** allows you to combine independent parts. A `Protocol` describes the methods a component must provide for static type checking. A fake implementation lets your tests run without network/database access.

| Concept | Practical purpose | Common misuse |
|---|---|---|
| constructor | initialize instance state | silently performing network connections |
| instance method | behavior based on an object | changing shared class attributes |
| inheritance | substitute one subtype for another | deep fragile hierarchies |
| composition | assemble components | hidden global dependencies |
| polymorphism | allow interchangeable implementations | assuming any implementation is trusted |
| frozen dataclass | represent normalized data | assuming runtime typing/deep immutability |
| Protocol | define expected interface | assuming enforcement of authorization |

### 6.3 Build a miniature policy service through composition

```python
# TEXTBOOK_RUNNABLE
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    rights: frozenset[str]

@dataclass(frozen=True)
class Report:
    report_id: str
    tenant: str
    owner: str

class ReportStore(Protocol):
    def find(self, report_id: str) -> Report | None: ...

class InMemoryStore:
    def __init__(self, reports: dict[str, Report]):
        self._reports = dict(reports)
    def find(self, report_id: str) -> Report | None:
        return self._reports.get(report_id)

class ReportService:
    def __init__(self, store: ReportStore):
        self._store = store
    def read(self, principal: Principal, report_id: str) -> Report | None:
        if type(report_id) is not str or not 1 <= len(report_id) <= 64:
            raise ValueError("invalid report id")
        record = self._store.find(report_id)
        if record is None:
            return None
        allowed = (
            principal.tenant == record.tenant
            and principal.subject == record.owner
            and "report:read-own" in principal.rights
        )
        return record if allowed else None

service = ReportService(InMemoryStore({
    "case-1": Report("case-1", "A", "alice")
}))
alice = Principal("alice", "A", frozenset({"report:read-own"}))
outsider = Principal("alice", "B", frozenset({"report:read-own"}))
assert service.read(alice, "case-1") is not None
assert service.read(outsider, "case-1") is None
assert service.read(alice, "missing") is None
print("LAB 06 PASS")
```

**Step 1:** `Principal` is an authenticated identity *in the application's assumed model*; it is not generated from raw caller JSON. **Step 2:** `Report` stores resource ownership metadata; the store is assumed authoritative. **Step 3:** `ReportStore` is an interface, not a database. **Step 4:** `InMemoryStore` isolates our tests from I/O. **Step 5:** `ReportService` checks the tenant, owner and specific permission, refusing the cross-tenant request. This code does not authenticate sessions or protect a production database—it tests one narrow decision under its stated assumptions.

### 6.4 State, inheritance, and surprising aliasing

Instance attributes are typically created with `self.x = ...`. A mutable class attribute such as `records = []` is shared across instances unless overridden; allocate a new list in each constructor. Inheritance should respect substitution: if a child class changes a method's return type or narrows valid inputs unexpectedly, callers may break. Use abstract base classes or Protocols sparingly; complexity does not automatically equal safety.

**Advanced pattern:** prefer an immutable event model, a pure detection rule, a separate database adapter, a separate CLI adapter, and a dedicated human-approved remediation component. It becomes straightforward to test authorization and error propagation without accidentally changing real systems.

### 6.5 Architecture and failure diagrams

```text
untrusted JSON bytes
    ↓ strict parser / schema validator
validated domain object  ← provenance and time limitations
    ↓ pure rule/policy
review candidate
    ↓ authorized sink adapter
staged report / database
    ↓
analyst review (not automatic containment)
```

Which layers perform I/O? Which failure causes `complete=False`? Where would a second output sink be installed without changing core policy? A good architecture answers all three clearly.

### 6.6 Graded exercises

**Beginner:** Create two instances with independent lists and demonstrate why class-level mutable defaults are dangerous. **Intermediate:** Add an auditor role that may read organization-level reports but not private reports or other tenants. Write a denial test. **Advanced:** Replace `InMemoryStore` with a toy SQLite adapter while keeping `ReportService` unchanged; simulate a storage error and ensure it cannot result in unauthorized access.

**Mastery gate:** you can explain class vs instance, constructor, `self`, composition vs inheritance, why annotations are not runtime checks, and how to isolate security decisions from side effects.

## Core concepts
- **Class:** declares a type's data and behavior; **instance:** concrete object.
- **Encapsulation:** expose a small stable interface; underscore is a convention, not access control.
- **Composition:** build behavior from collaborating objects; often preferable to deep inheritance.
- **Inheritance:** subclass when substitution really holds; override behavior carefully.
- **Polymorphism:** multiple implementations behind a common interface or `Protocol`.
- **Dataclass:** concise data models; `frozen=True` discourages accidental updates but nested mutable fields can still change.

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Event:
    actor: str
    action: str

class Rule(Protocol):
    def matches(self, event: Event) -> bool: ...

class FailedLoginRule:
    def matches(self, event: Event) -> bool:
        return event.action == "login_failure"

def evaluate(rule: Rule, events: list[Event]) -> list[Event]:
    return [event for event in events if rule.matches(event)]
```

## Architecture patterns
- Ports and adapters: keep the analysis core independent of storage vendors.
- Strategy: interchangeable detection rules.
- Repository: abstract persistence behind a narrow interface.
- Dependency injection: pass clock, client, filesystem adapter, config, and logger to test without real systems.
- Observer/event bus: notify consumers without coupling every component.
- Command: package repeatable actions with explicit arguments and outcomes.

## Abuse-resistant engineering
Define resource budgets, timeouts, cancellation and retry policy. Operations that mutate security controls must be explicitly authorized and idempotent when possible. Document rollback and audit trails. Avoid plugin systems that import arbitrary code from untrusted paths.

## Exercises
1. Add a second detection rule implementing `Rule`.
2. Replace a live API client with an in-memory test double.
3. Draw dependencies for a file-ingest → normalize → detect → report application.
4. Refactor a 500-line script into CLI, parser, domain logic and output modules.
