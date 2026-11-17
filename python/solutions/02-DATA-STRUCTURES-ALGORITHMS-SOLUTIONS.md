# Chapter 02 — Worked Solutions to 25 Data Structures & Algorithms Exercises

These are **reference approaches**, not mandatory implementations. Read the [questions](../exercises/02-DATA-STRUCTURES-ALGORITHMS-EXERCISES.md) first; then run each Python block independently from the repository root. Do not use similarity or a toy detection signal as proof of identity or malice.

## Solution 02.01 — Choosing a container

**Expected result:** Four correct container matches and reasons.

```python
from collections import Counter,deque
history=['a','b']; seen={'a','b'}; queue=deque(history); counts=Counter(history)
assert list(queue)==history and 'a' in seen and counts['a']==1
```

**Reasoning:** The right choice depends on operation, not popularity.

**Cybersecurity/engineering limitation:** A set or Counter can still grow without cardinality limits.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.02 — Amortized append versus front delete

**Expected result:** Front removal shifts the list left.

```python
items=[1,2,3]
items.append(4)
assert items==[1,2,3,4]
assert items.pop(0)==1 and items==[2,3,4]
```

**Reasoning:** Operations with the same list have different costs.

**Cybersecurity/engineering limitation:** O(1) amortized does not mean every append takes identical time.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.03 — Ordered deduplication

**Expected result:** ['a','b','c'].

```python
rows=['a','b','a','c']
assert list(dict.fromkeys(rows))==['a','b','c']
assert set(rows)=={'a','b','c'}
```

**Reasoning:** Dict insertion order preserves first encounter, unlike relying on set iteration order.

**Cybersecurity/engineering limitation:** Do not discard duplicate evidence until replay semantics are defined.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.04 — Counter and classification

**Expected result:** Three failures for code 401.

```python
from collections import Counter
status=[401,200,401,401,201]
failures=Counter(s for s in status if s==401)
assert failures=={401:3}
```

**Reasoning:** Counter builds the frequency table from a chosen filter.

**Cybersecurity/engineering limitation:** Define what status means; an HTTP code is not proof of hostile traffic.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.05 — Deque and bounded recent history

**Expected result:** Last three are [3,4,5].

```python
from collections import deque
q=deque(maxlen=3)
for i in range(1,6): q.append(i)
assert list(q)==[3,4,5]
```

**Reasoning:** Deque maxlen evicts oldest when full.

**Cybersecurity/engineering limitation:** The bounded preview is not an immutable evidence archive.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.06 — Recursive factorial

**Expected result:** fact(5)=120, fact(0)=1.

```python
def fact(n):
    if type(n) is not int or not 0<=n<=100: raise ValueError('bounds')
    return 1 if n<2 else n*fact(n-1)
assert fact(0)==1 and fact(5)==120
try: fact(-1)
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** The recurrence makes progress toward 0 and stops.

**Cybersecurity/engineering limitation:** Recursion depth and integer size are resource considerations.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.07 — Memoized Fibonacci

**Expected result:** F(10)=55.

```python
from functools import lru_cache
@lru_cache(maxsize=50)
def fib(n):
    if type(n) is not int or not 0<=n<=40: raise ValueError('bounds')
    return n if n<2 else fib(n-1)+fib(n-2)
assert fib(10)==55
```

**Reasoning:** Repeated Fib(n-2) problems are cached instead of recomputed.

**Cybersecurity/engineering limitation:** The cache has a memory cost and should be bounded.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.08 — Linear search

**Expected result:** Index 2 for x in ['b','a','x'].

```python
def find(data,target):
    for i,v in enumerate(data):
        if v==target: return i
    return None
assert find(['b','a','x'],'x')==2
assert find(['b','a'],'x') is None
```

**Reasoning:** Worst-case all N elements are checked.

**Cybersecurity/engineering limitation:** No-match after a complete scan is different from a failed scan.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.09 — Lower-bound binary search

**Expected result:** Index 1 for 7.

```python
def leftmost(a,x):
    lo,hi=0,len(a)
    while lo<hi:
        mid=(lo+hi)//2
        if a[mid]<x: lo=mid+1
        else: hi=mid
    return lo if lo<len(a) and a[lo]==x else None
