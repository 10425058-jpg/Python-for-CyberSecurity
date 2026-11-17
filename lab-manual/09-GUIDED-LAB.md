# Lab 09 — TCP framing, DNS assumptions and TLS verification

[Read Chapter 09](../course/09-NETWORKING-DNS-TCP-TLS.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A local service sends messages over a stream. A receiver must not assume one socket read equals one application message.

**Measurable goal:** Build a length-prefixed decoder with a strict payload cap and explain independent TLS and authorization checks.

**Input contract:** big-endian 4-byte length followed by ≤1024 bytes. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_09.py` and copy the next complete snippet into it. Run it with `python lab_09.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from io import BytesIO
from struct import pack, unpack

def parse_stream(stream):
    header = stream.read(4)
    if len(header) != 4:
        raise ValueError("short header")
    count = unpack("!I", header)[0]
    if count > 1024:
        raise ValueError("size cap")
    body = stream.read(count)
    if len(body) != count:
        raise ValueError("short body")
    return body

wire = pack("!I", 5) + b"hello"
assert parse_stream(BytesIO(wire)) == b"hello"
for corrupt in (wire[:3], wire[:-1], pack("!I",1025)):
    try:
        parse_stream(BytesIO(corrupt))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid message accepted")
print("PASS: byte stream framing")
```

**Expected result:** `PASS: byte stream framing`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. The four-byte header defines a byte count, not a character count.
2. The size limit is enforced before allocating or reading the body.
3. Real TCP reads can be short: production code needs read-exactly loops and overall deadlines.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Use 2-byte header: fail before unpacking.
2. Advertise 1025-byte payload: fail before reading payload.
3. Describe why verifying TLS identity does not establish authorization to view an API record.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

A protocol needs framing, byte limits, authentication and caller authorization as separate properties. The in-memory BytesIO example tests framing but not partial network reads.

**Security analysis:** An open TCP port is not a vulnerability finding; incorrect framing can make a parser hang or misinterpret data.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
