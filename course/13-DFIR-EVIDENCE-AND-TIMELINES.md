# Deep Dive 13 — Digital forensics and incident response with Python

> **Hands-on:** [Chapter 13 Guided Lab](../lab-manual/13-GUIDED-LAB.md) · [100 worked answers](../solutions/by-exercise/README.md). Run negative tests and document limitations.

**Level:** intermediate → advanced · **Estimated study:** 14–20 hours.

## Mission
An administrator reports a suspicious account sign-in on a lab VM. You are asked to create a *defensible timeline* from synthetic authentication logs and read-only file metadata. The goal is not to "prove" compromise immediately, but to preserve evidence, explain uncertainty and support an authorized response.

## 1. What DFIR does

**Digital forensics** applies disciplined acquisition, preservation, examination, analysis and reporting of digital evidence. **Incident response** coordinates detection, triage, containment, eradication, recovery and improvement within an organization's risk framework. The current NIST SP 800-61 Rev. 3 (April 2025) aligns incident response recommendations with the NIST Cybersecurity Framework 2.0 rather than treating response as an isolated linear checklist.

Python helps automate **repeatable** steps; it is not a replacement for validated forensic acquisition tools, legal authority, documented procedures or analyst judgment.

## 2. Evidence integrity: hash, source, and custody are different

A SHA-256 digest is a compact fingerprint of bytes. If two files have the same digest under trusted tooling, that supports a byte-for-byte integrity comparison to high confidence, but neither digest alone proves who created a file nor whether it is authentic.

**Chain of custody** records who collected/handled evidence, when, from where, how, and under what authority. Evidence also needs scope, collection tool/version, storage permissions and source-time interpretation.

```python
from pathlib import Path
import hashlib

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()
```

**Walkthrough:** create a digest object; read at most 1 MiB each iteration; update it with exact bytes; produce a hexadecimal digest. This uses bounded process memory even for very large files. Beware files changing while read, symlink races, network filesystems and inaccessible content.

### Example evidence manifest

```json
{
  "evidence_id": "LAB-2026-001",
  "source": "isolated-lab-vm/auth.jsonl",
  "sha256": "compute-from-your-actual-file",
  "collection_time_utc": "2026-01-01T11:00:00Z",
  "collector_role": "lab-analyst",
  "acquisition_method": "read-only copy from lab snapshot",
  "tool": "Python hashlib",
  "notes": "synthetic data; not a legal forensic acquisition"
}
```

Don't put real personally identifying evidence in a public GitHub repo.

## 3. Volatile and nonvolatile evidence

- **Volatile:** running processes, sockets, memory, temporary credentials and kernel state, which can disappear at shutdown.
- **Nonvolatile:** disk files, registry hives, saved logs and persistent configuration, though mutable.
- **Remote/cloud:** audit API data whose retention, identity, and clocks depend on a vendor.
- **Network:** PCAP/flow data that may be partial or encrypted.

Collection changes the machine; even running a benign command can update timestamps and logs. Prioritize actions according to incident response policy and acquisition risk.

## 4. Time is deceptively difficult

Consider:
- 10:00 UTC in one log.
- 17:00 at +07:00 in another log.
- An ingest timestamp at 10:05 UTC for the same event.
All may refer to the same activity or to different events.

```python
from datetime import datetime, timezone
a = datetime.fromisoformat("2026-01-01T10:00:00+00:00")
b = datetime.fromisoformat("2026-01-01T17:00:00+07:00")
assert a == b
assert a.astimezone(timezone.utc) == b.astimezone(timezone.utc)
```

**Do not assume** a timestamp without offset is UTC. It may be local, server or unspecified time; record assumptions and uncertainty.

### Filesystem timestamps
- `mtime`: content-modification time in common filesystems.
- `ctime`: metadata-change time on Unix-like systems, historically file creation on Windows; platform-dependent.
- Birth/creation time may be unavailable, unreliable or represented differently.
- Timestamps can be manipulated; synchronize clocks for legitimate collection, and avoid treating metadata as indisputable history.

## 5. Constructing a timeline

A normalized timeline row might include:
```json
{
  "event_time_utc": "2026-01-01T10:00:00+00:00",
  "time_source": "original_timestamp",
  "source": "lab-auth.jsonl",
  "source_line": 5,
  "actor": "alice",
  "action": "login_failure",
  "confidence": "source-stated",
  "raw_reference": "file-sha256:...:line-5"
}
```

