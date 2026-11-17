# Chapter 02 — 25 Independent Data Structures & Algorithms Exercises

**Study first:** [Python 02 textbook](../02-DATA-STRUCTURES-ALGORITHMS.md). **Check [the separate worked solutions](../solutions/02-DATA-STRUCTURES-ALGORITHMS-SOLUTIONS.md) only after trying the exercises.** Use local data, Python 3.11+ and explicit complexity bounds.

## General acceptance rubric

State the input preconditions, algorithm invariant, expected result, time complexity, auxiliary-space complexity, and how the code handles empty/duplicate/bad input. Write at least one negative test. Score: correctness 4, negative tests 3, explanation 2, reproducibility 1.

### Exercise 02.01 — Choosing a container (Beginner)

**Implement/explain:** Given a recent-window queue, a unique-ID index, an ordered event archive and a frequency table, choose deque, set, list and Counter respectively.

**Expected outcome:** Four correct container matches and reasons.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.02 — Amortized append versus front delete (Beginner)

**Implement/explain:** Explain why list.append is amortized O(1) and list.pop(0) usually O(N); demonstrate the different results.

**Expected outcome:** Front removal shifts the list left.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.03 — Ordered deduplication (Beginner)

**Implement/explain:** Deduplicate ['a','b','a','c'] while preserving first appearance, and contrast with set.

**Expected outcome:** ['a','b','c'].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.04 — Counter and classification (Beginner)

**Implement/explain:** Count failure status values among toy records, ignoring successful records.

**Expected outcome:** Three failures for code 401.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.05 — Deque and bounded recent history (Beginner)

**Implement/explain:** Keep only the last three values from five inputs and explain maxlen behavior.

**Expected outcome:** Last three are [3,4,5].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.06 — Recursive factorial (Beginner)

**Implement/explain:** Implement factorial with a base case and reject negative, Boolean, or excessive values.

**Expected outcome:** fact(5)=120, fact(0)=1.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.07 — Memoized Fibonacci (Beginner)

**Implement/explain:** Compute F(10)=55 using a memoization cache; explain subproblem overlap.

**Expected outcome:** F(10)=55.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.08 — Linear search (Beginner)

**Implement/explain:** Return the first index of a target from an unsorted list or None if absent.

**Expected outcome:** Index 2 for x in ['b','a','x'].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.09 — Lower-bound binary search (Intermediate)

**Implement/explain:** Find the first 7 in [3,7,7,11], return None for missing. Document sorted input requirement.

**Expected outcome:** Index 1 for 7.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.10 — bisect preconditions (Intermediate)

**Implement/explain:** Use bisect_left to find where 5 should be inserted in [1,3,7]; explain why it requires sorted input.

**Expected outcome:** Insertion index 2.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.11 — Stable sorting (Intermediate)

**Implement/explain:** Sort timestamp/source pairs by timestamp, keeping source order for ties.

**Expected outcome:** earlier, first, second.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.12 — Implement merge sort (Intermediate)

**Implement/explain:** Implement a non-mutating divide-and-conquer sort for integers.

**Expected outcome:** [-1,1,2,3] sorted from [3,1,-1,2].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.13 — Heap priority top K (Intermediate)

**Implement/explain:** Pick two highest-severity findings, breaking ties by earlier timestamp.

**Expected outcome:** ['A','B'].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.14 — Enumerated line numbers (Intermediate)

**Implement/explain:** Validate a list of parsed lines and report the exact line number of the first invalid action.

**Expected outcome:** Error on line 2.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.15 — Generator and bounded aggregation (Intermediate)

**Implement/explain:** Stream repeated actor strings and count them without storing all inputs; cap distinct actor names.

**Expected outcome:** a:100, b:100; distinct cap rejects fourth actor.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.16 — Breadth-first search (Intermediate)

**Implement/explain:** Traverse a cyclic toy graph from A using a queue and visited set.

**Expected outcome:** BFS [A,B,C,D].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.17 — Iterative depth-first search (Intermediate)

**Implement/explain:** Implement DFS with a list stack and visited set; explain order dependence on neighbor push order.

**Expected outcome:** Visits all four nodes exactly once.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.18 — Unweighted shortest path (Advanced)

**Implement/explain:** Return the shortest number-of-edges path from A to D using BFS predecessor tracking.

**Expected outcome:** ['A','B','D'].

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.19 — Dijkstra's minimum cost (Advanced)

**Implement/explain:** Implement Dijkstra for nonnegative toy weights and reject a negative edge.

**Expected outcome:** A→C→B→D total cost 4.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.20 — Negative-weight counterexample (Advanced)

**Implement/explain:** Show that negative weights invalidate Dijkstra's premise; name Bellman-Ford as a possible alternative.

**Expected outcome:** Negative edge explicitly rejected.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.21 — Edit-distance DP (Advanced)

**Implement/explain:** Compute Levenshtein distance from kitten to sitting, with bounded lengths.

**Expected outcome:** Distance 3.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.22 — Subset-sum dynamic programming (Advanced)

**Implement/explain:** Decide whether a bounded set of positive values can sum to target 9.

**Expected outcome:** [2,3,7] cannot make 9 unless 2+7; so yes.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.23 — End-to-end complexity measurement (Advanced)

**Implement/explain:** Benchmark list membership vs set membership while excluding set construction, then explain total costs separately.

**Expected outcome:** Benchmark results positive; do not assert which run is faster.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.24 — Detector actor and queue caps (Advanced)

**Implement/explain:** Simulate a bounded per-actor deque; reject excessive actors or excessive retained failures.

**Expected outcome:** In-range toy events accepted and overflow raises.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

### Exercise 02.25 — Project readiness: source-qualified burst rules (Advanced)

**Implement/explain:** Run the offline reference detector. Confirm two alerts and no repeated alert when the old event at t=0 expires and t=61 arrives.

**Expected outcome:** Two alerts for toy fixture, not three.

**Required reasoning:** State why your chosen structure or algorithm is appropriate, how its cost grows, and what happens when the preconditions are violated. Supply a normal and malformed/boundary assertion.

## Advanced capstone: offline bounded burst detector

Implement the full [Chapter 02 project contract](../02-DATA-STRUCTURES-ALGORITHMS.md) without looking at the [reference detector](../../projects/foundations/window_detector.py). Required cases: inclusive 60-second boundary, re-arm after a genuinely low count, source-qualified deduplication, out-of-order input, maximum actors, maximum deque length, conflicting duplicate IDs and atomic output preservation on malformed input. Use only the [synthetic fixture](../../fixtures/foundations-auth.jsonl).

**Pass gate:** at least 20/25 independent exercises plus all failure-path requirements of the capstone. This supports algorithmic engineering, not live incident attribution.
