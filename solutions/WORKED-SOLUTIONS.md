# Worked Solutions — 12 Python for Cybersecurity exercises

**Purpose:** These are complete, explained solutions to representative exercises from the [Second Edition](../course/README.md). They complement rather than replace the larger [100-exercise bank](../reference/100-EXERCISES.md). Try first without looking here. All exercises use local/synthetic data.

## Solution 01 — Strict numeric input (beginner)

**Task:** accept a TCP port from user-supplied *text* without accepting floats, signs, Unicode numeral alternatives or out-of-range values.

```python
def parse_port(raw: str) -> int:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 5:
        raise ValueError("port text must be 1–5 characters")
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError("port must contain ASCII decimal digits")
    value = int(raw)
    if not 1 <= value <= 65535:
        raise ValueError("port out of range")
    return value

assert parse_port("443") == 443
for sample in ("", "0", "65536", "-1", "22.0", "１２３"):
    try:
        parse_port(sample)
    except ValueError:
        pass
    else:
        raise AssertionError(f"unexpectedly accepted {sample!r}")
```

**Why this works:** the checks are ordered type → length → character class → numeric range. The function refuses to guess what malformed input "means." It is validation only; it does not authorize a network connection.

## Solution 02 — Names, aliases and mutable structures

**Task:** explain why a shallow copy is insufficient for nested mutable lists.

```python
from copy import deepcopy
original = [{"actor": "alice", "tags": []}]
shallow = original.copy()
deep = deepcopy(original)
shallow[0]["tags"].append("review")
assert original[0]["tags"] == ["review"]
assert deep[0]["tags"] == []
```

**Why:** `list.copy` creates a new *outer* list, but both lists still reference the same nested dict. `deepcopy` recursively duplicates most nested objects, but may be undesirable for resources/large graphs; design immutable normalized records when possible.

**Security relevance:** shared mutable state can make one analyst's annotations accidentally change another incident's data.

## Solution 03 — Count without retaining raw events

**Task:** count failure actions in a memory-bounded stream of synthetic lines.

```python
from collections import Counter

def failures_by_actor(rows):
    counts = Counter()
    for actor, action in rows:
        if action == "login_failure":
            counts[actor] += 1
    return counts

rows = [
    ("alice", "login_failure"), ("bob", "login_success"),
    ("alice", "login_failure"), ("bob", "login_failure")
]
assert failures_by_actor(rows) == {"alice": 2, "bob": 1}
```

**Complexity:** O(N) time and O(U) memory, U = distinct actors. In real data, U itself must be bounded because attacker-controlled unique actor names can consume memory. The exercise assumes data is already validated.

## Solution 04 — Date-time offsets represent instants

**Task:** show that two timestamps in different zones refer to the same instant.

```python
from datetime import datetime, timezone

first = datetime.fromisoformat("2026-01-01T10:00:00+00:00")
second = datetime.fromisoformat("2026-01-01T17:00:00+07:00")
assert first == second
assert second.astimezone(timezone.utc) == first
```

**Why:** aware datetime objects use UTC offsets for temporal comparison. Keep original timestamp text for evidence; ingest/record time is distinct. A naive datetime lacking timezone must not be silently assigned UTC.

## Solution 05 — Safe parameterized database query

**Task:** ensure an injection-looking string is interpreted only as data.

```python
from contextlib import closing
import sqlite3

with closing(sqlite3.connect(":memory:")) as connection:
    connection.execute("CREATE TABLE user_roles (username TEXT, role TEXT)")
    with connection:
        connection.execute(
            "INSERT INTO user_roles VALUES (?, ?)", ("alice", "reader")
        )
    name = "alice' OR '1'='1"
    roles = connection.execute(
        "SELECT role FROM user_roles WHERE username = ?", (name,)
    ).fetchall()
    assert roles == []
```

**Why:** the placeholder separates SQL code from values. Authorization is a *separate* required check; parameterization does not make a database request legitimate.

## Solution 06 — Explicit object-level access control

**Task:** only the document owner may read a personal document; the auditor may read organization documents under a simplified policy.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    user_id: str
    roles: frozenset[str]

@dataclass(frozen=True)
class Doc:
    owner: str
    classification: str

def may_read(principal: Principal, doc: Doc) -> bool:
    if doc.owner == principal.user_id:
        return True
    return ("auditor" in principal.roles
            and doc.classification == "organization")

alex = Principal("alex", frozenset({"reader"}))
pat = Principal("pat", frozenset({"reader"}))
doc = Doc(owner="alex", classification="personal")
assert may_read(alex, doc)
assert not may_read(pat, doc)
```

**Why:** authentication establishes the caller; authorization checks the caller against *this resource*. A real system must derive `Principal` from verified identity, not user-supplied JSON.

## Solution 07 — Stream a bounded line with visible errors

**Task:** reject oversized byte lines before decoding, preserving line number.

```python
from pathlib import Path

