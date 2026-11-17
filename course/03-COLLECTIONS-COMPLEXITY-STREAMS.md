# Deep Dive 03 — Data structures, algorithmic complexity and scalable security pipelines

**Level:** beginner → intermediate · **Estimated study:** 8–12 hours.

## The problem we will solve
Imagine one million synthetic authentication records arriving every day. You need to count login failures per user, keep track of repeated events over a five-minute window, and report the ten noisiest users, while respecting a memory budget.

The fundamental skill is choosing a data structure for each operation rather than reflexively putting everything into one list.

## 1. List, tuple, dict, set: semantics and tradeoffs

| Type | Shape | Typical operations | Security use | Trap |
|---|---|---|---|---|
| list | ordered mutable sequence | append, iterate, index | chronological records | membership scans O(n) |
| tuple | ordered fixed references | unpack, hash if elements hashable | immutable keys | nested mutability |
| dict | key → value | key lookup, update | normalized event | unexpected keys/data injection |
| set | unique hashable elements | membership, union/intersection | deduplicate indicators | no promised iteration order |
| deque | double-ended queue | O(1) append/popleft | rolling windows | needs maxlen/bounds |
| Counter | mapping of counts | update, most_common | event frequency | memory grows with unique keys |
| heap | priority queue | push/pop | top alert priority | not globally sorted |

All Big-O costs refer to operation *growth rates*, not absolute speed. A "fast" algorithm with unbounded allocations can still be unsafe.

## 2. Counting without storing all events

```python
from collections import Counter

def count_failures(lines):
    counts = Counter()
    for raw in lines:
        actor, action = raw.split(",", maxsplit=1)  # demo format only
        if action.strip() == "fail":
            counts[actor.strip()] += 1
    return counts

sample = ["alice,fail", "bob,ok", "alice,fail"]
assert count_failures(sample) == {"alice": 2}
```

Space complexity is O(U), where U is the number of **distinct actors**, not O(total events). But hostile data could provide one million distinct actor names: even this counter could exhaust memory. Enforce allowed identifier lengths, actor count caps, TTL or persistent spillover storage.

For robust production parsing, use JSONL/schema validation rather than `split(",")`; this split is intentionally minimal to illustrate the data structure.

## 3. Sliding windows with a deque

**Problem:** flag an actor whose failed-login timestamps include at least three events in 300 seconds.

Store only timestamps needed by the current window. Each timestamp is appended once and removed at most once, giving amortized O(n) processing for one actor's chronologically ordered events.

```python
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

def review_bursts(events, threshold=3, seconds=300):
    windows = defaultdict(deque)
    span = timedelta(seconds=seconds)
    results = []
    for when, actor, failed in events:  # must already be sorted by timestamp
        if not failed:
            continue
        queue = windows[actor]
        while queue and when - queue[0] > span:
            queue.popleft()
        queue.append(when)
        if len(queue) == threshold:
            results.append({"actor": actor, "at": when.isoformat(),
                            "count": threshold})
    return results
```

**Trace manually** with failures for Alice at 10:00:00, 10:01:00, 10:04:00 and 10:10:00. At 10:04:00, the deque contains all three; at 10:10:00, the previous times fall outside the 300-second window.

### Window definitions matter
- Inclusive boundary: `when - oldest <= 300 seconds` stays in the window.
- Rolling window: recomputed relative to each new event.
- Tumbling window: fixed bins, e.g. every five minutes on the clock.
- Late arrivals: a rule expecting chronological order may give invalid counts if sources arrive out of order.
- Event time vs ingest time: neither can be substituted without explaining the semantics.

**Memory trap:** an attacker can supply many distinct actor names, creating one deque per actor. A production pipeline needs eviction/watermarks, per-actor caps, backpressure and data-quality metrics.

## 4. Top-K reports and priority

`Counter.most_common(10)` is convenient but retains all keys. `heapq.nlargest(10, iterable, key=...)` can find top K from a stream of *already aggregated* (actor, count) pairs while keeping a bounded heap.

```python
import heapq
counters = {"alice": 8, "bob": 2, "charlie": 6}
top = heapq.nlargest(2, counters.items(), key=lambda pair: pair[1])
assert top == [("alice", 8), ("charlie", 6)]
```

