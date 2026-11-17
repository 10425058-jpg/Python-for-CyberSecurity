# Lab 14 — Offline PCAP metadata and incomplete capture caveats

[Read Chapter 14](../course/14-PCAP-AND-PROTOCOL-FORENSICS.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A student has permission to inspect an offline lab capture and wants protocol counts, not a live scanner.

**Measurable goal:** Understand five-tuples, protocol counts and packet-loss caveats using synthetic flow records; add optional Scapy offline comparison.

**Input contract:** A tiny list of invented IPv4 transport tuples. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_14.py` and copy the next complete snippet into it. Run it with `python lab_14.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
from collections import Counter
import ipaddress

records = [
    ("192.0.2.1","192.0.2.2",443,"TCP"),
    ("192.0.2.2","192.0.2.1",443,"TCP"),
    ("192.0.2.1","192.0.2.3",53,"UDP"),
]
flows = Counter()
for src,dst,port,proto in records:
    src = str(ipaddress.ip_address(src))
    dst = str(ipaddress.ip_address(dst))
    flows[(src,dst,port,proto)] += 1
assert len(flows) == 3
assert sum(flows.values()) == 3
print("PASS: 3 directional toy flows")
```

**Expected result:** `PASS: 3 directional toy flows`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. A 4-tuple here lacks source port, so it is not a complete TCP/UDP five-tuple.
2. Direction matters: forward and reverse observations are distinct.
3. Real packets can be retransmitted, fragmented, encrypted or absent from a partial capture.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Use invalid IP '999.1.1.1': reject with ipaddress.
2. Explain why one HTTP response may occupy many packets.
3. If Scapy is installed, compare offline metadata against Wireshark in a lab-created capture.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

Counts of records or IP tuples do not establish connection count, application transactions or maliciousness. Treat toy records as a precursor to real offline PCAP parsing.

**Security analysis:** Only analyze captures from explicitly authorized sources; packet contents may contain private data.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