assert leftmost([3,7,7,11],7)==1
assert leftmost([3,7,7,11],8) is None
```

**Reasoning:** The invariant keeps the earliest qualifying position in [lo,hi).

**Cybersecurity/engineering limitation:** Unsorted input violates the algorithm contract.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.10 — bisect preconditions

**Expected result:** Insertion index 2.

```python
from bisect import bisect_left
items=[1,3,7]
assert bisect_left(items,5)==2
items.insert(2,5)
assert items==[1,3,5,7]
```

**Reasoning:** Binary search is logarithmic but inserting into a Python list is O(N).

**Cybersecurity/engineering limitation:** Never claim an insertion into a list is O(log N).

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.11 — Stable sorting

**Expected result:** earlier, first, second.

```python
events=[(2,'first'),(1,'earlier'),(2,'second')]
assert [x[1] for x in sorted(events,key=lambda x:x[0])]==['earlier','first','second']
```

**Reasoning:** Python's sort is stable, preserving tie order.

**Cybersecurity/engineering limitation:** Use original sequence positions as evidence metadata when available.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.12 — Implement merge sort

**Expected result:** [-1,1,2,3] sorted from [3,1,-1,2].

```python
def ms(a):
    if len(a)<2: return a.copy()
    k=len(a)//2; left=ms(a[:k]); right=ms(a[k:])
    out=[]; i=j=0
    while i<len(left) and j<len(right):
        if left[i]<=right[j]:
            out.append(left[i]); i+=1
        else:
            out.append(right[j]); j+=1
    return out+left[i:]+right[j:]
assert ms([3,1,-1,2])==[-1,1,2,3]
```

**Reasoning:** The merge uses index pointers instead of list.pop(0), preserving O(N log N) time for standard mergesort. Slices and output arrays add O(N) auxiliary storage.

**Cybersecurity/engineering limitation:** Use index pointers for efficient merging; incorrect complexity claims are bugs in documentation.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.13 — Heap priority top K

**Expected result:** ['A','B'].

```python
from heapq import nsmallest
rows=[('C',5,3),('A',8,1),('B',8,2)]
result=nsmallest(2,rows,key=lambda x:(-x[1],x[2],x[0]))
assert [x[0] for x in result]==['A','B']
```

**Reasoning:** Heaps can select K priorities efficiently without fully sorting for small K.

**Cybersecurity/engineering limitation:** Priority labels do not establish confidence or maliciousness.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.14 — Enumerated line numbers

**Expected result:** Error on line 2.

```python
def validate(rows):
    for n,action in enumerate(rows,1):
        if action not in ('success','failure'):
            raise ValueError(f'line {n}: invalid action')
try: validate(['success','bad','failure'])
except ValueError as e: assert 'line 2' in str(e)
else: raise AssertionError
```

**Reasoning:** Enumerate produces meaningful 1-based line references.

**Cybersecurity/engineering limitation:** Do not print raw credential-bearing lines in public errors.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.15 — Generator and bounded aggregation

**Expected result:** a:100, b:100; distinct cap rejects fourth actor.

```python
from collections import Counter
def count(rows,cap=3):
    result=Counter()
    for actor in rows:
        if actor not in result and len(result)>=cap: raise ValueError('cap')
        result[actor]+=1
    return result
assert count(('a' if n%2 else 'b' for n in range(200)))=={'a':100,'b':100}
try: count(iter(['a','b','c','d']))
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** Streaming consumption uses constant input-buffer memory, but the dictionary grows with unique actors.

**Cybersecurity/engineering limitation:** Cap overflow means incomplete, not zero findings.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.16 — Breadth-first search

**Expected result:** BFS [A,B,C,D].

```python
from collections import deque
g={'A':['B','C'],'B':['D'],'C':['A'],'D':[]}
def bfs(start):
    q=deque([start]); seen={start}; order=[]
    while q:
        x=q.popleft(); order.append(x)
        for y in g[x]:
            if y not in seen: seen.add(y); q.append(y)
    return order
assert bfs('A')==['A','B','C','D']
```

**Reasoning:** Each vertex is queued at most once; the cycle is harmless due to visited.

**Cybersecurity/engineering limitation:** Real asset graphs can contain unknown or misleading edges.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.17 — Iterative depth-first search

**Expected result:** Visits all four nodes exactly once.

```python
g={'A':['B','C'],'B':['D'],'C':['A'],'D':[]}
def dfs(start):
    stack=[start]; seen=set(); result=[]
    while stack:
        x=stack.pop()
        if x in seen: continue
        seen.add(x); result.append(x)
        stack.extend(reversed(g[x]))
    return result
assert dfs('A')==['A','B','D','C']
```

**Reasoning:** A LIFO stack explores depth first; reversal preserves the written neighbor priority.

**Cybersecurity/engineering limitation:** Cap graph size or visited-set cardinality for untrusted graphs.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.18 — Unweighted shortest path

**Expected result:** ['A','B','D'].

```python
from collections import deque
g={'A':['B','C'],'B':['D'],'C':['A'],'D':[]}
q=deque(['A']); prev={'A':None}
while q:
    x=q.popleft()
    for y in g[x]:
        if y not in prev:
            prev[y]=x; q.append(y)
path=[]; node='D'
while node is not None:
    path.append(node); node=prev[node]
assert path[::-1]==['A','B','D']
```

**Reasoning:** FIFO exploration finds the fewest edges for an unweighted graph.

