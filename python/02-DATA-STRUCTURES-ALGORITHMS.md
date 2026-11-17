# 02 — Data structures, algorithms and complexity
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [collections complexity streams](../course/03-COLLECTIONS-COMPLEXITY-STREAMS.md).



## Extended textbook 02 — Choose data structures using invariants and complexity

### 2.1 Each container promises a different operation

A **list** stores a mutable ordered sequence, supports indexing in constant time and appends efficiently at the end; inserting or deleting near the front generally shifts elements. A **tuple** fixes the sequence of references (but nested mutable elements can still change). A **dictionary** maps hashable keys to values; a **set** stores unique hashable values. A **deque** supports efficient appends and pops from both ends. A **Counter** is a dictionary specialized for frequencies.

| Operation | List | Dict/Set | Deque | Why it matters |
|---|---|---|---|---|
| index by position | O(1) | not the same abstraction | O(n) for middle | event sequences |
| search arbitrary value | O(n) | expected O(1) hash lookup | O(n) | dedup and indicators |
| append to right | amortized O(1) | not positional | O(1) | streaming records |
| remove oldest | O(n) with `pop(0)` | unrelated | O(1) `popleft` | rolling windows |
| all entries | O(n) | O(n) | O(n) | report generation |

These are **typical** operation costs, not a promise that memory is unlimited or that adversarial inputs cannot affect performance. `dict` keys must have coherent `__hash__` and `__eq__` implementations, and mutable values generally should not be dictionary keys.

### 2.2 What Big-O means in practice

O(N) describes how cost grows as N grows; it does not predict an exact runtime in seconds. Nested loops over N values often grow O(N²), whereas building a dictionary index and then looking up each item may reduce repeated searches to expected O(N). Sorting N values is ordinarily O(N log N). For security tools, measure both **time complexity** and **space complexity**, especially when the adversary can control the number of distinct user IDs or event sizes.

### 2.3 Work through a rolling window rather than memorizing deque

A detector should define time order, inclusive boundary, threshold and when to notify **before** choosing its data structure. For one actor, keep each accepted timestamp in a deque; remove those older than 60 seconds; alert when count crosses three; suppress duplicates while the count stays at or above threshold.

```python
# TEXTBOOK_RUNNABLE
from collections import Counter, deque

def burst_alert_times(times: list[int], *, seconds=60, threshold=3) -> list[int]:
    if type(times) is not list or not 1 <= threshold <= 100 or seconds < 1:
        raise ValueError("invalid window parameters")
    queue = deque()
    already_notified = False
    alerts: list[int] = []
    previous = -1
    for t in times:
        if type(t) is not int or t < 0 or t < previous:
            raise ValueError("timestamps must be sorted nonnegative integers")
        previous = t
        while queue and t - queue[0] > seconds:
            queue.popleft()
        queue.append(t)
        if len(queue) < threshold:
            already_notified = False
        if len(queue) >= threshold and not already_notified:
            alerts.append(t)
            already_notified = True
    return alerts

assert burst_alert_times([0, 30, 60, 61]) == [60]
assert burst_alert_times([0, 30, 61]) == []
assert burst_alert_times([0, 30, 60, 61, 200, 210, 220]) == [60, 220]
assert Counter(["fail", "ok", "fail"]) == {"fail": 2, "ok": 1}
print("LAB 02 PASS")
```

**Trace table for threshold 3, inclusive 60 seconds:**

| Time | Active deque after new event | Alert? | Reason |
|---:|---|---|---|
| 0 | [0] | no | one event |
| 30 | [0, 30] | no | two events |
| 60 | [0, 30, 60] | **yes** | exactly three in window |
| 61 | [30, 60, 61] | no | still active; do not alert twice |
| 200 | [200] | no | old window expired; re-armed |
| 220 | [200, 210, 220] | **yes** | new crossing |

The last row assumes the intermediate event at 210 was processed. Each event enters and exits the deque at most once, so total deque operations are O(N). **Important limitation:** for an extremely high event rate, the deque remains unbounded; add a per-actor capacity and a documented overflow policy. For many actors, also limit the total number of actor keys and record the incomplete state if you exceed capacity.

### 2.4 Algorithms beyond counters

