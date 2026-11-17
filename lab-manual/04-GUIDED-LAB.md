# Lab 04 — Binary protocol framing with structured reject paths

**Paired lesson:** [Chapter 04](../course/04-BYTES-ENCODING-BINARY-PARSERS.md)  
**Time:** 2–4 hours · **Prerequisite:** Python 3.11+, repository root · **Safety:** synthetic/local data only.

## Mission and acceptance contract

**Situation.** You receive a complete local byte buffer representing a toy 'SC' frame; parse only after checking its boundaries.

**By the end:** Read an invented binary header, validate advertised lengths, and reject truncation and extra bytes.

**Input or assumptions:** 2-byte magic SC, 1-byte version, 1-byte type, 2-byte big-endian length, JSON bytes

**Success standard:** running the reference example produces the stated output, the negative cases fail as specified, and your lab notebook includes a threat-boundary diagram and a short explanation of what the result does *not* prove.

## Step 1 — Set up an isolated environment

From the repository root, run:

```bash
python -m venv .venv
python -m unittest discover -s tests -v
```

Activate your virtual environment using your OS instructions from [Start Here](../python/00-START-HERE.md). For the next exercise, copy the snippet into `lab_04.py` **in a temporary working directory** and run `python lab_04.py`. It uses only the Python standard library and local repository modules where noted.

## Step 2 — Predict the result before executing

Write in your notebook: (a) accepted input shape, (b) error conditions, (c) result type, (d) memory/time limit, and (e) whether it performs external I/O. Then compare your predictions with the program.

```python
import json
import struct

def decode(raw):
    if type(raw) is not bytes or len(raw) < 6:
        raise ValueError("short header")
    magic, version, kind, length = struct.unpack("!2sBBH", raw[:6])
    if magic != b"SC" or version != 1 or kind not in (1,2):
        raise ValueError("header fields")
    if length > 1024 or len(raw) != 6 + length:
        raise ValueError("length mismatch or cap")
    data = json.loads(raw[6:].decode("utf-8", "strict"))
    if type(data) is not dict:
        raise ValueError("JSON object needed")
    return data

body = b'{"ok":true}'
frame = struct.pack("!2sBBH", b"SC", 1, 1, len(body)) + body
assert decode(frame) == {"ok":True}
for bad in (frame[:-1], frame + b"x", b"XX" + frame[2:]):
    try:
        decode(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted bad frame")
print("PASS: bad frames rejected")
```

**Expected terminal signal:** `PASS: bad frames rejected`. Additional test-runner output may appear on stderr. A lack of a crash is not evidence of a correct security decision.

## Step 3 — Explain each transformation

1. Unpack !2sBBH means network (big-endian) order and a six-byte header.
2. Reject a declared payload longer than 1024 bytes before decoding it.
3. Reject trailing bytes too; TCP framing belongs to a separate read-exactly transport layer.

**Required deliverable:** draw `input → parse/validate → algorithm → output`; mark the point where untrusted data becomes validated and indicate any assumed trust (e.g., source, time, authentication).

## Step 4 — Deliberately break the input

1. Make magic XX or version 2: reject.
2. Declare a length of 1025: reject before allocation.
3. Modify valid JSON to duplicate keys: this illustrative parser does not reject them; compare with examples.strict_frame.

Do not delete negative test results. In your report, include actual observed exceptions or differences and explain *why* they matter, not just "passed/failed."

## Step 5 — Worked solution and reasoning

The secure parser must validate length against actual bytes. For stricter JSON, use object_pairs_hook to reject duplicate keys and reject non-standard constants.

### Security review

Length-field trust bugs can induce unbounded allocations, incomplete reads and parser disagreements.

**Not proven:** the educational snippet does not establish protection of a deployed service, authenticity of incoming evidence, complete threat coverage, or production readiness. Only its explicitly tested behavior is demonstrated.

## Step 6 — Independent extensions (graded)

1. **Foundations (2 points):** rewrite the example in your own style without changing its input contract.
2. **Robustness (3 points):** add three automated negative tests covering wrong types, limits, or error paths.
3. **Engineering (3 points):** isolate the pure algorithm from I/O and document time and space complexity.
4. **Security reasoning (2 points):** provide one realistic false-positive or failure scenario and an appropriate mitigation.

**Pass mark:** at least 8/10 with *all* required boundary tests passing. Submit code, a one-page Markdown lab report, exact commands, observed results and known limitations.

## Knowledge transfer

Explain the same problem without code to a new SOC analyst: what data is inspected, what evidence is produced, what assumptions could be wrong, and why the action taken is only defensive observation.
