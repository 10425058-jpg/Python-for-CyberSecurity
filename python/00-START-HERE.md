# Start here: Python for Cybersecurity
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [readme](../course/README.md).


> Track A: programming fundamentals → Track B: systems and networking → Track C: defensive engineering → Track D: advanced specialization.


## Extended textbook 00 — From zero to a reproducible Python laboratory

### 0.1 What exactly are you installing?

**Python** is both a programming language (the rules for writing a program) and a family of implementations that execute those rules. **CPython** is the standard implementation used by the examples in this course. Your editor is not the interpreter: VS Code can edit text, while the Python executable reads and runs that text.

When you type `python hello.py`, the operating system launches an interpreter process, and the interpreter executes the top-level statements of `hello.py`. A project usually has four distinct things: **source code**, an **interpreter**, optional **third-party packages**, and **runtime data**. Mixing them causes confusing "module not found" errors, unreproducible machines and accidental credential exposure.

| Term | First-principles meaning | Beginner mistake |
|---|---|---|
| `.py` file | Python source text | believing it executes just by being saved |
| Terminal/shell | program that starts other programs | confusing a shell command with Python syntax |
| Interpreter | process that executes Python | using a different Python version than the editor |
| `pip` | package installer associated with an interpreter | installing into the wrong environment |
| `venv` | isolated location for package installation | thinking it is a security sandbox |
| `sys.path` | ordered import search locations | placing untrusted files where imports can find them |
| Git | version control history | accidentally committing `.env` files |

### 0.2 Verify the environment one command at a time

In a terminal, find a **Python 3.11+** installation. On Windows, `py -3 --version` often works; on Linux/macOS, `python3 --version` is common. Use the interpreter *you actually selected* to create a virtual environment:

```bash
# Windows PowerShell (from your project directory)
py -3 -m venv .venv
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip --version

# Linux/macOS (from your project directory)
python3 -m venv .venv
.venv/bin/python --version
.venv/bin/python -m pip --version
```

Using the virtual environment's Python executable directly avoids relying on shell activation. **Only run the block for your operating system.** Avoid global `sudo pip install` for the exercises. The virtual environment keeps package installations separate, but Python programs inside it still have your user's filesystem and network privileges; it does **not** sandbox untrusted code.

Create a project folder with `hello.py`, `tests/`, a Markdown lab notebook, and `.gitignore` containing `.venv/`, `__pycache__/` and secrets such as `.env`. Use Git commits to capture small, testable milestones.

### 0.3 The smallest complete program

```python
# TEXTBOOK_RUNNABLE
"""First reproducible, entirely local cybersecurity-flavored Python program."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

assert sys.version_info >= (3, 11)

def classify_count(count: int) -> str:
    """Return a label for a synthetic authentication failure count."""
    if type(count) is not int or not 0 <= count <= 1000:
        raise ValueError("count must be an integer in [0,1000]")
    return "review" if count >= 3 else "observe"

with TemporaryDirectory() as folder:
    path = Path(folder) / "toy-event.json"
    path.write_text(json.dumps({"actor": "student", "failures": 3}), encoding="utf-8")
    document = json.loads(path.read_text(encoding="utf-8"))
    assert type(document) is dict and set(document) == {"actor", "failures"}
    assert classify_count(document["failures"]) == "review"
    print("LAB 00 PASS: 3 failures -> review")
```

**Predict before execution:** Is `document` a file or a dictionary? Does `write_text` write bytes or textual characters? What does the function return for zero? Which statement stops the program if a requirement fails?

**Step-by-step trace:** (1) `TemporaryDirectory` allocates a disposable folder, not a privileged location. (2) `json.dumps` converts a dictionary into JSON text. (3) `write_text` encodes that text to UTF-8 on disk. (4) `read_text` reads the text back; `json.loads` produces a dictionary. (5) The validator rejects boolean counts even though `isinstance(True, int)` is true. (6) `assert` checks a learning invariant and prints the exact terminal signal on success. For **production validation**, use explicit exceptions, not assertions: `python -O` can disable assertions.

**Expected output:** `LAB 00 PASS: 3 failures -> review`. This is a *toy review label*, not a conclusion that someone attacked a real account.

