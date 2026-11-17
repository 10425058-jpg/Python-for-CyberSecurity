# Complete Python Foundations Textbook — Modules 00–11

**Learning track:** from zero to advanced Python software engineering skills used in cybersecurity. All chapters are in **English** and expand the twelve exact Markdown files in this directory. Keep the existing supporting material, but work through the new `Extended textbook` section in every chapter first.

## Chapter-by-chapter learning path

| Unit | Direct link | Core competency |
|---|---|---|
| 00 | [Chapter 00](00-START-HERE.md) | Setup, interpreter, venv and reproducible labs |
| 01 | [Chapter 01](01-LANGUAGE-FOUNDATIONS.md) | Expressions, types, branches, loops and Unicode |
| 02 | [Chapter 02](02-DATA-STRUCTURES-ALGORITHMS.md) | Lists, dictionaries, sets, complexity and bounded queues |
| 03 | [Chapter 03](03-FUNCTIONS-MODULES-TYPING.md) | Functions, modules, typing, dataclasses and interfaces |
| 04 | [Chapter 04](04-FILES-ENCODING-PARSING.md) | Files, raw bytes, JSON/CSV parsing and evidence safety |
| 05 | [Chapter 05](05-EXCEPTIONS-TESTING-DEBUGGING.md) | Exceptions, tests, debugging and observability |
| 06 | [Chapter 06](06-OOP-AND-ARCHITECTURE.md) | Classes, composition, architecture and authorization |
| 07 | [Chapter 07](07-ITERATORS-ASYNC-FOUNDATIONS.md) | Iterators, generators, context managers and async concepts |
| 08 | [Chapter 08](08-CONCURRENCY-AND-ASYNCIO.md) | Threads, processes, asyncio, backpressure and failure propagation |
| 09 | [Chapter 09](09-OS-AND-AUTOMATION.md) | OS automation, filesystem, permissions and subprocesses |
| 10 | [Chapter 10](10-CLI-PACKAGING-DEPENDENCIES.md) | CLI design, pyproject.toml, dependency trust and CI |
| 11 | [Chapter 11](11-INTERNALS-PERFORMANCE-ADVANCED.md) | CPython internals, profiling, memory, caching and resource limits |

## Special focus: Deep Core 01 and 02

Chapters **01** and **02** now contain an extensive extra learning layer beyond their prior Extended Textbook lessons. Start with the concept and trace tables, run each of the **19 new `# DEEP_CORE_RUNNABLE` snippets**, then solve the **[50 independent exercises](exercises/README.md)** before opening the **[separate solutions](solutions/README.md)**.

The [two full local defensive projects](../projects/foundations/README.md) connect these concepts to JSONL parsing, bounded queues, UTC event-time windows, error propagation and atomic reporting. Their [regression tests](../tests/test_foundations_projects.py) cover malformed input, duplicate event IDs, thresholds, resource caps and previous-report preservation.

**Important scope:** Other chapters (00, 03–11) retain their existing Expanded Textbook content; the extra-deep 01–02 pass is a starting milestone, not a completeness claim for all of Python.

## A realistic schedule at 10 hours per week

**Weeks 1–2:** Chapters 00–01. Configure your interpreter and write/trace the first complete programs.  
**Weeks 3–4:** Chapters 02–03. Learn collection choices, algorithm costs, function contracts and import-safe design.  
**Weeks 5–6:** Chapters 04–05. Parse bounded bytes, distinguish syntax from source trust, and write tests that catch malformed data.  
**Weeks 7–8:** Chapters 06–07. Design cooperating objects and streaming iterators that clean up resources.  
**Weeks 9–10:** Chapters 08–09. Use concurrency selectively and operate safely at the OS/process boundary.  
**Weeks 11–12:** Chapters 10–11. Package a CLI, understand supply-chain risks, profile code and enforce resource budgets.  
**Weeks 13–14 (optional):** Rebuild one defensive local tool from scratch with tests, a threat model and reproducible demonstration.

This is a suggested learning pace, not a guarantee of senior-level proficiency. Revisit chapters until you can explain the failure paths without copying the answer.

## How to study a chapter

First read each definition and state table. Before executing the `# TEXTBOOK_RUNNABLE` example, predict its output and the exceptions for invalid inputs. Run the example, change one input at a time, and add your own negative test. Then solve the **beginner, intermediate and advanced** extensions, document the exact Python version and commands, and explain what your evidence *does not* establish about security.

Run from the repository root:

```bash
python tools/verify_curriculum.py
python -m unittest tests.test_python_textbook_chapters -v
python -m unittest discover -s tests -v
```

The [dedicated test harness](../tests/test_python_textbook_chapters.py) executes one standalone standard-library example per expanded module in CI. Other retained snippets may be didactic fragments or optional-dependency examples and are not all executed by this test. The [editorial review rubric](../reference/PYTHON-FOUNDATIONS-TEXTBOOK-RUBRIC.md) distinguishes technical and pedagogical review.

## Before you move to Cybersecurity-specific chapters

You should be able to: (1) validate input type/range/size; (2) select a data structure based on cost and invariants; (3) separate untrusted parsing from trusted domain models; (4) write normal and negative tests; (5) manage resources and cancellation explicitly; (6) handle incomplete data without reporting success; and (7) build and document an import-safe CLI.

Continue to the [22-unit Deep Dive](../course/README.md), [guided practical labs](../lab-manual/README.md), [100 exercise solutions](../solutions/by-exercise/README.md), and [progressive portfolio projects](../projects/BUILD-PATH.md).
