# Workshop 04 — Build an evidence timeline with correct UTC handling

**Duration:** 3–5 hours · **Network:** none · **Inputs:** synthetic files only.

## Situation
Your lab has two authentication logs. One uses UTC with `Z`, another uses a local +07:00 offset. Your supervisor wants an ordered incident timeline and a hash manifest. You must avoid changing original evidence.

## 1. Evidence checklist
Before processing:
1. Record authorization and input location.
2. Record source purpose and format.
3. Compute SHA-256 for each input.
4. Record system date/time and acquisition method.
5. Make a separate working copy; preserve originals.
6. Keep each source's original timestamp.
7. Record parse errors without guessing missing data.

## 2. Generate two toy log files
```python
from pathlib import Path
import json

a = [
    {"timestamp": "2026-01-01T10:00:00Z", "actor": "alice", "action": "login_failure"},
    {"timestamp": "2026-01-01T10:02:00Z", "actor": "alice", "action": "login_success"},
]
b = [
    {"timestamp": "2026-01-01T17:01:00+07:00", "actor": "alice", "action": "login_failure"},
]
Path("lab-a.jsonl").write_text(
    "".join(json.dumps(record) + "\n" for record in a), encoding="utf-8"
)
Path("lab-b.jsonl").write_text(
    "".join(json.dumps(record) + "\n" for record in b), encoding="utf-8"
)
```

These are synthetic data, not collected logs.

## 3. Hash the originals
```python
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

for path in (Path("lab-a.jsonl"), Path("lab-b.jsonl")):
    print(path.name, sha256_file(path))
```

**Expected:** two 64-character hex digests; values depend on the exact bytes and line endings. Do not invent the hashes in your report; record the actual observed outputs.

## 4. Parse and normalize
```python
import json
from datetime import datetime, timezone

def normalize_when(value: str):
    if not isinstance(value, str):
        raise ValueError("timestamp must be text")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)

timeline = []
for filename in ("lab-a.jsonl", "lab-b.jsonl"):
    with open(filename, encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            data = json.loads(line)
            timeline.append({
                "utc": normalize_when(data["timestamp"]),
                "original": data["timestamp"],
                "actor": data["actor"],
                "action": data["action"],
                "source": filename,
                "line": line_number,
            })
timeline.sort(key=lambda e: (e["utc"], e["source"], e["line"]))
for event in timeline:
    print(event["utc"].isoformat(), event["actor"],
          event["action"], event["source"], event["line"])
```

**Expected ordering:**
```text
2026-01-01T10:00:00+00:00 alice login_failure lab-a.jsonl 1
2026-01-01T10:01:00+00:00 alice login_failure lab-b.jsonl 1
2026-01-01T10:02:00+00:00 alice login_success lab-a.jsonl 2
```

Why? 17:01:00 at UTC+07:00 represents 10:01 UTC. An incorrect parser might place it seven hours later.

## 5. Interpret carefully
Observation: two failed logins followed by a success occurred in the toy records. You **cannot infer** that an attacker obtained access. Legitimate users may mistype passwords. Source clocks may be wrong or records incomplete.

Questions to ask in a real, authorized incident:
- Was MFA required and satisfied?
- Were IP/device and identity-provider subject consistent with the user?
- Were logs complete and clocks synchronized?
- What activity occurred after the successful login?
- What benign alternate explanations fit the timeline?

## 6. Error experiment

Add a line without a timezone offset or a malformed JSON row to a **copy**. Your parser should reject it rather than assigning a guessed UTC zone. Extend code with line-context exceptions and file size bounds. The reference script is intentionally focused on timestamp learning and not production-hardened.

## 7. Chain-of-custody report template

```text
Case: LAB-001
Collector: student running isolated environment
Source: synthetic, locally created lab-a.jsonl / lab-b.jsonl
Acquisition: working copy after SHA-256
Hash values: <actual observed values>
Collection UTC time: <actual observed value>
Tool version: <actual Python version>
Transformations: strict JSON parse, aware UTC conversion, sorting
Observations: <facts only>
Interpretations: <clearly separate hypotheses>
Limitations: synthetic records, unverified source clocks, small sample
Cleanup: delete temporary generated files and outputs
```

## 8. Exercises / answer checks
1. Why is `ctime` not a universal file creation time? Platform/file system differences.
2. Why retain original strings after normalization? Evidence fidelity and source uncertainty.
3. Why add line numbers? Reproducible evidence tracing.
4. Why keep collection time separate from event time? They represent different moments.
5. Why is a hash not proof of user identity? A digest identifies bytes, not their origin.
6. Create an incident summary with an alternative benign explanation and state confidence.

**Deliverable:** exact command log, observed hashes, UTC timeline, one intentionally rejected timestamp and a concise incident report.
