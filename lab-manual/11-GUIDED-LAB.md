# Lab 11 — Hashes, HMAC and key-management boundaries

[Read Chapter 11](../course/11-CRYPTOGRAPHY-DEEP-DIVE.md) · **Expected time:** 2–5 hours · Python 3.11+ · **Scope:** synthetic data and offline work; no third-party assets.

## Problem statement

A local service wants to confirm a synthetic event has not been modified and the sender knows a shared key.

**Measurable goal:** Compare a plain digest with an HMAC and negative tampering tests; explain why neither encrypts the message.

**Input contract:** b'event=lab-001' and a locally generated 32-byte key. Write down the difference between trustworthy metadata, attacker-controlled input, and assumptions before starting.

## Prepare your project

From the root of the repository:

```bash
python -m unittest discover -s tests -v
```

Create a temporary file named `lab_11.py` and copy the next complete snippet into it. Run it with `python lab_11.py`. Do not put credentials, production log files, or real personal data in your lab repository.

## Guided implementation

```python
import hashlib
import hmac
import secrets

payload = b"event=lab-001"
key = secrets.token_bytes(32)
digest = hashlib.sha256(payload).hexdigest()
tag = hmac.new(key, payload, hashlib.sha256).digest()
assert len(digest) == 64
assert hmac.compare_digest(tag, hmac.new(key, payload, hashlib.sha256).digest())
assert not hmac.compare_digest(tag, hmac.new(key, payload + b"!", hashlib.sha256).digest())
print("PASS: tampered message rejected")
```

**Expected result:** `PASS: tampered message rejected`

If you get a different result, report the actual exception and compare your Python version and input data. Do not replace validation with silent exception handlers to make the lab pass.

## Step-by-step explanation

1. SHA-256 supplies a digest, not confidentiality or sender identity.
2. HMAC authenticates under a shared secret, using compare_digest for check.
3. The shared key requires protection, rotation and scope; HMAC cannot distinguish two parties holding the same key.

At each step, identify the Python type, invariant and source of trust. Explicitly distinguish observations produced by the program from security conclusions that would require independent corroboration.

## Negative tests: try to falsify your own solution

1. Tamper with one byte: tag mismatch.
2. Compute SHA-256 for a changed payload: different digest but no proof of origin.
3. Plan a separate optional AEAD experiment using a vetted cryptography package; never reuse a GCM nonce.

A correct negative test asserts not just *that* something fails but also *why* the error is the intended response. Include expected and observed outputs in your report.

## Guided answer / important limitation

Digest comparison verifies integrity only against a trusted reference; HMAC adds shared-key integrity/authentication, still not encryption. Use password-specific KDFs for passwords.

**Security analysis:** Hardcoded keys, unsuitable random generators and nonce reuse can undermine otherwise strong algorithms.

A passing demonstration does **not** prove all malicious inputs are handled, that a real environment is safe, or that the tool is suitable for production. State source completeness and affected assumptions.

## Independent assignment (10 points)

1. **2 pts — Reproduce:** run the snippet, record Python version, exact command and observed output.
2. **3 pts — Test:** add a normal, boundary and malformed-input test with assertions.
3. **2 pts — Explain:** write a byte diagram, data-flow diagram or policy table relevant to this lab.
4. **2 pts — Threat model:** identify a plausible false positive, false negative or resource exhaustion.
5. **1 pt — Reflect:** list what additional proof a professional analyst would need.

**Completion gate:** ≥8/10 and every required negative test behaves correctly. Deliver your source, tests and one-page `lab-report.md` with a scope statement and evidence references.