Sorting such rows by event time gives a chronological view. But when clocks are skewed or records arrive late, ordering may not reflect causal sequence. Distinguish an *observed timestamp* from a conclusion about what happened.

## 6. Worked timeline builder (synthetic in-memory data)

```python
from datetime import datetime, timezone

def event_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be text")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("timezone required")
    return dt.astimezone(timezone.utc)

def make_timeline(records):
    staged = []
    for number, record in enumerate(records, 1):
        timestamp = event_time(record["timestamp"])
        staged.append({
            "time": timestamp, "line": number,
            "actor": record["actor"], "action": record["action"],
        })
    return sorted(staged, key=lambda item: (item["time"], item["line"]))

synthetic = [
    {"timestamp":"2026-01-01T17:01:00+07:00","actor":"alice","action":"login_success"},
    {"timestamp":"2026-01-01T10:00:00Z","actor":"alice","action":"login_failure"}
]
timeline = make_timeline(synthetic)
assert timeline[0]["action"] == "login_failure"
```

This is a teaching example. A real version must validate missing keys, field lengths, provenance, stable sorting across sources, output size, duplicates and source-specific clocks.

## 7. Correlation versus causation

A suspicious process launched two minutes after a login does not prove that login caused it. An account may be shared, local clock could be wrong, monitoring can be incomplete, and an attacker may insert misleading events. Support conclusions with multiple independent artifacts and clearly distinguish:
- **Observed fact:** event record states X.
- **Interpretation:** X is consistent with an unauthorized login.
- **Alternative hypothesis:** maintenance or legitimate user action also fits.
- **Confidence:** low/medium/high with stated evidence and limitations.

## 8. Response actions require authorization

An analyst may recommend account session revocation, password reset, network isolation or system reimaging. Performing them can disrupt users and destroy evidence. Use an organization-approved escalation path, decision-maker, containment playbook, rollback and audit trail. Python automation should default to *observation*; high-impact changes need explicit approvals and safe rollback.

## 9. Structured incident report template

```text
Case ID:
Scope and authorization:
Executive summary:
Systems, accounts and data potentially affected:
Timeline (UTC, source pointer, uncertainty):
Collection notes and evidence hashes:
Observed facts:
Assessment and alternative explanations:
Impact and current risk:
Containment/recovery actions (owner + approval + time):
Recommended improvements:
Open questions and confidence:
```

A report written for executives should say what decision is needed; technical appendices should allow another analyst to reproduce your observations.

## 10. Lab: evidence manifest and incident timeline

1. Use the existing `fixtures/synthetic-auth.jsonl`.
2. Make a copy in a dedicated lab directory; do not modify the source.
3. Compute SHA-256 for original and copy, record file sizes and UTC collection time.
4. Parse events, normalize time zones, and preserve source line numbers.
5. Add a synthetic event with +07:00 offset and confirm equivalent UTC ordering.
6. Write a timeline with the source's original timestamp beside normalized UTC.
7. Add a malformed event and demonstrate a visible, nonzero error status.
8. Complete an analyst report documenting uncertainty and alternatives.

**Success criteria:** another person can reproduce hashes, timeline, assumptions and test results from your written instructions.

## 11. Questions and answer checks

**Q:** Why should analysts hash the source and derived outputs? **A:** To demonstrate which bytes were acquired and whether copies/outputs changed; hashes do not prove original truthfulness.

**Q:** Is `ctime` always creation time? **A:** No, semantics differ by platform/filesystem.

**Q:** Why not use a production log as a public test fixture? **A:** Potential personal data, credentials and confidential operational details.

**Q:** How can Python "contaminate" an investigation? **A:** Writes, access/metadata side effects, fragile parsers, mislabeled time zones or evidence transformation without provenance.

**Q:** How does NIST Rev. 3 differ from a rigid sequential incident life-cycle depiction? **A:** It integrates incident response into broader risk governance and CSF functions, with organizational preparation and improvement as ongoing work.

