# 02 — Data structures, algorithms and complexity
> **Expanded textbook (Beginner → Advanced):** This chapter now includes a first-principles lesson, a runnable local program, a reasoning trace, failure cases and graduated exercises. For additional specialized lessons, see: [collections complexity streams](../course/03-COLLECTIONS-COMPLEXITY-STREAMS.md).



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


## 2.7 Deep Core I — Model the operation before picking a container

A data structure is an *agreement* about operations, costs and ordering. A `list` keeps a sequence of references; its `append` is amortized constant time, but inserting at index zero usually shifts N elements. A `deque` is efficient at both ends but not designed for repeated random indexing in the middle. A `dict` maps keys using hash and equality; `set` uses similar membership semantics without storing values.

**Hashability is not the same as true immutability.** A tuple is hashable only when each element is hashable. A frozen dataclass might be hashable but can still contain mutable nested state under certain arrangements. Dictionary key equality must be coherent with hashing; changing a key's equality-relevant state after inserting it can break assumptions. Numeric `True` and `1` compare equal and share a hash, so they occupy one key position.

| Requirement | Candidate | Usual complexity | Hidden constraint |
|---|---|---|---|
| append event to ordered history | `list` | amortized O(1) | entire history consumes O(N) memory |
| remove oldest event | `collections.deque` | O(1) | bounds needed for long-running monitor |
| test whether ID was seen | `set` | expected O(1) | keys retained; provenance matters |
| count per actor | `Counter`/`dict` | expected O(1) per record | cardinality can be attacker-controlled |
| select top K by severity | heap / `nlargest` | O(N log K) typical | tie-breakers and memory |
| find record in sorted timeline | binary search | O(log N) | input must be sorted |
| return all events by actor | map to lists | O(N) retained | data minimization/retention |

**A complete demonstration, including first-seen order:**

```python
# DEEP_CORE_RUNNABLE
from collections import Counter, deque

events = ["alice", "bob", "alice", "carol", "bob"]
first_seen = list(dict.fromkeys(events))
assert first_seen == ["alice", "bob", "carol"]  # insertion-ordered dict
assert Counter(events) == {"alice": 2, "bob": 2, "carol": 1}

recent = deque(maxlen=3)
for identity in events:
    recent.append(identity)
assert list(recent) == ["alice", "carol", "bob"]
assert len({1: "integer", True: "boolean"}) == 1
forbidden = ["not-hashable"]
try:
    {forbidden}
except TypeError:
    pass
else:
    raise AssertionError("mutable list accepted as set member")
print("D02-A: container semantics")
```

**Trace:** `dict.fromkeys` records the first insertion of every distinct key and preserves order, but it retains only one instance of each key. The deque is a last-three-event *view*, not an evidence archive. A count of three logins is not a finding of an attack. Consider what you must preserve to reconstruct source evidence and dedup duplicates reliably.

**Practice:** choose the best container for each task: LIFO undo stack; FIFO work queue; unique IP membership; sorted finding ranking; source-qualified event counts. Explain why "fast lookup" is not sufficient if key normalization merges distinct accounts.

## 2.8 Deep Core II — Recursion, call stacks and termination

A recursive function calls itself on a **smaller subproblem**, eventually reaching a **base case**. Each call has its own local state on the call stack. For simple Python algorithms, recursion often has greater overhead than iteration. Extremely deep input can raise `RecursionError`; do not raise the interpreter recursion limit merely to process attacker-controlled nesting.

**Reasoning example:** factorial is defined by \(0! = 1\) and \(n! = n(n-1)!\) for \(n>0\). It is a good recursion teaching tool but rarely the best production implementation for untrusted `n`.

| Call | Waits for | Returned value |
|---|---|---:|
| `fact(3)` | `3 * fact(2)` | 6 |
| `fact(2)` | `2 * fact(1)` | 2 |
| `fact(1)` | `1 * fact(0)` | 1 |
| `fact(0)` | base case | 1 |

```python
# DEEP_CORE_RUNNABLE
def factorial_recursive(n: int) -> int:
    if type(n) is not int or not 0 <= n <= 100:
        raise ValueError("n outside bounded teaching range")
    if n <= 1:
        return 1
    return n * factorial_recursive(n - 1)

def factorial_iterative(n: int) -> int:
    if type(n) is not int or not 0 <= n <= 100:
        raise ValueError("n outside bounded teaching range")
    result = 1
    for value in range(2, n + 1):
        result *= value
    return result

assert factorial_recursive(0) == factorial_iterative(0) == 1
assert factorial_recursive(5) == factorial_iterative(5) == 120
for n in (-1, 101, True):
    try:
        factorial_recursive(n)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid recursion input accepted")
print("D02-B: base case and resource bound")
```

**Proof sketch (induction):** for zero the function returns 1, matching the definition. If it correctly returns \((n-1)!\), multiplying by `n` gives \(n!\). Runtime is O(n) calls and stack space O(n); the iterative version uses O(n) multiplications and O(1) **auxiliary** control space, excluding the increasingly large integer result. This distinction matters for honest complexity claims.

**Checkpoint:** show a recursive function missing its base case. Predict why a maximum recursion depth is reached, and explain why exception handling must not label an unfinished security parser as "no suspicious records".

## 2.9 Deep Core III — Searching: linear versus binary search

