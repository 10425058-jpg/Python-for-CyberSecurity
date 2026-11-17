# Workshop 03 — Authenticated encryption, hashing and HMAC (synthetic data)

**Duration:** 2–4 hours · **Requires:** maintained Python 3 and optional vetted `cryptography` package.

## Security boundaries
This lab uses local synthetic notes and generated disposable keys. Never paste real private keys, credentials, production logs or encrypted customer data into a public repository. Do not design custom cryptographic protocols for production.

## 1. Distinguish four primitives

| Primitive | Secret? | Main goal | Example |
|---|---|---|---|
| SHA-256 hash | no key | digest/integrity comparison | compare file copies |
| HMAC-SHA-256 | shared secret | integrity and symmetric authentication | protect messages |
| AEAD | shared key + nonce | confidentiality and integrity | encrypt records |
| Digital signature | private/public key | verify signed message under trusted key | signed manifests |

A hash is not encryption. HMAC is not a digital signature. Encryption without correct key management is not a complete secure system.

## 2. SHA-256

```python
import hashlib
data = b"lab record"
digest = hashlib.sha256(data).hexdigest()
assert len(digest) == 64
assert hashlib.sha256(data + b"!").hexdigest() != digest
```

**Expected:** change one byte → a different digest. Does that establish origin? **No**. A trusted reference and evidence handling are necessary.

## 3. HMAC and tampering

```python
import hmac, hashlib, secrets
key = secrets.token_bytes(32)
message = b"event=e-100;severity=review"
tag = hmac.new(key, message, hashlib.sha256).digest()
assert hmac.compare_digest(
    hmac.new(key, message, hashlib.sha256).digest(), tag
)
assert not hmac.compare_digest(
    hmac.new(key, message + b"!", hashlib.sha256).digest(), tag
)
```

**Expected:** original message verifies, modified message fails. Anyone who knows the shared key can produce a valid tag, which affects attribution.

## 4. AEAD with AES-GCM

Set up a virtual environment and install from a trusted package source:
```bash
python -m venv .venv
# activate using your shell
python -m pip install cryptography
```

### Encryption and negative tests
```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
aead = AESGCM(key)
aad = b"purpose=synthetic-note;version=1"
plaintext = b"synthetic evidence only"
ciphertext = aead.encrypt(nonce, plaintext, aad)
assert aead.decrypt(nonce, ciphertext, aad) == plaintext

try:
    aead.decrypt(nonce, ciphertext, b"purpose=different")
except InvalidTag:
    print("tampered AAD correctly rejected")
else:
    raise AssertionError("unexpected success")
```

### Explain each ingredient
- **Key:** must remain secret; separate from code and outputs.
- **Nonce:** must be unique for every encryption under a key; 96-bit random nonce in the toy demo, but production high-volume systems require a designed uniqueness strategy.
- **AAD:** contextual bytes authenticated but *not* encrypted.
- **Ciphertext + tag:** encrypted output and verification material in library's format.
- **Decrypt failure:** must not expose unauthenticated plaintext.

## 5. Password hashing is different

Use a password-specific KDF, not SHA-256 alone:
```python
import hashlib, secrets, hmac
salt = secrets.token_bytes(16)
stored = hashlib.scrypt(b"example-only", salt=salt, n=2**14, r=8, p=1)
candidate = hashlib.scrypt(b"example-only", salt=salt, n=2**14, r=8, p=1)
assert hmac.compare_digest(stored, candidate)
```

For production, prefer current vetted password storage guidance and appropriate work factors, versioning and MFA. Do not publish real salts + password hashes from user accounts.

## 6. Exercises
**A:** Explain why a digest cannot provide confidentiality. Answer: the digest does not protect the original plaintext, and anyone can hash guesses.

**B:** Modify ciphertext/AAD/nonce individually; show authentication failure. Answer: AEAD rejects changes when verification fails.

**C:** Explain nonce reuse risk in AES-GCM. Answer: reuse under one key can compromise security guarantees.

**D:** Write a key-rotation plan for a small encrypted file vault: how would ciphertext indicate which authorized key is needed, how would you migrate and revoke, what happens to backups?

**E:** Explain why "decrypted successfully" does not imply "caller is authorized." Answer: cryptographic integrity/authenticity and access policy are independent.

## Deliverable
One-page table distinguishing primitives; runnable synthetic encrypt/decrypt demo; negative tests; key lifecycle diagram; documented limits.
