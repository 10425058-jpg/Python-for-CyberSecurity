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



## 2.12 Deep Core VI — Trees and graphs: represent relationships

A **tree** is a connected acyclic graph with a designated root in many applications. A **graph** contains vertices (nodes) and edges (relationships); it may be directed or undirected, weighted or unweighted, cyclic or acyclic. An *adjacency list* stores neighbors for each node; for a sparse graph, it commonly uses O(V+E) space rather than an O(V²) adjacency matrix.

Cybersecurity analogies: a filesystem directory hierarchy is tree-like but symbolic links can introduce cycles and cross-boundary edges. An asset dependency graph models software relationships; an identity/role graph models access edges. The representation alone does not make a trust decision—missing or fabricated edges are a data quality problem.

**Breadth-first search (BFS)** explores vertices in increasing number of edges from the start when all edges have equal cost. It uses a FIFO queue. **Depth-first search (DFS)** explores along one path before backtracking and uses a stack (or recursion). Always track `visited` in cyclic graphs.

```python
# DEEP_CORE_RUNNABLE
from collections import deque

TOY = {
    "gateway": ("web", "database"),
    "web": ("app",),
    "database": (),
    "app": ("gateway",),  # cycle for visited-set demonstration
}

def bfs(start: str, graph: dict[str, tuple[str, ...]], max_nodes=20) -> list[str]:
    if start not in graph or type(max_nodes) is not int or max_nodes < 1:
        raise ValueError("invalid start or cap")
    queue = deque([start])
    visited = {start}
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in graph:
                raise ValueError("dangling graph edge")
            if neighbor not in visited:
                if len(visited) >= max_nodes:
                    raise ValueError("node cap exceeded")
                visited.add(neighbor)
                queue.append(neighbor)
    return order

assert bfs("gateway", TOY) == ["gateway", "web", "database", "app"]
try:
    bfs("gateway", TOY, max_nodes=2)
except ValueError:
    pass
else:
    raise AssertionError("vertex cap bypassed")
print("D02-F: BFS visits each node once")
```

**Trace:**

| Queue before pop | Node visited | Neighbors newly queued |
|---|---|---|
| [gateway] | gateway | web, database |
| [web, database] | web | app |
| [database, app] | database | none |
| [app] | app | gateway is already visited |

BFS/DFS traversal time is O(V+E) for an adjacency list when each vertex and edge is processed a bounded number of times; auxiliary space O(V), excluding the graph storage. For a huge attacker-controlled graph, cap vertices, neighbor counts and total edges. A cap hit must return **incomplete or error**, never silently return a seemingly complete reachability report.

**Independent task:** implement iterative DFS with a list as a stack; predict how its order differs from BFS. Then implement shortest unweighted path using a predecessor map. Use toy graphs only, not network exploration against real hosts.

## 2.13 Deep Core VII — Weighted graphs and Dijkstra's algorithm

If edges have different **nonnegative** costs (latency, distance or a synthetic effort score), BFS no longer guarantees the minimum total weight. Dijkstra's algorithm maintains best-known distances from a start node and repeatedly expands the smallest tentative distance using a min-heap.

**Core invariant:** Once the smallest-distance node is removed from the priority queue with a non-stale distance, nonnegative edge weights ensure that no later path can improve it. **Negative edges invalidate this argument**; reject them explicitly or choose a different algorithm with appropriate guarantees.

```python
# DEEP_CORE_RUNNABLE
from heapq import heappop, heappush
from math import isfinite

def dijkstra(graph: dict[str, dict[str, float]], start: str) -> dict[str, float]:
    if start not in graph or len(graph) > 100:
        raise ValueError("invalid start or vertex cap")
    distances = {start: 0.0}
    pending = [(0.0, start)]
    while pending:
        cost, node = heappop(pending)
        if cost != distances[node]:
            continue                # stale heap entry
        for neighbor, weight in graph[node].items():
            if neighbor not in graph:
                raise ValueError("unknown neighbor")
            if type(weight) not in (int, float) or not isfinite(weight) or weight < 0:
                raise ValueError("edge weight must be finite and nonnegative")
            candidate = cost + weight
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                heappush(pending, (candidate, neighbor))
    return distances

toy = {
    "A": {"B": 4.0, "C": 1.0},
    "B": {"D": 1.0},
    "C": {"B": 2.0, "D": 8.0},
    "D": {},
}
result = dijkstra(toy, "A")
assert result == {"A": 0.0, "C": 1.0, "B": 3.0, "D": 4.0}
try:
    dijkstra({"A": {"B": -1.0}, "B": {}}, "A")
except ValueError:
    pass
else:
    raise AssertionError("negative weight accepted")
print("D02-G: shortest path with nonnegative weights")
```