def strict_lines(path: Path, cap: int = 1024):
    if cap < 1:
        raise ValueError("invalid cap")
    with path.open("rb") as source:
        for number, raw in enumerate(
            iter(lambda: source.readline(cap + 1), b""), 1
        ):
            if len(raw) > cap:
                raise ValueError(f"line {number}: size cap exceeded")
            try:
                yield number, raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise ValueError(f"line {number}: bad encoding") from exc
```

**Why:** reading with an explicit max protects against a single extremely long line. The last line may lack a terminating newline and can still be accepted if below cap. A higher-level parser still must validate schema and size.

## Solution 08 — Hash integrity and evidence limits

**Task:** hash a file using bounded memory.

```python
from hashlib import sha256
from pathlib import Path

def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()
```

**Why:** hashing processes exact bytes in chunks. A trusted previous digest makes a useful comparison; a hash by itself does not establish who created a file. This is not forensic-grade acquisition against mutable/adversarial filesystems.

## Solution 09 — AEAD integrity failure (optional dependency)

**Task:** prove that a different associated-data context fails verification.

```python
# requires cryptography from a trusted source
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
aead = AESGCM(key)
ciphertext = aead.encrypt(nonce, b"toy note", b"tenant=A")

assert aead.decrypt(nonce, ciphertext, b"tenant=A") == b"toy note"
try:
    aead.decrypt(nonce, ciphertext, b"tenant=B")
except InvalidTag:
    pass
else:
    raise AssertionError("tampered context was accepted")
```

**Why:** AEAD authenticates ciphertext and associated data. Nonces must never repeat with the same key. Production requires robust key/nonce management and access policy.

## Solution 10 — Confusion matrix and alert quality

**Task:** evaluate toy detector performance.

```python
def evaluate(tp: int, fp: int, fn: int, tn: int):
    counts = (tp, fp, fn, tn)
    if any(type(x) is not int or x < 0 for x in counts):
        raise ValueError("counts must be nonnegative integers")
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * tp / (2 * tp + fp + fn)
          if 2 * tp + fp + fn else None)
    return precision, recall, f1

assert evaluate(15, 5, 5, 95) == (0.75, 0.75, 0.75)
```

**Why:** a classifier's alert count alone tells little about quality. Here undefined metrics return `None` rather than a fabricated zero. False positives carry analyst cost; false negatives carry missed incidents. Ground-truth labeling and dataset composition matter.

## Solution 11 — Immutable policy configuration

**Task:** reject invalid operational limits and treat booleans differently from integers.

```python
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Settings:
    max_items: int = 1000
    timeout_seconds: float = 3.0

    def __post_init__(self):
        if type(self.max_items) is not int or not 1 <= self.max_items <= 100_000:
            raise ValueError("max_items invalid")
        if type(self.timeout_seconds) not in (int, float):
            raise ValueError("timeout type invalid")
        if not isfinite(self.timeout_seconds) or not 0 < self.timeout_seconds <= 30:
            raise ValueError("timeout range invalid")

assert Settings().max_items == 1000
for kwargs in ({"max_items": True}, {"max_items": 0},
               {"timeout_seconds": float("nan")}):
    try:
        Settings(**kwargs)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid settings accepted")
```

**Why:** `NaN` and infinities defeat naive float range assumptions; bool is a subclass of int; frozen dataclasses reduce accidental configuration mutation but do not deeply freeze nested data.

## Solution 12 — Local sliding-window threshold

**Task:** emit one review candidate when a third failure occurs in a rolling 60-second window.

```python
from collections import deque

def crossings(times: list[int], *, threshold: int = 3, span: int = 60):
    if threshold < 1 or span < 1:
        raise ValueError("threshold and span must be positive")
    if times != sorted(times):
        raise ValueError("events must be sorted")
    q = deque()
    active = False
    alerts = []
    for t in times:
        while q and t - q[0] > span:
            q.popleft()
        q.append(t)
        if len(q) < threshold:
            active = False
        if len(q) >= threshold and not active:
            alerts.append(t)
            active = True
    return alerts

assert crossings([0, 30, 60, 121, 130, 140]) == [60, 140]
```

**Trace:** at t=60, [0,30,60] triggers. At t=121 the old times expire and the rule rearms. At t=140, [121,130,140] triggers again. This is a pure toy; production needs event IDs, actor grouping, late arrivals, memory caps, privacy and evidence provenance.

## Beyond these answers

Finish the [four guided workshops](../course/README.md#fully-guided-workshops-and-checked-code) and write independent solutions for the 100 exercises. An answer is only complete when you can explain the contract, trade-offs, testing, safety and what the result does **not** prove.
