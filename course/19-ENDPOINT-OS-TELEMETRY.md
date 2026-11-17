# Deep Dive 19 — Linux, Windows and endpoint telemetry with Python

**Level:** intermediate → advanced · **Estimated study:** 10–14 hours.

## Goal
Understand how operating systems represent activity, which logs are reliable for specific questions, and how Python can normalize *approved, exported* system events. Work with synthetic data rather than gathering privileged logs from other people's machines.

## 1. Linux processes, identities and permissions

A Linux process has a PID and credentials (UID/GID and related security context). File permissions can be represented by owner/group/other modes and ACLs; security modules such as SELinux/AppArmor can impose further controls. Root or broad capabilities can do far more than a normal process.

Systemd manages services and units; journald stores structured logs in many modern distributions. Auth logs, auditd, kernel logs and application logs may complement each other. Availability and location differ among distros.

### Safe local process information
```python
import os
import platform
print({"pid": os.getpid(), "platform": platform.system()})
```

This reports your own process ID and platform without scanning remote or privileged information.

### Syslog/journald pitfalls
A line of text is not guaranteed to contain an authentic username or trustworthy IP. Different sources record different time zones and formats. Hostnames can be attacker influenced; log completeness depends on forwarding, disk pressure and permissions.

## 2. Windows identities and logging

A Windows process has a security token, access rights and integrity level. UAC, local/domain roles, NTFS ACLs, service identities and Group Policy affect access. Windows Event Logs are organized by channels/providers, and Sysmon can record extended event types.

**Never interpret an event ID without provider/channel context.** "Event ID 1" can mean different things across providers. Some IDs or event fields change with OS/software versions.

Important areas for defenders:
- Logon/authentication events.
- Service creation/changes.
- Process creation and parent relationship.
- Scheduled task changes.
- PowerShell script-block logging where enabled.
- Registry modifications and startup entries.
- Windows Defender/EDR signals.
- Time sync, device and audit configuration.

## 3. Create a portable event schema

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class EndpointEvent:
    time_utc: datetime
    host: str
    source: str
    event_type: str
    principal: str | None
    process_id: int | None
    raw_reference: str
```

Validation is required before instantiating this model from untrusted JSON. `process_id` alone is not a stable process identity because PIDs get reused; combine host, process creation time or provider-specific IDs as available.

## 4. Normalization should be loss-aware

Given an exported Linux event:
```json
{"timestamp":"2026-01-01T10:00:00Z","host":"lab-linux","program":"sshd","message":"synthetic login failure"}
```

Given an exported Windows event:
```json
{"timestamp":"2026-01-01T10:00:02Z","host":"lab-windows","provider":"ToyAuth","event_id":1001,"action":"login_failure"}
```

You may derive an event type "authentication_failure" for both sources, but do not discard the original fields. Source messages have different trust and semantics. Map unknown provider/event IDs to "unknown", not to a guessed category.

## 5. Detecting suspicious patterns responsibly

### Example hypothesis
Three failed logins followed by a success for one account in a short window could deserve review. It may also be a human fixing a password typo. Confirm identity-provider subject, source device, MFA state and expected user behavior before escalating.

### Process tree analysis
Parent/child relationships can be informative but may be absent or misleading. PID reuse, process injection and logging gaps complicate interpretation. Avoid claiming a process tree alone proves an infection.

### Persistence mechanisms
Startup services, scheduled tasks, registry autoruns and cron jobs can be used by legitimate software. A change is not automatically malicious; defenders compare baselines, policy and change records. This course does not instruct creation of stealth persistence.

## 6. Python adapter design

```text
authorized exported event file
  ↓
size-bound schema reader
  ↓
source-specific parsing adapter
  ↓
common event model + original reference
  ↓
per-host/identity aggregation
  ↓
analyst report with uncertainty
```

Keep adapters read-only and isolate any platform-specific package from the pure analysis core. Do not invoke privileged commands as a workaround to missing permissions.

## 7. Operational constraints

- Time sync and clock skew.
- Log rotation and retention.
- Restricted channels and event collection rights.
- Sensitive command lines and environment variables in process records.
- Endpoint performance and storage overhead.
- Cross-platform parsing and localized message formats.
- Missing events during outages, crashes or deliberate tampering.
- False positives from update systems, administrators and backups.

## 8. Lab
1. Create two synthetic JSONL files representing Linux and Windows events.
2. Write source-specific normalizers that produce `EndpointEvent`.
3. Require aware ISO 8601 time, host, source and raw reference.
4. Add malformed and missing fields; test that rejection is visible.
5. Merge the records into a single UTC timeline.
6. Count login failures per host, then by principal where available.
7. Write three alternative explanations for one suspicious-looking burst.
8. Document which sources you would need in a real investigation and their access permissions.

## 9. Questions
- Why should an event ID include provider/channel context?
- Why is a PID not globally unique over time?
- Why is an endpoint log a source of claims rather than unquestionable truth?
- What extra fields help correlate user and device actions?
- What are the privacy risks of collecting process command lines?

**References:** [Microsoft Windows Event Logging](https://learn.microsoft.com/en-us/windows/win32/eventlog/event-logging), [systemd journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html), [Python platform](https://docs.python.org/3/library/platform.html).