Do not confuse "top 10 actors" with "ten most recent events"; the former needs counts, the latter a time-ordered queue or index.

## 5. Sorting, searching, and indexing

Sorting n event timestamps takes O(n log n) time. Linear search over unsorted data takes O(n); binary search via `bisect` over a sorted array takes O(log n) for lookup, but inserting into a Python list generally requires shifting O(n) elements. On millions of records, database indexes are often more appropriate.

```python
from bisect import bisect_left
timestamps = [10, 20, 30, 50]  # seconds since artificial epoch
position = bisect_left(timestamps, 25)
assert position == 2  # first position not less than 25
```

A dictionary allows expected O(1) exact-key lookup, not efficient time-range queries unless you maintain additional structure.

## 6. Generators and memory

`list(source)` materializes all records. A generator yields one at a time; memory is kept only for what the consumer retains.

```python
def valid_events(lines):
    for raw in lines:
        raw = raw.strip()
        if raw:
            yield raw

# Avoid: [transform(e) for e in massive_log]
# Better: for event in map(transform, valid_events(massive_log)): ...
```

One common mistake: making a generator but immediately calling `list(generator)`. That loses the memory advantage.

### When to use SQLite
If you must query by time, actor and event ID across tens of millions of rows, SQLite/PostgreSQL with suitable indexes can be more robust than arbitrary Python dictionaries. Database storage still has costs and requires retention, access controls and transactions.

## 7. Worked defensive pipeline

Synthetic input rows:
```json
{"actor":"alice","action":"fail","timestamp":"2026-01-01T10:00:00Z"}
```

Pipeline:
1. Read one line (bounded length).
2. Parse JSON and validate schema.
3. Normalize timestamp to aware UTC.
4. Deduplicate by event ID (only if you have a stable ID).
5. Update the actor's deque.
6. If rule threshold crossed, generate a **review candidate** with evidence pointers, not a declaration of attack.
7. Count processing errors and latency, not just positive alerts.
8. Persist state or document loss on restart; define retention.

For a runnable implementation with explicit timestamp ordering, see [examples/log_detector.py](../examples/log_detector.py).

## 8. Failure modes and safety limits
- If data arrives out of order, silently continuing can under/over-count.
- If identifiers are unbounded, an attacker can cause memory exhaustion.
- If an event ID is not globally unique, deduplication can delete real evidence.
- If a rule is based on a list of millions of events, memory scales with traffic.
- If timestamps lack time zones, the same clock reading can represent different instants.
- If input is attacker-controlled, do not interpolate it into SQL, shell commands or paths.

## 9. Exercises and worked answer checks

**Exercise 1:** Given `["a","b","a","c","a","b"]`, write a `Counter` and show the two most frequent actors. **Answer:** `a:3, b:2`.

**Exercise 2:** Manually trace a 60-second sliding window for events at t=0, 30, 60, 61. With inclusive boundaries, the queue at t=60 has [0,30,60]; at t=61 it has [30,60,61]. Explain why t=0 expired.

**Exercise 3:** Write a data structure selection paragraph for a script that must (i) deduplicate 100,000 hashes and (ii) return the most recent ten events. **Answer:** a set for hashes and a fixed-size deque for recent events; consider hash cardinality and retention.

**Exercise 4:** Generate 100,000 synthetic event lines and compare `tracemalloc` peaks of a list and a generator. Explain sources of measurement bias (interning, allocator behavior and retention).

**Exercise 5:** Design an eviction strategy for actor queues in a real detector. Explain how eviction may affect accuracy and what metrics you would publish.

## Self-check
Why does a deque give amortized linear time? What are the memory implications of unbounded key cardinality? When would `bisect` be insufficient? How would delayed log ingestion change a detection rule?