**Trace from A:** start A=0. Inspect edges A→C=1 and A→B=4. Expand C=1 and discover C→B=2, yielding B=3 (better than 4), and C→D=8, yielding D=9. Expand B=3 and improve D to 4 through B→D=1. Expand D=4. A stale queued candidate B=4 can be ignored.

**Complexity:** with an adjacency list and binary heap, roughly O((V+E) log V) is commonly cited when heap entries are managed appropriately, though this implementation can keep stale heap entries, giving bounds expressed with O((V+E) log(V+E)) for a simple accounting. Memory is O(V+E) for the input and up to O(E) heap entries in typical implementations. This algorithm is **not** a vulnerability graph risk model: adding arbitrary numbers to "severity" labels cannot make them legitimate path weights.

**Exercise:** add predecessor tracking to reconstruct A→C→B→D and explain why an unreachable node is absent from the returned dictionary. Add tests for zero weights, disconnected vertices, NaN and infinity. Show that your code never automatically queries real network topology.

## 2.14 Deep Core VIII — Dynamic programming: solve once, reuse the answer

Dynamic programming (DP) applies when a problem has **overlapping subproblems** and an **optimal substructure** property. Instead of calculating the same subproblem repeatedly, keep answers in a table (bottom-up) or cache them (top-down memoization).

An introductory example: minimum edit distance between two short strings using insertions, deletions and substitutions of cost 1. This measures **string distance**, not proof that two user identities refer to the same person. A machine-generated suggestion should be reviewed against authoritative identity records.

Define `dp[i][j]` as the minimum edits to convert the first `i` characters of `a` into the first `j` characters of `b`. The recurrence compares deletion (`dp[i-1][j]+1`), insertion (`dp[i][j-1]+1`), and substitution/match (`dp[i-1][j-1]+cost`).

```python
# DEEP_CORE_RUNNABLE
def edit_distance(a: str, b: str, max_length: int = 64) -> int:
    if (type(a) is not str or type(b) is not str
            or not 0 <= len(a) <= max_length or not 0 <= len(b) <= max_length):
        raise ValueError("bounded text required")
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,            # delete from a
                current[j-1] + 1,           # insert into a
                previous[j-1] + (char_a != char_b),  # substitute/match
            ))
        previous = current
    return previous[-1]

assert edit_distance("", "abc") == 3
assert edit_distance("kitten", "sitting") == 3
assert edit_distance("same", "same") == 0
try:
    edit_distance("x" * 65, "")
except ValueError:
    pass
else:
    raise AssertionError("unbounded dynamic-programming input accepted")
print("D02-H: recurrence and bounded DP table")
```

| Prefixes | Interpretation | Expected DP value |
|---|---|---:|
| empty → "a" | one insertion | 1 |
| "a" → "a" | exact match | 0 |
| "a" → "b" | one substitution | 1 |
| "ab" → "a" | one deletion | 1 |

**Complexity:** full DP table takes O(mn) time and O(mn) memory; the rolling-row implementation above takes O(mn) time and O(n) auxiliary list memory where `n=len(b)`. It still uses time proportional to the **product** of input lengths, which is why input bounds matter.

**Security reasoning:** edit-distance similarity may help an analyst investigate **possible** related strings, but automatically merging account IDs risks false matches and privilege errors. It must not be used as an authorization mechanism.

## 2.15 Deep Core IX — Deterministic priority queues, top K and fairness

A heap is a partially ordered tree-like array. With `heapq`, the smallest item is at index zero. `heappush`/`heappop` typically cost O(log N). A heap is not a fully sorted list; never assume iterating over it yields items in rank order. For top K, `heapq.nlargest(k, records, key=...)` is often useful when K is far smaller than N.

Tie-breaking matters: if two findings have the same severity, use a deterministic secondary key, such as timestamp and event ID, to make reports reproducible. Priority is not proof of maliciousness; a high-severity alert may be a false positive.

```python
# DEEP_CORE_RUNNABLE
import heapq

findings = [
    {"id": "C", "severity": 5, "time": 3},
    {"id": "A", "severity": 8, "time": 1},
    {"id": "B", "severity": 8, "time": 2},
    {"id": "D", "severity": 1, "time": 4},
]
ranked = sorted(findings, key=lambda r: (-r["severity"], r["time"], r["id"]))
assert [r["id"] for r in ranked] == ["A", "B", "C", "D"]
top_two = heapq.nsmallest(2, findings, key=lambda r: (
    -r["severity"], r["time"], r["id"]
))
assert [r["id"] for r in top_two] == ["A", "B"]
print("D02-I: deterministic priority order")
```

