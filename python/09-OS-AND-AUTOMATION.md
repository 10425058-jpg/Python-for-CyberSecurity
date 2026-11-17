# 09 — Operating-system automation with Python
> **Expanded textbook (Beginner → Advanced):** This chapter now includes a first-principles lesson, a runnable local program, a reasoning trace, failure cases and graduated exercises. For additional specialized lessons, see: [concurrency async os automation](../course/08-CONCURRENCY-ASYNC-OS-AUTOMATION.md) · [endpoint os telemetry](../course/19-ENDPOINT-OS-TELEMETRY.md).



## Extended textbook 09 — Operating-system interfaces, privileges and reproducible automation

### 9.1 Python is a user-space process with real OS permissions

Your script runs as a process with a current working directory, environment variables, open file descriptors, permissions and usually an identity inherited from the account that started it. On Linux/macOS, UIDs/GIDs and discretionary permissions are relevant; on Windows, access tokens and ACLs affect access. The virtual environment does **not** lower privilege. A script run with administrator/root permission can damage files or reveal secrets even if its functions seem read-only.

Important standard-library modules: `os` and `pathlib` for paths and filesystem operations; `sys` for interpreter/process information; `subprocess` for child processes; `tempfile` for temporary files; `shutil` for copying; `stat` for modes; `platform` for runtime information; `signal` for process signals where supported; `datetime` for timestamps; `hashlib` for integrity summaries.

### 9.2 Paths and symlinks are not simple strings

A relative path such as `reports/today.json` is resolved relative to the process's working directory. An absolute path identifies a location in the current filesystem namespace. `resolve()` normalizes an existing path as the OS sees it, but a path can be replaced between a check and an open. A symlink can redirect reads outside the expected tree.

For an automated tool, define an **authorized root** and whether symlinks should be followed, check maximum file counts/byte lengths, record unreadable files as *incomplete*, and avoid silently skipping failures. Real adversarial path safety may require OS-specific handle-relative access and open-time flags; `Path.is_relative_to` and string-prefix checks alone cannot prevent all races.

### 9.3 Child processes: arguments are not shell source code

Prefer `subprocess.run([sys.executable, "--version"], check=True, capture_output=True, text=True, timeout=5)` over building a shell string. The argument list prevents the shell from interpreting metacharacters in ordinary cases, but still **does not** make a dangerous executable or arbitrary user-supplied arguments safe. Specify executable, timeout, working directory and environment policy. Capture stdout/stderr carefully; they may contain confidential information.

### 9.4 Hands-on read-only inventory

```python
# TEXTBOOK_RUNNABLE
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

def digest_file(path: Path, max_bytes: int = 1024 * 1024) -> str:
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid byte cap")
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected a regular non-symlink test file")
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while block := stream.read(4096):
            total += len(block)
            if total > max_bytes:
                raise ValueError("file too large")
            digest.update(block)
    return digest.hexdigest()

with TemporaryDirectory() as directory:
    path = Path(directory) / "owned.txt"
    path.write_text("synthetic log\n", encoding="utf-8")
    expected = hashlib.sha256(b"synthetic log\n").hexdigest()
    assert digest_file(path) == expected
    result = subprocess.run(
        [sys.executable, "--version"],
        check=True,
        text=True,
        capture_output=True,
        timeout=5,
    )
    assert "Python" in (result.stdout + result.stderr)
    path.write_text("changed\n", encoding="utf-8")
    assert digest_file(path) != expected
print("LAB 09 PASS")
```

**Step-by-step:** the code creates an owned temporary file, hashes it with fixed-size chunks and a per-file cap, then launches only the Python interpreter already executing the test. There is no arbitrary remote host or user-controlled command. When the file bytes change, the SHA-256 digest changes with overwhelming probability. **Security limits:** this sample checks a symlink before open, which is not race-proof; a privileged hostile filesystem could swap the target between checking and reading. It is educational, not evidence-grade acquisition.

### 9.5 Environment variables, secrets and process metadata

Environment variables are useful for configuration but not a guaranteed secret vault. They can be inherited by child processes or inspected by sufficiently privileged local tools. Do not print keys, tokens or personal paths in logs. Avoid passing secrets on command-line flags when processes may expose their argument vectors. Prefer a scoped secret-management mechanism for real deployments.

### 9.6 Safe automation is a two-phase workflow

**Discovery:** collect only approved, minimally necessary metadata. **Decision:** present findings with error status and source references. **Change:** only with explicit authorization, rollback plan, minimum privileges and auditable results. A health-check tool should default to read-only and dry-run when changes are possible.

### 9.7 Exercises and checkpoints

**Beginner:** Explain `cwd`, relative vs absolute paths, and the difference between stdout and stderr. **Intermediate:** Add test cases with Unicode filenames, spaces, empty files, missing paths and a file exceeding the cap. **Advanced:** Produce a deterministic directory manifest with added/removed/changed comparison, symlink handling, max-file count and visible incomplete state on any unreadable file. Compare with [the tested inventory project](../projects/BUILD-PATH.md).

**Mastery gate:** explain who authorizes the tool, what OS privileges it has, how arguments cross into subprocesses, what path and symlink risks remain and which observed facts can legitimately be concluded from a hash.

## Core libraries
`os`, `sys`, `pathlib`, `shutil`, `tempfile`, `subprocess`, `signal`, `platform`, `stat`, `getpass`, `logging`, `time` and `datetime`. Learn filesystem permissions, process ownership, environment variables, UIDs/GIDs, Windows tokens, services, scheduled jobs, and shell quoting.

```python
import subprocess
result = subprocess.run(
    ["python", "--version"],
    check=True, text=True, capture_output=True, timeout=5
)
print(result.stdout or result.stderr)
```

**Never** form shell commands by concatenating user input and `shell=True`. Prefer argument arrays, fixed executable paths where possible, per-command timeouts, and least privilege. Note that even `shell=False` does not make an unsafe command or untrusted executable safe.

## Filesystem safety
A path may refer to a symlink; checking then opening creates a time-of-check/time-of-use race. For sensitive operations, use OS-specific secure file APIs and file-descriptor-relative checks. Do not follow arbitrary user-controlled paths into protected areas. Use `tempfile.TemporaryDirectory` and atomic replace patterns where appropriate.

## Defensive automation examples
- Periodic checksum baseline generation for a configured folder.
- Inventory file ownership and weak permission modes on owned hosts.
- Rotate/normalize logs while preserving retention and audit requirements.
- Check whether a known local service listens on a configured port.
- Gather system configuration for an approved compliance checklist.
- Monitor disk pressure and backup freshness without leaking private filenames.

## Security boundaries
Automation often runs with privileged accounts. Split discovery from remediation, default to read-only, require confirmation for high-impact changes, maintain dry-run mode, write immutable logs where supported, and provide rollback. Limit processes' network/file privileges and never embed passwords in source.

## Exercises
1. Write a read-only directory inventory with path, size, modification time and SHA-256.
2. Build a subprocess wrapper with timeout and explicit error reporting.
3. Test paths with spaces, Unicode, symlinks, and missing permissions.
4. Explain why `subprocess.run(["tool", user_value])` is safer than a shell string but still needs validation.

References: [subprocess](https://docs.python.org/3/library/subprocess.html), [pathlib](https://docs.python.org/3/library/pathlib.html).