### 0.4 Running programs, modules and tests

These three commands do different things:

- `python path/to/script.py` executes that file as the main script.
- `python -m package.module` imports and runs a named module through the selected interpreter, useful for packages.
- `python -m unittest discover -s tests -v` searches for standard-library unit tests and reports pass/fail status.

The working directory influences relative file paths, while the selected interpreter and import path influence which modules load. Keep commands in the project README, including the exact version and the expected output. If an import fails, inspect `sys.executable` and the project layout before randomly installing more packages.

### 0.5 A weekly practice protocol: understand, modify, break, repair

At **10 hours per week**, use two hours reading/diagramming, four hours writing programs, two hours on intentional failure tests, one hour writing lab notes, and one hour revising mistakes. One meaningful program that you can explain is more valuable than hundreds of lines copied from an assistant.

**Foundational exercise:** Change the failure count to 0, 2, 3, 4 and 1001; predict each result. **Intermediate exercise:** replace the count with `True`, `"3"` and `None`; confirm which guard rejects each. **Advanced exercise:** write an import-safe `main(argv=None)` function using `argparse` and exit with a nonzero status on invalid data. In every exercise, preserve exact commands and observed outputs.

### 0.6 Readiness checklist and knowledge map

You are ready for Chapter 01 when you can: (a) distinguish interpreter/editor/terminal, (b) create and select a virtual environment, (c) run a program and a unit test, (d) explain where local file data comes from, (e) predict a normal and a malformed input, and (f) describe why a virtual environment is **not** a containment boundary.

The upcoming chapters move from **values and control flow → collections and algorithmic costs → reusable modules and typing → bytes/files/parsers → errors/testing → architecture → lazy iteration → concurrency → OS automation → packaging → profiling and Python internals**. Review [the 22 Deep Dive courses](../course/README.md) when you want a second angle, but master the fundamentals here first.

## Outcomes and boundaries
After the foundational track, you should be able to write maintainable Python, transform security telemetry, build local diagnostic tools, and explain why a tool is safe. After the security tracks, you should be able to design, test, and document useful blue-team automation. No single handbook makes someone an expert: practical experience, operating-system fundamentals, networking, and incident judgment are essential.

**Authorization first.** Run network experiments against loopback, owned VMs, or systems for which you have written permission. Treat collected traffic and logs as sensitive. Never upload production credentials or third-party packet captures. All active exercises default to isolated lab environments.

## Environment and prerequisites
- A supported Python 3 release (prefer a maintained stable version), Git, VS Code or another editor.
- A shell (Bash, PowerShell), a Git repository, and the ability to make a virtual environment.
- Recommended: Linux VM with snapshots, Windows VM for event-log study, and an isolated virtual network.
- A personal notebook: record commands, hypotheses, screenshots, expected results, observed results, and limitations.

### Start a virtual environment
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python --version
python -m unittest discover -s tests -v
```

Do not execute fetched scripts blindly; verify sources and pin dependency versions for reproducible builds. Nothing in the standard-library examples needs paid services.

## Recommended sequence
1. `01–11`: master Python syntax, data handling, typing, file processing, tests, OOP, async and packaging.
2. `security/01–12`: understand boundaries, logs, networks, web apps, crypto, IR, detection, cloud, malware triage, and threat intelligence.
3. `labs/`: complete reproducible, local exercises; write a report for each.
4. `projects/`: extend and test the reference programs.
5. `reference/`: review the library map, exercises, glossary, and study schedule.

## Definition of done for a topic
- Explain **what it does**, **why it is used**, **how it can fail**, and **how to test it**.
- Implement at least one script without copying code.
- Add tests for normal, edge, and error cases.
- Document input assumptions, output format, required privileges, and privacy impact.
- Demonstrate that your code fails closed or safely when data is malformed.

## Learning method: 10 hours/week
- 2 h reading, 4 h building, 2 h debugging/testing, 1 h documenting, 1 h reviewing.
- Keep a small evidence-based portfolio. Compare observations with reference baselines, not intuition.
- Prefer official references: [Python documentation](https://docs.python.org/3/), [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/), [NIST CSRC](https://csrc.nist.gov/).