**Think deeper:** alert triage fairness may require policies beyond pure severity sorting. If analysts only ever work the highest-volume source, lower-volume critical signals may starve. A production queue needs an age policy, ownership, escalation and explicit workflow state, not just a heap.

## 2.16 Deep Core X — Streaming aggregation with honest resource limits

"Streaming" describes how input is consumed, not necessarily how much memory the *result* retains. A program that reads one JSONL line at a time but stores every unique user key can still use O(U) memory where U is distinct identities. An attacker generating one new actor per event can stress a detector more than a million events from the same actor.

Define resource budgets *before* implementing: total records, maximum bytes per record, maximum distinct actors, events retained per actor, time allowed, memory or disk budget, and output cap. A cap hit must be an error/incomplete state unless a safe lossy policy was deliberately specified.

```python
# DEEP_CORE_RUNNABLE
from collections import Counter

def bounded_counts(records, max_actors: int = 3):
    if type(max_actors) is not int or not 1 <= max_actors <= 100:
        raise ValueError("actor cap")
    count = Counter()
    for actor in records:
        if type(actor) is not str or not 1 <= len(actor) <= 16:
            raise ValueError("invalid actor")
        if actor not in count and len(count) >= max_actors:
            raise ValueError("actor cap exceeded: report incomplete")
        count[actor] += 1
    return count

assert bounded_counts(["a", "a", "b"]) == {"a": 2, "b": 1}
try:
    bounded_counts(["a", "b", "c", "d"])
except ValueError as exc:
    assert "incomplete" in str(exc)
else:
    raise AssertionError("cardinality overflow silently accepted")
print("D02-J: input streaming does not imply bounded aggregation")
```

**Engineering progression:** use a list/Counter for small fixtures, then a bounded deque for time windows, then disk-backed key/value state for large authorized feeds. You must still decide how to expire keys, handle late events, manage duplicates and record incomplete processing. SQLite transactions and source-qualified event IDs become relevant later in the curriculum.

## 2.17 Deep Core XI — Project: a deterministic offline burst detector

Build a CLI using a JSONL fixture of synthetic authentication events. Requirements:
1. Validate each event's exact JSON schema, UTF-8, byte count, source-qualified event ID, aware timestamp and action.
2. Require nondecreasing event times or declare a separate late-event strategy.
3. Keep bounded per-actor rolling windows for failed logins.
4. Deduplicate source/event IDs; do not silently ignore conflicting records.
5. Emit only one alert per continuous threshold crossing; re-arm correctly after event count drops.
6. On any invalid input or exceeded cap, leave the previous complete report intact and return an error.
7. Include supporting event references and explain that a *review alert* is not proof of compromise.

**Test trace:**

| Synthetic failures | Expected alerts | Why |
|---|---|---|
| at 0, 30, 60 sec | 1 | inclusive 60 sec boundary |
| at 0, 30, 60, 61 sec | 1 | replacement at threshold must not re-alert |
| at 0, 30, 61 sec | 0 | oldest expired before third |
| at 0, 30, 60, 200, 210, 220 | 2 | re-arm after count drops |
| malformed JSON after a valid burst | no new complete report | batch must fail visibly |

The [reference project](../projects/foundations/window_detector.py) and its [tests](../tests/test_foundations_projects.py) provide a tested baseline, but you should **build your solution first**. Run on a local fixture only; do not use the toy signal to lock accounts.

## 2.18 Deep Core XII — Independent exercise bank and answer separation

Solve [25 Data Structures & Algorithms exercises](../python/exercises/02-DATA-STRUCTURES-ALGORITHMS-EXERCISES.md), progressing through Big-O reasoning, implementation, boundary testing, graph paths, edit distance and detector engineering. A [separate worked solution key](../python/solutions/02-DATA-STRUCTURES-ALGORITHMS-SOLUTIONS.md) is provided for feedback after attempting each problem.

**Mastery gates:** describe time and auxiliary-space complexity; reproduce the algorithm's invariant; test empty/duplicate/boundary input; explain resource exhaustion for untrusted data; demonstrate a complete failure path rather than silently returning an empty result.

**What is not claimed:** learning BFS, Dijkstra and edit distance alone does not establish a cybersecurity practitioner's ability to identify attacks. These algorithms become useful only when the data sources, labels, authorization and problem model are sound.


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
