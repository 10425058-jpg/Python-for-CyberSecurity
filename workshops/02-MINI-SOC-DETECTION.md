# Workshop 02 — A complete offline SOC detection exercise

**Duration:** 3–5 hours · **Environment:** Python 3.11+ · **Network:** none · **Input:** synthetic JSONL.

## Mission
Build an analyst-friendly report of repeated failed logins without connecting to a real identity provider. Explore how to parse raw data, distinguish timestamps, apply a rolling threshold, reject corrupted records and avoid partial reports when ingestion fails.

## Safety and scope
Use **only** `fixtures/synthetic-auth.jsonl` or newly generated lab data. Do not collect other people's login data. Alerts are *review candidates*, never proof of account compromise.

## 1. Input schema

Open [fixtures/synthetic-auth.jsonl](../fixtures/synthetic-auth.jsonl). Each line is an independent JSON object. Core fields are `timestamp`, `actor` and `action`. Optional fields include `event_id`, `source`, `src_ip` and `outcome`. The advanced example validates these rather than trusting them.

**The rule:** at least 3 failed logins by the same actor within a rolling 300-second event-time window, in chronologically sorted data.

## 2. Run the example

From repo root:
```bash
python -m examples.mini_soc_pipeline \
  --input fixtures/synthetic-auth.jsonl \
  --output /tmp/mini-soc-findings.jsonl \
  --threshold 3 \
  --window-seconds 300
```

On Windows PowerShell, use an output path such as `.\mini-soc-findings.jsonl` and put the command on one line.

**Expected stderr:**
```text
complete: wrote 2 review alert(s) to /tmp/mini-soc-findings.jsonl
```

On Windows, the path portion differs. Each alert is one JSON line with `rule_id`, `actor`, `failure_count`, `window_seconds`, `timestamp_utc`, `supporting_event_ids` and `classification`. Do **not** claim two true attacks; the fixture is synthetic and the count is a rule result.

## 3. Trace the fixture

- 10:00 Alice failure → Alice queue length 1.
- 10:01 Alice failure → length 2.
- 10:01:30 Alice failure → length 3; first alert.
- 10:02 Alice failure → queue length 4; alert suppressed by latch.
- 10:09 Alice failure → old timestamps have expired; queue length 1; latch rearms.
- 10:09:30 Alice failure → length 2.
- 10:10 Alice failure → length 3; second alert.
- Bob's event(s) are below threshold.

The output counts supporting event IDs, generated from file line numbers if the record has no explicit event ID. These are lab-local identifiers, not globally trustworthy event IDs.

## 4. Inspect the parser

Open [examples/mini_soc_pipeline.py](../examples/mini_soc_pipeline.py). Find:
- `MAX_LINE_BYTES = 16_384` — hard cap before decoding.
- `readline(MAX_LINE_BYTES + 1)` — avoids eagerly reading an unlimited line.
- `json.loads(..., object_pairs_hook=...)` — rejects duplicate keys.
- `datetime.fromisoformat(...).astimezone(timezone.utc)` — handles offsets.
- `ipaddress.ip_address` — validates optional IP metadata.
- `seen` keyed by (source,event_id) — deduplicates replayed IDs.
- `deque` per actor — maintains windows.
- `max_actors` and `max_queue_per_actor` — resource caps.
- `NamedTemporaryFile` and `os.replace` — report committed only on successful complete ingest.

### Why atomic output is useful
If the file is corrupt halfway through processing, the script should not overwrite an existing report with a seemingly complete "zero alerts" result. The reference stages output to a temporary file in the destination directory, then replaces the target **only when processing succeeds**. This is a teaching atomic-write pattern, not a guarantee of forensic-grade durability, permission preservation or protection from filesystem races.

## 5. Run automated tests
```bash
python -m unittest tests.test_deep_examples.MiniSocTests -v
```

Check cases for duplicate IDs, out-of-order timestamps, wrong input types, large records, threshold rearm and incomplete-ingest output. "All tests passed" is meaningful only for these tested invariants.

## 6. Break your own fixture without touching the original

```python
from pathlib import Path
original = Path("fixtures/synthetic-auth.jsonl").read_bytes()
Path("broken-auth.jsonl").write_bytes(original + b"{not-json}\n")
```

Run the same command using `broken-auth.jsonl` and a report path that already contains a marker line. **Expected:** nonzero exit code, visible error, previous report unchanged. Delete the temporary lab file after testing.

### Investigate out-of-order data
Create a controlled copy with one event whose timestamp is earlier than the previous record. The detector must reject it rather than silently claiming valid correlation. A production stream processor could buffer/reorder within a documented allowed-lateness window; this reference implementation deliberately does not.

## 7. Change the threshold
Test `--threshold 5` and compare alert counts. Expected: fewer alerts, potentially zero in this fixture. Discuss the tradeoff: raising thresholds may reduce benign false positives but increases missed slow patterns.

## 8. Analyst interpretation

Write a short report:
- Observation: Alice has repeated failures within 300 seconds in synthetic data.
- Hypothesis: repeated authentication failures may merit triage.
- Benign alternatives: password typo, device retry, automation or test activity.
- Corroboration needed: known device, successful logins, MFA, risk context, time accuracy.
- Action: review, **not automatic account disable**.

## 9. Independent challenge
Add a deterministic `--max-records` flag to the CLI, demonstrate failures on overflow, update tests, and document what it means to stop early. Do not hide an incomplete scan behind a successful result.

## 10. Questions and checks
1. What is the difference between an event-time window and an ingest-time window?
2. Why is a deque appropriate?
3. Why are source IPs not reliable human identities?
4. What is the limitation of deduplicating by a guessed event ID?
5. Why can an empty output file mean "zero alerts in complete input" but not "no security incidents"?
6. Why is a fail-visible response safer than silent parse-error skipping?

**Deliverables:** output JSONL, three test outcomes, a threshold comparison table, a one-page analyst note and a clear statement of limitations.