**Sorting and stability:** `sorted(events, key=...)` is stable; when two events share an equal timestamp, original order is retained, which is useful when a source index is meaningful. **Binary search:** `bisect_left` finds an insertion point in an already-sorted sequence in O(log N), but list insertion remains O(N). **Heap:** `heapq.nlargest(k, iterable)` efficiently selects the highest-k values without fully sorting when k is small. **Grouping:** a `defaultdict(list)` is convenient but may retain all raw evidence in RAM; streaming aggregation is often safer.

### 2.5 Semantic bugs hidden inside common operations

Blindly calling `lower()` or `casefold()` on every account identifier can merge distinct identities, depending on the provider. `set` deduplication loses first-seen order and may hide duplicate *evidence*; keep both a canonical identity key and raw source references. A `Counter` reporting five failed logins says nothing about who caused them or whether your logging system was complete.

### 2.6 Graded exercise set

**Beginner:** Compare a list, set and dict by predicting what they contain after duplicate insertions. Explain ordering and uniqueness. **Intermediate:** Find the three most common toy IP strings using `Counter`; compare fully sorting versus `heapq.nlargest`. **Advanced:** Extend `burst_alert_times` to support multiple actors, source-qualified deduplication, a max actor count, a max deque count, and explicit failure on out-of-order timestamps.

**Answer checks:** inclusive boundary means `t - oldest > window` causes expiration; `>=` would exclude the exact boundary. Every distinct-key or queue cap needs tests. An overflow cannot silently mean "no alerts."

## Collections
| Type | Ordering | Mutable? | Typical cybersecurity use |
|---|---|---|---|
| `list` | insertion | yes | event sequences |
| `tuple` | insertion | no | immutable event keys |
| `dict` | insertion | yes | parsed JSON, counters, indexes |
| `set` / `frozenset` | iteration not ordered contract | yes / no | deduplication, indicators |
| `collections.deque` | sequence | yes | bounded queues, rolling windows |
| `collections.Counter` | mapping | yes | frequency analysis |
| `heapq` | heap ordering | yes | top-priority alerts |
| `bisect` | sorted-list operations | n/a | thresholds and intervals |

### Counting events
```python
from collections import Counter, defaultdict
events = [
    {"ip": "192.0.2.1", "status": 401},
    {"ip": "192.0.2.1", "status": 401},
    {"ip": "198.51.100.2", "status": 200},
]
failures = Counter(e["ip"] for e in events if e["status"] == 401)
print(failures.most_common(5))
by_ip = defaultdict(list)
for event in events:
    by_ip[event["ip"]].append(event)
```

### Complexity
- List append: amortized O(1); membership: O(n).
- Dict/set lookup: expected average O(1), not a universal worst-case guarantee.
- Sorting: O(n log n); sorting millions of logs in memory is expensive.
- Streaming through a file: O(n) time and bounded memory when avoiding `read()` of the whole file.
- Nested comparison of all hosts against all hosts: O(n²), which often does not scale.

Understand the distinction between **average performance**, **worst-case performance**, and **adversarial inputs**. Set limits on input sizes, recursion depth, and decompression output to prevent resource exhaustion.

### Comprehensions and safe parsing
```python
valid_ports = {p for p in [22, 80, 443, -1, 70000] if 1 <= p <= 65535}
assert valid_ports == {22, 80, 443}
```
Comprehensions are concise but can obscure multiple validation steps. Prefer explicit loops when incident logic needs an audit trail.

### Core patterns to master
- Deduplication with a set while preserving first-seen order with dict keys.
- Sliding windows for burst detection (deque of timestamps).
- Aggregation by normalized principal/IP/event ID.
- Sorting with `key=`, stable sorting, and `heapq.nlargest`.
- Searching sorted timestamps via `bisect`.
- Hashing and indexing normalized indicators; normalize case and Unicode thoughtfully.

## Exercises
1. Stream 100,000 synthetic login events and count by user using a `Counter`.
2. Find the ten noisiest client addresses without storing full event payloads.
3. Implement a bounded sliding-window failed-login count and explain O(n) time.
4. Compare list vs set membership with `timeit` and document measurement errors.
5. Create adversarial tests with missing keys, null values, duplicates, and huge fields.