**References:** [collections](https://docs.python.org/3/library/collections.html), [heapq](https://docs.python.org/3/library/heapq.html), [bisect](https://docs.python.org/3/library/bisect.html).


## 10. Production-style problem: repeated failures with bounded state

A simple `defaultdict(deque)` is efficient **per actor** but can grow forever when millions of different usernames appear. Threat actors can exploit high-cardinality keys to exhaust memory without generating many events per account. The key observation is that "O(number of actors)" is still dangerous if that number is attacker controlled.

### Trace a rolling window (including exact boundary)

Window = 60 seconds; threshold = 3; events for actor Alice occur at t = [0, 30, 60, 61].

| t | Remove timestamps strictly older than t−60 | Queue after append | Threshold |
|---|---|---|---|
| 0 | none | [0] | no |
| 30 | none | [0,30] | no |
| 60 | none (0 is inclusive) | [0,30,60] | yes |
| 61 | remove 0 | [30,60,61] | remains met |

A detector that sends a new alert on every qualifying event causes duplicates. Define *latch* or cooldown semantics: emit on first threshold crossing, suppress until the count falls below the threshold, then rearm. The policy affects analyst load and missed repeated bursts.

### Standalone bounded detector with per-source accounting

```python
from collections import defaultdict, deque

def burst_crossings(events, *, window=60, threshold=3, max_actors=100):
    if window <= 0 or threshold <= 0 or max_actors <= 0:
        raise ValueError("positive limits required")
    queues = {}
    active = set()
    last_time = None
    for t, actor in events:
        if type(t) is not int or t < 0:
            raise ValueError("invalid timestamp")
        if last_time is not None and t < last_time:
            raise ValueError("events must be globally time-sorted")
        last_time = t
        if not isinstance(actor, str) or not 1 <= len(actor) <= 64:
            raise ValueError("invalid actor")
        if actor not in queues:
            if len(queues) >= max_actors:
                raise ValueError("actor cardinality cap exceeded")
            queues[actor] = deque()
        q = queues[actor]
        while q and t - q[0] > window:
            q.popleft()
        if len(q) < threshold:
            active.discard(actor)
        q.append(t)
        if len(q) >= threshold and actor not in active:
            active.add(actor)
            yield {"actor": actor, "time": t, "count": len(q)}

assert list(burst_crossings([(0,"a"), (30,"a"), (60,"a")])) == [
    {"actor":"a","time":60,"count":3}
]
```

**Complexity:** each event is appended once and removed at most once from its actor queue: amortized O(N) total deque operations. Memory is bounded by the number of stored actors and timestamps *only if* both are capped. This example caps actor cardinality but not per-actor queue size, so a production adaptation must cap it or use a counted compressed window structure.

**Limitations:** no deduplication, no bounded per-actor queue, no stale-actor eviction, and the global ordering assumption is strict. It demonstrates the exact window semantics rather than a deployable SIEM.

## 11. Selection of structures by query

| Question | Candidate structure | Complexity / hidden costs |
|---|---|---|
| Have we observed this file hash before? | set of digests | expected O(1) lookup; unbounded set grows |
| How many failures per actor? | Counter | O(N) processing, O(unique actors) memory |
| Ten newest validated events? | deque(maxlen=10) | fixed memory, O(1) append |
| Ten actors with highest count? | heap or Counter.most_common | requires maintained counts |
| All events in time interval? | sorted timestamps + bisect, or indexed DB | insertions are O(N) for list |
| Event IDs across process restart? | SQLite UNIQUE index | transactional persistence, storage cost |

### Exercise ladder with model reasoning

**A:** For 1,000,000 events and 20 actors, which dominates memory: entire list or Counter? Answer: full list stores O(1,000,000) records; Counter O(20).

**B:** What happens with 1,000,000 distinct malicious usernames? Counter memory is O(1,000,000). Consider caps, rejected/overflow metrics and disk-backed aggregation.

**C:** Build a `deque(maxlen=10)` recording last-seen *synthetic* file events. Explain why losing the oldest record is fine for an activity preview but unacceptable for evidence preservation.

**D:** Add per-actor queue caps to the code above. Decide whether to stop processing or drop older entries; explain how each changes accuracy.

**E:** Add unit tests for t = 60 (included) and t = 61 (first event expired), plus two actors interleaving and an out-of-order record.

**Operator question:** if your pipeline must handle 10 million events/day and low-memory clients, which stage should spill to SQLite or Parquet, and why? Model throughput, query pattern and retention before picking a library.