A **linear search** checks entries in order and works without a sorted input. Worst-case time is O(N), auxiliary space O(1). **Binary search** compares against the middle of a sorted range and discards half of the remaining search space on each step. Its comparisons are O(log N), but it requires a *verified sorted-order invariant* and a consistent key/comparator.

If you need only one search across a tiny dataset, sorting everything first may cost more than linear search. If you perform many searches over an already-sorted database/index, binary search can be worthwhile.

```python
# DEEP_CORE_RUNNABLE
from bisect import bisect_left

def linear_search(items: list[int], target: int) -> int | None:
    for index, item in enumerate(items):
        if item == target:
            return index
    return None

def binary_search(sorted_items: list[int], target: int) -> int | None:
    low, high = 0, len(sorted_items)
    while low < high:
        mid = (low + high) // 2
        if sorted_items[mid] < target:
            low = mid + 1
        else:
            high = mid
    return low if low < len(sorted_items) and sorted_items[low] == target else None

items = [3, 7, 7, 11, 20]
assert linear_search(items, 7) == 1
assert binary_search(items, 7) == 1
assert binary_search(items, 10) is None
assert bisect_left(items, 7) == 1
assert binary_search([], 10) is None
print("D02-C: binary search invariant")
```

**Trace: searching for 7 in [3,7,7,11,20].** Start `[low,high)=[0,5)`. Mid=2 has 7, so upper bound becomes 2. Mid=1 has 7, upper bound becomes 1. Mid=0 has 3, so low becomes 1. The loop stops at 1, the first possible position for 7 (a **lower bound**). The condition uses `<` rather than `<=` specifically to find the first equal value.

**Test design:** Find a target smaller than all items, larger than all items, absent between two numbers, equal to the first, equal to the last, and duplicated. Binary search on an **unsorted** list may produce the wrong answer without raising; validate preconditions at the boundary of the module instead of re-sorting secretly inside a function that promises O(log N) query time.

## 2.10 Deep Core IV — Sorting, stable ordering and cost

Sorting is not just about numeric ascending order. In a SOC timeline, *stable sorting* preserves original order among events whose timestamps compare equal. Python's `sorted` returns a new list and the built-in sort is stable; `list.sort` mutates the original list. A key function is evaluated to determine ordering; it can be different from the value displayed.

**Selection versus merge sort:** a simple quadratic selection sort repeatedly searches the minimum in the unsorted suffix (O(N²) comparisons). **Merge sort** recursively divides lists, sorts halves, then merges them (O(N log N) time, O(N) extra list storage in a standard implementation). Python's production built-in sort is highly optimized and should normally be preferred.

```python
# DEEP_CORE_RUNNABLE
def merge_sorted(left: list[int], right: list[int]) -> list[int]:
    i = j = 0
    result = []
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:  # left on equal keys -> stable
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    return result + left[i:] + right[j:]

def merge_sort(items: list[int]) -> list[int]:
    if len(items) <= 1:
        return items.copy()
    middle = len(items) // 2
    return merge_sorted(
        merge_sort(items[:middle]),
        merge_sort(items[middle:]),
    )

values = [5, 2, 2, -1, 7, 3]
assert merge_sort(values) == [-1, 2, 2, 3, 5, 7]
assert values == [5, 2, 2, -1, 7, 3]   # non-mutating
timeline = [(2, "first"), (1, "earlier"), (2, "second")]
assert sorted(timeline, key=lambda x: x[0]) == [
    (1, "earlier"), (2, "first"), (2, "second")
]
print("D02-D: merge sort and stability")
```

**How divide-and-conquer yields O(N log N):** the list is halved across about log₂N levels; across each level, all N elements are examined/merged once. That yields O(N log N) comparisons and O(N) auxiliary storage for the output lists in a conventional implementation. The demonstration uses slices, so it is not optimized for minimum allocations and deliberately limits itself to a small teaching dataset.

**Applied exercise:** sort synthetic security findings by severity descending, then by event time ascending, then by stable source order. Write down tie-breaking rules before implementing them. A deterministic ordering helps incident reports remain reproducible.

## 2.11 Deep Core V — Measuring complexity without misleading benchmarks

`time.perf_counter` provides a high-resolution clock for elapsed duration; `timeit` can repeat a very small benchmark many times; `tracemalloc` tracks many Python allocations, not necessarily all native allocations or full process RSS. A benchmark with one run can be dominated by interpreter startup, caching and CPU scheduling. A microbenchmark's fastest timing does not prove end-to-end pipeline speed.

```python
# DEEP_CORE_RUNNABLE
from timeit import repeat

def count_by_list(n: int) -> int:
    items = list(range(n))
    return sum(items)

assert count_by_list(10) == 45
# A tiny, bounded measurement; do not assert a particular elapsed time.
samples = repeat(lambda: count_by_list(100), number=100, repeat=3)
assert len(samples) == 3 and all(sample >= 0 for sample in samples)
print("D02-E: benchmark outcome is measurement, not proof")
```

**Correct reporting:** include interpreter version, environment, input sizes, number of repetitions, memory tracking method and whether construction, parsing and output were included in the timed interval. Compare multiple scales (e.g., 100, 1,000, 10,000) to infer growth. Never claim a result is O(1) simply because its milliseconds barely changed on your machine.

**Challenge:** Compare `needle in list(range(N))` against `needle in set(range(N))`. If you construct the set *inside* the timed test, are you measuring set lookup or the full cost of building the index? Explain the tradeoff.


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
