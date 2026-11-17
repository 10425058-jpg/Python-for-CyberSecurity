# Python Foundations — Two Integrated Portfolio Projects

These are **read-only / offline defensive teaching projects** for the first two Python textbook chapters. They are deliberately self-contained and use only Python's standard library. Never run them against unapproved identity services, real private login records, or production response systems.

## Project 01 — Auth Summary (Language Foundations)

**Skills:** strict types, string/byte handling, branching, loops, dictionaries/Counter, parsing, errors, source-qualified deduplication, basic file I/O and import-safe CLI design.

**Input contract:** each line of a UTF-8 JSONL file is one object with exactly:

| Key | Type | Requirement |
|---|---|---|
| `source` | string | 1–64 ASCII letters, digits, underscores, dots or hyphens |
| `event_id` | string | same form; only unique within its source |
| `timestamp` | string | timezone-aware ISO timestamp, e.g. `2026-01-01T10:00:00Z` |
| `actor` | string | 1–64 allowed ASCII characters (toy username) |
| `action` | string | `login_failure` or `login_success` |

Each raw line is capped at **4096 bytes**, a complete input at **1000 lines**, and the number of distinct failing actors at **500**. The implementation rejects duplicate JSON keys, non-JSON numerical constants, malformed UTF-8, invalid types and conflicting records with the same source-qualified ID. Identical replays are counted but not treated as separate events.

**Run (from repository root):**

```bash
python -m projects.foundations.auth_summary --input fixtures/foundations-auth.jsonl --output auth-summary.json
python -m unittest tests.test_foundations_projects.SummaryProjectTests -v
```

**Expected derived values:** `complete=true`, 8 unique events, 0 duplicates, 1 success, `failures_by_actor={"alex":7}`. The report includes a SHA-256 digest of the original bytes. SHA-256 alone supports comparison to trusted reference bytes; it does not authenticate the source.

**Failure drill:** use `fixtures/foundations-invalid-third.jsonl` as input, ensure the command returns nonzero with `INCOMPLETE` on stderr, and verify any previously complete destination file is **unchanged**. The program reads and validates completely *before* staging one JSON report. A same-directory temporary file is fsynced and replaced on success; this is not a multi-file transaction, guaranteed power-loss durability, or a race-free filesystem acquisition.

**Build it yourself before reading the reference:** define a validated event type; parse bytes; handle each error without losing its line number; deduplicate using a composite key; count failures; return structured results; write the CLI separately.

## Project 02 — Burst Detector (Data Structures & Algorithms)

**Skills:** deque, dictionary, set, sliding window, threshold state machine, UTC event-time ordering, amortized complexity, capacity limits, deterministic output and regression tests.

**Rule:** for each (`source`, `actor`) pair, retain `login_failure` events whose timestamp is within an **inclusive 60-second interval**. A new review candidate appears the first time its count reaches three; it stays latched while count remains ≥3. Re-arm only when the **post-arrival** active failure count drops below three. A login success is ignored by this particular toy failure-only detector, and it does not reset the window.

**Run:**

```bash
python -m projects.foundations.window_detector --input fixtures/foundations-auth.jsonl --output burst-report.json
python -m unittest tests.test_foundations_projects.WindowProjectTests -v
```

**Expected:** exactly **2** review candidates. The 0/30/60-second group triggers at t=60. The t=61 event replaces the expired t=0 event but must **not** create a duplicate alert. The 200/210/220-second group triggers a new alert after the old window expired and the notification state re-armed.

| Test case | Expected behavior |
|---|---|
| `[0,30,60]` | one alert |
| `[0,30,60,61]` | still one alert |
| `[0,30,61]` | zero alerts |
| `[0,30,60,200,210,220]` | two alerts |
| out-of-order UTC events | explicit incomplete error |
| same source+event ID, identical event | one event, duplicate count +1 |
| same ID with different content | conflicting ID error |
| too many actors / failures in window | explicit incomplete error |
| malformed record late in input | no partially committed report |

The algorithm is O(N) deque work over N normalized events under the stated per-actor model; memory is O(U + R), where U is the number of retained actor keys and R is total queued failures, plus O(N) for the bounded, in-memory event list loaded by this teaching implementation. Those dimensions must be considered separately when adapting the design.

**Security honesty:** a burst of failures may be a forgotten password, a service retry, a testing event or an attacker. This tool creates *review candidates*, **not** confirmed incidents, and never automatically blocks accounts.

## Complete engineering checklist

1. Start with the two [expanded chapters](../../python/README.md).
2. Complete [25 language exercises](../../python/exercises/01-LANGUAGE-FOUNDATIONS-EXERCISES.md) and [25 algorithms exercises](../../python/exercises/02-DATA-STRUCTURES-ALGORITHMS-EXERCISES.md).
3. Try the code yourself **before** opening the corresponding [solution keys](../../python/solutions/README.md).
4. Run the entire test suite:

   ```bash
   python -m unittest tests.test_foundations_deep_examples -v
   python -m unittest tests.test_foundations_solution_snippets -v
   python -m unittest tests.test_foundations_projects -v
   python -m unittest discover -s tests -v
   ```

5. Deliver a short threat model, a screenshot of clean and incomplete CLI runs, the input schema and max-size policy, and a report stating what the observations do **not** prove.
6. Follow the rest of the [12-chapter Python foundation track](../../python/README.md), then the [Mini-SOC build path](../BUILD-PATH.md).

**Further reading:** [Python data model](https://docs.python.org/3/reference/datamodel.html), [collections](https://docs.python.org/3/library/collections.html), [bisect](https://docs.python.org/3/library/bisect.html), [heapq](https://docs.python.org/3/library/heapq.html), [unittest](https://docs.python.org/3/library/unittest.html).
