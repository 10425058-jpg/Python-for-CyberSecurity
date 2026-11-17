# Python Foundations — Editorial and Engineering Review Standard

This rubric applies specifically to the twelve files in [the expanded Python textbook](../python/README.md), `python/00` through `python/11`. **Word count alone is not quality.** The aim is accurate explanations that let a beginner reason about real Python behavior and a more experienced learner identify safety and resource limits.

## The ten dimensions (0 = absent, 1 = partial, 2 = complete)

| Criterion | Question for the reviewer |
|---|---|
| First principles | Can a beginner understand the concept before any new jargon appears? |
| Correct syntax and semantics | Do Python snippets use valid behavior on supported versions? |
| Causal explanation | Is there an input→state→output trace, not just a result? |
| Contrasting cases | Are a normal and at least two wrong/boundary cases explained? |
| Learning progression | Does this build on prerequisites rather than assume advanced knowledge? |
| Resource limits | Are input size, time, memory and I/O considerations explained? |
| Security honesty | Are validation, provenance, authentication and authorization distinguished? |
| Reproducibility | Are interpreter version, commands and expected observations clear? |
| Independent practice | Are beginner, intermediate and advanced exercises transferable? |
| Maintenance | Are existing links preserved and assertions tested in CI? |

**Target:** at least 16/20 with no critical factual/safety errors for a chapter to pass a substantive editorial review. Automated checks do not grant this grade by themselves.

## What to verify by chapter

| Unit | Essential assessment |
|---|---|
| 00 | interpreter/editor/terminal, venv limitations, reproducible local example |
| 01 | identity vs equality, Boolean-int trap, Unicode and typed validation |
| 02 | dict/set/list/deque complexity, window boundary and notification latch |
| 03 | function contracts, imports, typed models and dependency injection |
| 04 | raw bytes vs text, UTF-8, strict JSON, byte caps and source hashes |
| 05 | exceptions vs valid-empty results, failed-input regression tests |
| 06 | instance vs class, composition, Protocols and object permission |
| 07 | iterator protocol, lazy evaluation, cleanup and async foundation |
| 08 | TaskGroup failure propagation, bounded queue and CPU/I/O distinctions |
| 09 | symlinks, subprocess execution, least privilege and read-only hashing |
| 10 | argparse, packaging, build-time code execution and supply chain |
| 11 | implementation details, profiling, cardinality and cache isolation |

## Additional review target for 01 and 02

The [extra-deep language chapter](../python/01-LANGUAGE-FOUNDATIONS.md) and [algorithm chapter](../python/02-DATA-STRUCTURES-ALGORITHMS.md) now include multiple independent runnable examples. Reviewers should verify that explanations of object aliasing, decimal/Boolean semantics, Unicode codepoints, closures, hash-key contracts, recursion, binary search, merge sort, graph traversal, Dijkstra and DP match their observed behavior. The [50 separate answer snippets](../python/solutions/README.md) and the [local project tests](../tests/test_foundations_projects.py) are executed by CI. **These tests supplement, not replace, independent human technical editing.**

## Test scope and honest limitations

[The textbook regression suite](../tests/test_python_textbook_chapters.py) executes the code block explicitly tagged `# TEXTBOOK_RUNNABLE` in each chapter, under a subprocess deadline and multiple supported Python interpreters. It verifies reproducibility of the *new main example*. It does not execute every legacy snippet or independently review every statement for currency.

Human reviewers should check Python-version-specific library behavior against [the official Python documentation](https://docs.python.org/3/) and inspect security claims against authoritative sources. No educational example constitutes authorization to scan external systems or a certificate of production security.
