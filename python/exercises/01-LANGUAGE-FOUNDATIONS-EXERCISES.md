# Chapter 01 — 25 Independent Python Language Foundations Exercises

**Learn first:** [Python 01 — Language Foundations](../01-LANGUAGE-FOUNDATIONS.md). **Do not read the [solution key](../solutions/01-LANGUAGE-FOUNDATIONS-SOLUTIONS.md) until your own implementation passes.** Work entirely offline with synthetic data and Python 3.11+.

## How to submit

For each exercise provide: (a) source or written prediction, (b) exact Python command, (c) expected and observed output, (d) one normal and one negative/boundary assertion, and (e) a two-sentence explanation of the trust or correctness concern. Rubric: 4 correctness, 3 tests, 2 explanation, 1 reproducibility.

### Exercise 01.01 — Expression versus statement (Beginner)

**Task:** Explain why 2+3 produces a value but total=2+3 binds a name. Predict the value and type of total.

**Acceptance check:** total evaluates to integer 5. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.02 — Rebinding and in-place mutation (Beginner)

**Task:** Create two aliases of one list. Compare a=a+[3] with a += [3]; preserve reference identity tests.

**Acceptance check:** First creates a new list; second mutates aliased list. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.03 — Shallow versus deep copy (Beginner)

**Task:** Copy a list containing a nested dictionary. Change a nested value through the copy. Explain the outcome.

**Acceptance check:** A shallow copy shares nested dict objects. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.04 — Equality and identity (Beginner)

**Task:** Create two separately allocated lists with equal values; assert equality but not identity.

**Acceptance check:** == true; is false for distinct objects. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.05 — The bool-int inheritance trap (Beginner)

**Task:** Validate a signed integer count without accepting True, False, strings or floats. Test 0 and 100 as boundaries.

**Acceptance check:** Exact int type accepted only within 0..100. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.06 — Floating-point and Decimal (Beginner)

**Task:** Predict 0.1+0.2==0.3, then compare a calculation using decimal strings.

**Acceptance check:** Float comparison false; Decimal string computation exact. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.07 — Negative floor division (Beginner)

**Task:** Compute -7//2 and -7%2; explain the quotient-remainder identity.

**Acceptance check:** Quotient -4; remainder +1. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.08 — Presence is not truthiness (Beginner)

**Task:** A config accepts a legitimate zero limit. Write code that rejects missing but accepts zero.

**Acceptance check:** {'limit':0} is valid; {} is missing. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.09 — Short-circuit operators (Beginner)

**Task:** Predict outputs of 0 or 9, 'x' and 5, False and (1/0). Explain return value type.

**Acceptance check:** 9, 5, False; division never runs. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.10 — Chained comparisons (Beginner)

**Task:** Explain why 1 < x < 5 is not always the same as comparing two separately evaluated expressions.

**Acceptance check:** It evaluates x once in the chain. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.11 — Unicode code points versus bytes (Intermediate)

**Task:** Compare len('é'), len('é') and their UTF-8 byte lengths.

**Acceptance check:** 1 vs 2 code points; 2 vs 3 bytes. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.12 — Unicode normalization (Intermediate)

**Task:** Normalize composed/decomposed accented strings with NFC; explain why not to normalize every account identifier blindly.

**Acceptance check:** NFC makes the two example sequences equal. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.13 — Strict UTF-8 decoding (Intermediate)

**Task:** Show that b'\xff' rejects strict UTF-8 decoding rather than being silently dropped.

**Acceptance check:** UnicodeDecodeError raised. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.14 — Slicing and reverse traversal (Intermediate)

**Task:** Predict [0,1,2,3,4][1:4:2] and [0,1,2,3,4][::-1].

**Acceptance check:** [1,3] and [4,3,2,1,0]. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.15 — Comprehension versus generator (Intermediate)

**Task:** Transform bounded numbers with a comprehension and with a generator. Explain eager versus lazy memory.

**Acceptance check:** List built immediately; generator yields values as consumed. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.16 — Starred unpacking (Intermediate)

**Task:** Use head,*middle,tail with a sequence and test short input behavior.

**Acceptance check:** Middle is a new list; fewer than two items raises ValueError. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.17 — Enumerate and strict zip (Intermediate)

**Task:** Pair two columns, rejecting mismatched lengths with strict=True; preserve row numbers with enumerate.

**Acceptance check:** Mismatched lengths raise ValueError. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.18 — Loop else (Intermediate)

**Task:** Find an ID and return None when a full scan finds no match. Use a for/else example.

**Acceptance check:** No-match branch only after normal loop completion. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.19 — Structural pattern matching (Intermediate)

**Task:** Use match to recognize toy login action and reject unknown shapes. Explain extra-key acceptance.

**Acceptance check:** Mapping pattern can match a dictionary with extra fields. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.20 — Mutable default arguments (Intermediate)

**Task:** Demonstrate a shared default-list bug and rewrite using None.

**Acceptance check:** Two independent calls return separate lists. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.21 — Late-bound closures (Advanced)

**Task:** Create three callbacks in a for loop that return 0,1,2 rather than all 2.

**Acceptance check:** Bind i=i at function definition. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.22 — LEGB and nonlocal (Advanced)

**Task:** Implement a two-step counter closure using nonlocal; explain why this state is hidden from globals.

**Acceptance check:** Consecutive calls return 1 then 2. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.23 — Formatting and output context (Advanced)

**Task:** Format alice: 003, then HTML-escape a toy string. Explain why escaping is context-specific.

**Acceptance check:** alice: 003 and &lt;...&gt; for HTML text. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.24 — Schema-driven defensive parsing (Advanced)

**Task:** Validate a toy actor/action dict with exact keys and allowed values, including malformed types.

**Acceptance check:** Bad actor, unknown action, and extra field rejected. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

### Exercise 01.25 — Project readiness: complete log reporting (Advanced)

**Task:** Run the local reference auth_summary on the valid fixture and reject the invalid-third fixture. Confirm old output is preserved.

**Acceptance check:** 8 unique events and 7 failures for alex; malformed file fails. Include at least one wrong-input or edge case and write why it should fail or differ.

**No-copy hint:** Trace object types, binding changes and the relevant Python contract before running.

## Independent project challenge

Build your own local authentication summary with strict JSONL schema, source-qualified deduplication, bounded input, UTC normalization and explicit incomplete-input behavior. Compare only *afterward* with [reference code](../../projects/foundations/auth_summary.py) and [regression tests](../../tests/test_foundations_projects.py). Your code must preserve an existing complete report when the third input event is corrupt.

**Pass gate:** at least 20/25 exercises completed, including every type and Unicode failure question; additionally complete the project with all required negative cases. Passing does not prove production security.