**Cybersecurity/engineering limitation:** An absence of a path in incomplete topology is not proof of isolation.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.19 — Dijkstra's minimum cost

**Expected result:** A→C→B→D total cost 4.

```python
from heapq import heappush,heappop
g={'A':{'B':4,'C':1},'B':{'D':1},'C':{'B':2,'D':8},'D':{}}
def shortest(start):
    dist={start:0}; q=[(0,start)]
    while q:
        d,x=heappop(q)
        if d!=dist[x]: continue
        for y,w in g[x].items():
            if w<0: raise ValueError('negative weight')
            new=d+w
            if new<dist.get(y,float('inf')):
                dist[y]=new; heappush(q,(new,y))
    return dist
assert shortest('A')['D']==4
```

**Reasoning:** A heap repeatedly expands the smallest known tentative distance.

**Cybersecurity/engineering limitation:** Reject negative and nonfinite weights in real implementations.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.20 — Negative-weight counterexample

**Expected result:** Negative edge explicitly rejected.

```python
weights=[1.0,-0.5,2.0]
def require_nonnegative(values):
    for w in values:
        if w<0: raise ValueError('negative edge')
try: require_nonnegative(weights)
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** The shortest-distance finalization argument needs nonnegative weights.

**Cybersecurity/engineering limitation:** Do not silently adapt threat scores as if they were path distances.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.21 — Edit-distance DP

**Expected result:** Distance 3.

```python
def distance(a,b):
    if len(a)>64 or len(b)>64: raise ValueError('cap')
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        row=[i]
        for j,y in enumerate(b,1):
            row.append(min(prev[j]+1,row[-1]+1,prev[j-1]+(x!=y)))
        prev=row
    return prev[-1]
assert distance('kitten','sitting')==3
```

**Reasoning:** Rolling rows reduce auxiliary memory to O(len(b)) with O(mn) time.

**Cybersecurity/engineering limitation:** String similarity must never authorize identity merges.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.22 — Subset-sum dynamic programming

**Expected result:** [2,3,7] cannot make 9 unless 2+7; so yes.

```python
def reachable(values,target):
    if target<0 or target>100: raise ValueError('target')
    sums={0}
    for value in values:
        if type(value) is not int or value<=0: raise ValueError('value')
        sums|={s+value for s in sums if s+value<=target}
    return target in sums
assert reachable([2,3,7],9)
assert not reachable([2,3,7],6)
```

**Reasoning:** The set of attainable sums is updated per input item; each item is used at most once in this recurrence.

**Cybersecurity/engineering limitation:** An input cap and bounded target prevent exponential or huge-state behavior.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.23 — End-to-end complexity measurement

**Expected result:** Benchmark results positive; do not assert which run is faster.

```python
from timeit import repeat
seq=list(range(1000)); keys=set(seq)
a=repeat(lambda:999 in seq,number=100,repeat=3)
b=repeat(lambda:999 in keys,number=100,repeat=3)
assert len(a)==len(b)==3 and all(x>=0 for x in a+b)
```

**Reasoning:** A single microbenchmark doesn't prove asymptotic complexity; build costs and workload matter.

**Cybersecurity/engineering limitation:** Never claim performance from one unrepresentative measurement.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.24 — Detector actor and queue caps

**Expected result:** In-range toy events accepted and overflow raises.

```python
from collections import deque
q=deque(maxlen=3)
for x in (1,2,3): q.append(x)
assert list(q)==[1,2,3]
seen=set(['a','b'])
def add_actor(a,cap=2):
    if a not in seen and len(seen)>=cap: raise ValueError('incomplete')
    seen.add(a)
try: add_actor('c')
except ValueError: pass
else: raise AssertionError
```

**Reasoning:** The deque's maxlen silently drops an old item; this is appropriate only for an explicitly lossy preview.

**Cybersecurity/engineering limitation:** A detector needing full evidence must reject/record overflow, not silently truncate.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Solution 02.25 — Project readiness: source-qualified burst rules

**Expected result:** Two alerts for toy fixture, not three.

```python
from pathlib import Path
from projects.foundations.window_detector import analyze
r=analyze(Path('fixtures/foundations-auth.jsonl'))
assert r['complete'] and len(r['alerts'])==2
assert r['alerts'][0]['trigger_time_utc'].endswith('10:01:00+00:00')
```

**Reasoning:** Re-arm after post-arrival count dips below threshold to avoid duplicate alerts.

**Cybersecurity/engineering limitation:** A burst is only a review candidate, not proof of compromise.

**Transfer test:** alter the data so the precondition fails or an edge case is reached; explain why the reference must reject or change its output.

## Verification and next steps

Run `python -m unittest tests.test_foundations_deep_examples tests.test_foundations_projects -v`. The standalone snippets demonstrate expected outcomes on toy data; complete protection requires verified source provenance, authenticated identity, bounded state, and a reviewed operational policy.
