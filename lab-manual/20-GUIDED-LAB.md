# Lab 20 — Python caching, memory profiling and import safety

**Companion:** [Deep Dive Chapter 20](../course/20-ADVANCED-PYTHON-PERFORMANCE.md) · **Duration:** 2–5 hours · Python 3.11+ · **Authorization:** local, synthetic, owned data only.

## Why this lab exists

Two tenants use the same report ID and an optimization accidentally tries to share a cached result.

**Learning goal:** Show that cache keys need tenant context and that profiling must include input construction.

**Input assumptions:** two toy tenants with report ID r-1. Write down your data types, provenance and resource bounds before coding.

## Guided build

1. Verify Python runs: `python --version` from the repository root.
2. Run `python -m unittest discover -s tests -v` to establish a working baseline.
3. Copy this example into a temporary file `lab_20.py`.
4. Predict the output and two failure conditions without executing the code.
5. Run the example, note the real output, and then perform the negative tests below.

```python
from functools import lru_cache
import tracemalloc

records = {("A","r-1"):"A secret example",("B","r-1"):"B secret example"}

@lru_cache(maxsize=16)
def load(tenant, report_id):
    return records[(tenant, report_id)]

assert load("A","r-1") != load("B","r-1")
tracemalloc.start()
values = [str(i) for i in range(10_000)]
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
assert len(values) == 10_000
assert peak >= current
print("PASS: tenant-keyed cache and allocation measurement")
```

**Expected terminal result:** `PASS: tenant-keyed cache and allocation measurement`.

## Explain the code, not merely the output

1. Cache identity must include tenant, relevant principal/authorization scope and policy lifetime.
2. Start allocation tracking before creating the list; otherwise input memory would be invisible.
3. A cache improves speed only when its stale-data and security semantics are acceptable.

Draw a sequence diagram or trust-boundary sketch showing how the input becomes validated, which assumptions are still unverified, and where failure is surfaced.

## Defensive fault injection

1. Remove tenant from cache key in a local test double and demonstrate a collision.
2. Run tracemalloc after list creation and compare measured peak.
3. Explain why sys.getsizeof is shallow and why native allocations are not fully tracked.

Create an automated regression assertion for each meaningful failure. Where no executable test is reasonable, write a short design argument and the additional evidence a professional engineer would require.

## Worked solution and interpretation

Never cache authorization decisions indefinitely. Cache keys and invalidation must reflect tenant, scope, data mutation and permission revocation.

**Threat model / safety consideration:** Cross-tenant cache collisions can leak protected report content even with correct SQL and TLS.

This is an educational local exercise, not certification of a deployed service or a real security finding. Preserve provenance, uncertainty and privacy limits in every report.

## Independent challenge

**Tier 1 (2 pts):** reproduce the expected result on a clean environment and report your Python version.  
**Tier 2 (3 pts):** create three reproducible negative/boundary tests with expected vs observed results.  
**Tier 3 (3 pts):** refactor pure policy/logic away from I/O and document complexity and limits.  
**Tier 4 (2 pts):** produce a concise evidence-based analyst note, including alternative explanations.

**Pass:** ≥8/10 and no required negative test is silently skipped. Attach `lab_20.py`, a tests file, and `report_20.md` with exact commands, outcomes and limitations.