**References:** [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), [Python hashlib](https://docs.python.org/3/library/hashlib.html), [Python datetime](https://docs.python.org/3/library/datetime.html).


## 12. Full DFIR exercise: preserve, normalize and explain a three-event timeline

You receive two **synthetic** logs collected from an isolated VM. One uses UTC; one uses UTC+07:00. An analyst asks whether a successful login happened after two failures.

The question is deceptively simple: event timestamps are source claims, not automatically authoritative facts. An incident conclusion should also document clock synchronization, collection provenance and alternative benign explanations.

### The input

```text
source-a.jsonl: {"timestamp":"2026-01-01T10:00:00Z","event_id":"a1","actor":"alex","action":"login_failure"}
source-b.jsonl: {"timestamp":"2026-01-01T17:01:00+07:00","event_id":"b1","actor":"alex","action":"login_failure"}
source-a.jsonl: {"timestamp":"2026-01-01T10:02:00Z","event_id":"a2","actor":"alex","action":"login_success"}
```

The correct UTC order is 10:00 failure → 10:01 failure → 10:02 success. This **does not prove** that an attacker signed in. A legitimate user might have typed the wrong password twice.

### Minimal verified transformation

```python
from datetime import datetime, timezone

def normalized_time(original: str) -> datetime:
    if type(original) is not str or len(original) > 64:
        raise ValueError("bad timestamp representation")
    try:
        value = datetime.fromisoformat(original.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("bad timestamp syntax") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("offset required")
    return value.astimezone(timezone.utc)

timeline = [
    ("a1", "2026-01-01T10:00:00Z", "failure"),
    ("b1", "2026-01-01T17:01:00+07:00", "failure"),
    ("a2", "2026-01-01T10:02:00Z", "success"),
]
ordered = sorted(timeline, key=lambda item: normalized_time(item[1]))
assert [event_id for event_id, _, _ in ordered] == ["a1", "b1", "a2"]
```

The code checks timestamp parsing but not provenance or source integrity. A full forensic pipeline records the *original raw bytes*, a hash of acquired files, collection method, tool version and transformation details.

## 13. Evidence chain-of-custody table

| Field | What you record | Why it matters |
|---|---|---|
| Evidence ID | stable local case ID | track artifacts unambiguously |
| Origin | VM, path, volume/source | explain source |
| Authority | approved lab/case scope | demonstrate permitted collection |
| Collector & time | UTC and role | accountability |
| Acquisition method | snapshot/export/tool version | reproducibility |
| SHA-256 | computed from acquired exact bytes | integrity comparison |
| Transfer history | actor/time/method | custody |
| Work product | normalized timeline, report | distinguish derived analysis |

A SHA-256 digest **does not** prove a file's origin or that its statements are truthful. File timestamps may have been altered by normal activity or adversaries; `ctime` is platform-dependent.

### Interpret evidence without overstating certainty

Write separate headings:
- **Observation:** two failures and a success appear in provided logs.
- **Interpretation:** sequence is consistent with a person retrying credentials.
- **Alternative:** benign password correction, scripted test or compromised credential use.
- **Missing evidence:** MFA outcomes, source device, authoritative identity-provider logs, clock synchronization.
- **Confidence:** limited because the lab records alone do not identify intent.

## 14. Practicum: chain-of-custody and validation

1. Generate the three synthetic JSONL records locally.
2. Compute SHA-256 for each file using chunked reading; record actual values.
3. Make read-only working copies; verify hashes match.
4. Normalize timestamps; keep original strings beside normalized UTC.
5. Add an event missing an offset; reject it, don't guess UTC.
6. Add an event with a timestamp earlier than prior ingest order; discuss source-time ordering.
7. Create a one-page report with observable facts and alternative explanations.
8. Explain how any response action (e.g., account revocation) would require the organization's authority and evidence-preservation policy.

### Assessment and solution cues

**Q:** Why might turning off a potentially compromised computer damage an investigation? Volatile memory, process/network state and temporary keys disappear; operational safety may still require shutdown under policy.

**Q:** How does "the log states..." differ from "the attacker did..."? The former describes evidence; the latter asserts attribution and intent requiring corroboration.

**Q:** Is it correct to merge three streams by **ingest** timestamp alone? Not necessarily. Ingest time may be delayed and is different from event time; preserve both.

**Q:** Is an unchanged hash enough to prove clean acquisition? No. It supports bytes being unchanged between comparisons, not source truth or chain of custody.

**Official standard:** [NIST SP 800-61 Revision 3 (April 2025)](https://csrc.nist.gov/pubs/sp/800/61/r3/final) integrates incident response into organization-wide cybersecurity risk management.
