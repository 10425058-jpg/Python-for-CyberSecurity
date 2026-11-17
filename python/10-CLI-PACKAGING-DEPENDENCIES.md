# 10 — CLI engineering, distribution and software supply chain
> **Need more depth?** This is the quick-reference chapter. Continue with fully explained English lessons, worked examples, negative tests and practical exercises: [testing ci and supply chain](../course/07-TESTING-CI-AND-SUPPLY-CHAIN.md).



## Extended textbook 10 — Make a Python script installable, testable and safe to operate

### 10.1 A command-line interface is an API

A good CLI defines its **arguments**, output schema, error codes and predictable help text just as carefully as a web API. `argparse` converts command-line text into typed options; it does not automatically enforce every business or security constraint. Use `--help`, descriptive errors, explicit limits and a documented output format.

A useful convention: stdout contains machine-readable success output, stderr contains diagnostics, exit code `0` means completion, and a nonzero code means the operation failed or was incomplete. Do not print a partial JSON document and exit zero after a mid-stream parser error.

### 10.2 A pure CLI core you can test without process launching

```python
# TEXTBOOK_RUNNABLE
from argparse import ArgumentParser
import json
from pathlib import Path
from tempfile import TemporaryDirectory

def parse_cli(argv: list[str]):
    parser = ArgumentParser(description="Synthetic read-only input checker")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be 1..1000")
    return args

def summarize(path: Path, limit: int) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected local non-symlink file")
    total = 0
    with path.open("rb") as stream:
        while True:
            line = stream.readline(1025)
            if not line:
                break
            if len(line) > 1024:
                raise ValueError("record byte limit")
            total += 1
            if total > limit:
                raise ValueError("too many records")
    return {"complete": True, "records": total}

with TemporaryDirectory() as directory:
    path = Path(directory) / "test.txt"
    path.write_bytes(b"first\nsecond\n")
    args = parse_cli(["--input", str(path), "--limit", "3", "--format", "json"])
    report = summarize(args.input, args.limit)
    assert json.loads(json.dumps(report)) == {"complete": True, "records": 2}
    try:
        summarize(path, limit=1)
    except ValueError:
        pass
    else:
        raise AssertionError("record cap ignored")
print("LAB 10 PASS")
```

**Trace:** `parse_args` recognizes options and converts `--limit` from text into an integer. The program performs a separate range check. The reader uses binary `readline` with a byte cap; it counts complete lines and refuses a file with more records than the requested limit. The result is structured data that a CLI adapter could print as JSON, while errors would map to a nonzero status. **Limitation:** counting lines alone does not validate JSONL; never call this example a secure event parser.

### 10.3 Build a tiny package, not an unstructured pile of scripts

```text
toytool/
  pyproject.toml
  src/toytool/
    __init__.py
    cli.py
    core.py
  tests/
    test_core.py
  README.md
  .gitignore
```

A minimal modern `pyproject.toml` example (for a project using setuptools) illustrates metadata and a console entry point:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "toy-local-inventory"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.scripts]
toy-inventory = "toytool.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

This is a **skeleton**; it requires corresponding source files and an import-safe `main` function. `pip install -e .` installs an editable development package in the selected environment; do not run it on untrusted repositories. Build/install backends and imported package code may execute code. Always understand what is being installed and the rights of the build process.

### 10.4 Dependency versions and supply-chain boundaries

A virtual environment isolates package directories but not your filesystem or credentials. For published applications, record direct/transitive dependencies, constrain versions appropriately, verify releases or hashes when supported, and review security advisories and provenance. Python packages use PEP 440 version rules: `"1.10"` is newer than `"1.2"` by version semantics even though naive string ordering can imply otherwise. Package metadata, build artifacts and dependency lockfiles answer different questions.

Do not put a production API token in `pyproject.toml`, `README.md`, command examples or CI logs. An application dependency or build hook can execute code during installation, so use reviewed sources, least-privilege build identities and isolation for untrusted contributions.

### 10.5 CI is part of software behavior

A basic project pipeline should run syntax validation, unit/integration tests, lint/type checks where configured, and dependency reviews. CI must protect its own credentials: a workflow running an untrusted pull request should not receive deployment keys. A green pipeline proves **tested behavior**, not that the project is invulnerable.

### 10.6 Exercises and release checklist

**Beginner:** Implement `main(argv=None)` so `--help` works and an invalid limit returns a nonzero exit code. **Intermediate:** Package a small log parser using the tree above; write unit tests and a README with exact install/run commands. **Advanced:** Add a CI matrix for supported Python versions, a dependency audit and a release checklist verifying artifact integrity, package provenance, import-time side effects and secret handling.

**Mastery gate:** explain why `python -m pip` is associated with the selected interpreter, what an editable install does, how `pyproject.toml` differs from source code, and what you must verify before distributing a command used in security operations.

## CLI design
Use `argparse` for clear options, validation, help text and exit codes. Define stable output formats (JSONL/CSV), stderr for errors, and stdout for machine-readable results. Never echo tokens passed through flags.

```python
from argparse import ArgumentParser
from pathlib import Path

def main() -> int:
    parser = ArgumentParser(description="Read-only local file inventory")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error("directory must exist")
    print(args.directory.resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

## Project structure
```text
tool/
  pyproject.toml
  README.md
  src/package_name/__init__.py
  src/package_name/cli.py
  src/package_name/core.py
  tests/test_core.py
```

## Dependency management
`venv` isolates Python environments but is **not a security sandbox**. `pip` installs third-party code which may execute during build/install. Review maintainers, pin and hash dependencies in controlled deployments, keep lockfiles, inventory transitive dependencies, generate SBOMs where useful, and update affected packages. Check official sources and advisories rather than trusting download counts.

## CI/CD
- Trigger unit tests and type checks on PR.
- Run SAST (e.g. Bandit) and dependency audit; triage, don't blindly suppress.
- Protect credentials with least-privilege CI identities.
- Require review on workflow changes; do not expose secrets to untrusted PR code.
- Build artifacts reproducibly and document provenance and signing where practical.
- Define responsible disclosure and a private security contact.

## Exercises
1. Package an event parser as a `console_scripts` entry point.
2. Add `--help`, `--json`, `--limit` and correct nonzero error codes.
3. Write a pipeline that checks tests, lint, and minimum supported Python.
4. Explain why dependency pinning, signing, and vulnerability scanning address different risks.
References: [packaging user guide](https://packaging.python.org/), [pip](https://pip.pypa.io/).
