# Deep Dive 11 — Cryptography in Python: hashes, MACs, passwords, encryption and trust

**Level:** intermediate → advanced · **Estimated study:** 12–18 hours.

## Security goals before algorithms

Cryptography is a toolbox for specific guarantees:
- **Confidentiality:** unauthorized parties cannot learn plaintext (under assumptions).
- **Integrity:** unauthorized modification is detected.
- **Authenticity:** the recipient can verify the origin under a key identity/trust model.
- **Non-repudiation:** context-dependent evidence related to a signature; it is not magically provided by any checksum.
- **Forward secrecy:** compromise of long-term keys need not expose earlier sessions, with suitable protocols.

Different primitives address different goals. Choosing a strong algorithm for the **wrong problem** still produces an insecure system.

## 1. Hashing versus encryption

A cryptographic hash such as SHA-256 maps arbitrary-length bytes to a fixed 256-bit digest. It cannot be decrypted. A hash can help detect file changes when compared against a trustworthy expected digest. Hashes are not proof of authorship, and unsalted fast hashes are not suitable for password storage.

```python
import hashlib

payload = b"synthetic incident note"
digest = hashlib.sha256(payload).hexdigest()
print(digest)  # 64 lowercase hexadecimal characters
assert len(digest) == 64
```

A one-byte change usually produces an unrelated digest (avalanche behavior), but demonstrating changed output does not prove security against all attacks. Choose algorithms with appropriate current security properties; do not use MD5 or SHA-1 for modern collision-resistance needs.

## 2. HMAC: a keyed integrity/authentication check

HMAC combines a hash function with a shared secret key. Anyone with that key can produce valid MACs, so it does not give independent evidence of which party in a shared-secret group authored a message.

```python
import hmac, hashlib, secrets

key = secrets.token_bytes(32)
message = b"event_id=e-1001"
tag = hmac.new(key, message, hashlib.sha256).digest()

def verify_tag(k: bytes, msg: bytes, expected: bytes) -> bool:
    supplied = hmac.new(k, msg, hashlib.sha256).digest()
    return hmac.compare_digest(supplied, expected)

assert verify_tag(key, message, tag)
assert not verify_tag(key, message + b"!", tag)
```

Use `compare_digest` for authentication-relevant comparisons. It reduces timing leaks from byte-by-byte early exits, but does not automatically eliminate all side channels in an application.

## 3. Randomness: `secrets` versus `random`

`random` is meant for simulation and sampling. It is deterministic from a seed and should not generate passwords, reset tokens, API keys, encryption keys or session identifiers.

```python
from secrets import token_urlsafe, token_bytes
session_token = token_urlsafe(32)
encryption_key_bytes = token_bytes(32)
```

Estimate entropy in *bits*, not string length alone. Entropy depends on the generator and distribution; formatting does not create randomness.

## 4. Password storage is not encryption

A server should **verify** a user's password, not recover the plaintext. Password hashing must be computationally expensive relative to fast hashes and use an independently random per-password salt. Modern options include Argon2id, scrypt and PBKDF2 in contexts requiring it.

```python
import hashlib, secrets, hmac

salt = secrets.token_bytes(16)
password = b"toy-password-not-for-use"
stored = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=1)
candidate = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=1)
assert hmac.compare_digest(stored, candidate)
```

**Production requirements:** maintain a vetted password-hashing library; benchmark work factor and memory on real hardware; encode algorithm, parameters and salt with the stored verifier; migrate old hashes gradually; enforce account protections and MFA; impose operational caps against resource exhaustion.

### Salt versus pepper
A **salt** is random per password and stored alongside the hash; it defeats many precomputed lookup and identical-hash correlations. A **pepper** is a separately protected server secret used in some architectures; it complicates key management and rotation. Neither replaces a strong password-hashing KDF.

## 5. Authenticated encryption: AEAD

AES-GCM and ChaCha20-Poly1305 are widely used AEAD algorithms when applied through maintained libraries. AEAD encrypts plaintext and authenticates the ciphertext together with *associated data* (AAD) that is not encrypted.

```python
# Requires: python -m pip install cryptography
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
aead = AESGCM(key)
aad = b"tenant=lab;purpose=note"
ciphertext = aead.encrypt(nonce, b"private synthetic note", aad)
assert aead.decrypt(nonce, ciphertext, aad) == b"private synthetic note"
```

### Step-by-step
1. `generate_key` creates random key material for AES-GCM.
2. We choose a 96-bit nonce. **It must never repeat under the same key**. Random nonces only provide a probabilistic uniqueness argument; high-volume systems need a deliberate nonce-management design.
3. `encrypt` returns ciphertext and its authentication tag in the library's format.
4. `decrypt` checks the tag; wrong nonce/key/AAD or modified ciphertext causes failure.
5. You need trustworthy key storage, access controls, rotation and key identification outside the demonstration.

Don't invent a custom encryption scheme to avoid library dependencies.

### Negative test
```python
from cryptography.exceptions import InvalidTag
try:
    aead.decrypt(nonce, ciphertext, b"tenant=other")
except InvalidTag:
    pass
else:
    raise AssertionError("tampered associated data accepted")
```

## 6. Nonce reuse and why it matters

For AES-GCM, repeating a nonce with the same key can compromise confidentiality and integrity. A nonce need not be secret, but uniqueness is essential. Strategies include monotonic counters with durable state, partitioned counters across writers and correct random-nonce engineering with conservative usage limits. The exact design depends on the protocol and deployment, so follow a vetted library/protocol rather than mixing strategies ad hoc.

## 7. Public/private key cryptography and signatures

An asymmetric key pair has public and private components. Digital signatures authenticate a signed message under a public-key trust model. Key exchange helps parties derive shared secrets. TLS certificates bind public keys to identities in a PKI, subject to trust anchors and validation.

Concepts to study:
- RSA vs elliptic curve / Ed25519 signing.
- ECDH/X25519 key agreement.
- Signed certificates and chain validation.
- Padding/mode choices and algorithm agility.
- Revocation and key compromise.
- Key usage separation (do not reuse one key for unrelated roles).

Example signing API (optional `cryptography`):
```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
private = Ed25519PrivateKey.generate()
public = private.public_key()
note = b"synthetic evidence manifest v1"
signature = private.sign(note)
public.verify(signature, note)  # raises on invalid signature
```

Verification proves that the holder of the private key signed these bytes under the algorithm; whether that key belongs to the expected person/system depends on trusted key management.

## 8. Cryptography is not authorization

Even correctly decrypted data must be checked against access policies. Even a valid JWT signature does not mean the token is intended for *your* service: issuer, audience, expiry, purpose and allowed algorithms must be checked.

## 9. Threat model a file encryption utility

**Assets:** plaintext, keys, metadata and backups.
**Threats:** stolen key, nonce reuse, modified ciphertext, partial writes, wrong file permissions, backups left plaintext, encryption used on the wrong tenant, logging secrets.
**Controls:** scoped KMS access, AEAD, unique nonce strategy, metadata authentication, atomic write, access audits, secure rotation and recovery.
**Operational nuance:** filesystem snapshots may retain plaintext; deleting a Python variable does not guarantee erasure from RAM.

## 10. Exercises and answer checks
**A:** Hash two synthetic files with SHA-256. Flip a byte and compare; explain why hashes alone do not prove origin.

**B:** Compute and verify an HMAC. Tamper with one byte and verify rejection. Explain shared-key attribution limitations.

**C:** Use `AESGCM` to encrypt/decrypt a toy record. Wrong key, nonce, AAD and ciphertext must fail with `InvalidTag`.

**D:** Write a 200-word decision for Argon2id vs scrypt/PBKDF2 based on current guidance and your deployment constraints.

**E:** Draw a system for encrypting many files across multiple workers. Explain how you would ensure nonce uniqueness and rotate keys without losing access to old authorized data.

## Common mistakes
| Error | Consequence |
|---|---|
| `random` for tokens | predictable credentials |
| SHA-256 alone for passwords | fast offline guessing |
| Hardcoded encryption keys | easy key disclosure |
| GCM nonce reuse | catastrophic security risks |
| Encryption without integrity | undetected manipulation |
| Disabled TLS verification | active interception |
| "Signed" without trusted key identity | false attribution |
| Custom crypto protocols | hidden design flaws |

**References:** [cryptography.io](https://cryptography.io/en/stable/), [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [secrets](https://docs.python.org/3/library/secrets.html).


## 11. Security protocol design case: an encrypted lab record

You want to store a private synthetic note. AES-GCM provides confidentiality and authentication **only when the key is strong, nonce uniqueness holds and the caller checks authentication failures**. The security of the overall application still depends on access control and key management.

### Explicit message format for the teaching exercise

```text
version  | nonce (12 bytes)  | ciphertext+tag
0x01     | 96-bit GCM nonce | variable length
```

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import os

def encrypt_note(key: bytes, plaintext: bytes, tenant: str) -> bytes:
    if len(key) not in (16, 24, 32) or not isinstance(plaintext, bytes):
        raise ValueError("invalid key length or plaintext")
    if not tenant or len(tenant) > 64:
        raise ValueError("invalid tenant")
    nonce = os.urandom(12)
    aad = ("note:v1:" + tenant).encode("utf-8")
    return b"\x01" + nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

def decrypt_note(key: bytes, envelope: bytes, tenant: str) -> bytes:
    if len(envelope) < 1 + 12 + 16 or envelope[0] != 1:
        raise ValueError("invalid encrypted note envelope")
    nonce = envelope[1:13]
    ciphertext_and_tag = envelope[13:]
    aad = ("note:v1:" + tenant).encode("utf-8")
    return AESGCM(key).decrypt(nonce, ciphertext_and_tag, aad)

key = AESGCM.generate_key(bit_length=256)
sealed = encrypt_note(key, b"synthetic private note", "lab-a")
assert decrypt_note(key, sealed, "lab-a") == b"synthetic private note"
try:
    decrypt_note(key, sealed, "lab-b")
except InvalidTag:
    pass
else:
    raise AssertionError("cross-tenant AAD mismatch was accepted")
```

**Security limitations of this illustration:** it uses randomly generated GCM nonces without tracking uniqueness (acceptable only at well-controlled low volumes within conservative bounds); it has no durable key identifier or rotation, secure secret storage, length cap, authenticated version negotiation or replay protection. In production choose a maintained high-level storage protocol and KMS, and check nonces per key. The function does not confirm a tenant is authorized to call it.

### Step-by-step reasoning

1. Generate a high-entropy key using a verified primitive, not `random.Random`.
2. Build authenticated context (tenant/version) as AAD.
3. Generate an independent nonce for this encryption *under the same key*.
4. Encrypt; library emits ciphertext and authentication tag.
5. Store version, nonce and ciphertext+tag.
6. On read, verify the complete envelope and require exact tenant context.
7. If authentication fails, return an error; never expose unauthenticated plaintext.

## 12. Why signatures, HMAC and hashing cannot substitute for one another

**Scenario:** two services share a secret HMAC key. A valid HMAC proves that someone with the shared key produced the tag; it does not distinguish which of those services created it. A digital signature, by contrast, uses a private key and can be verified using its corresponding public key—but key identity, custody, time and compromise still matter.

| Property | Plain SHA-256 | HMAC-SHA-256 | AEAD | Digital signature |
|---|---|---|---|---|
| Needs a secret key | no | yes | yes | signer holds private key |
| Hides plaintext | no | no | yes | no |
| Detects unauthorized changes | only against trusted reference | yes under key trust | yes under key trust | yes under public-key trust |
| Strong origin attribution | no | shared-key group only | shared-key group only | depends on trusted signer key |
| Supports password storage directly | no | no | no | no |

For password verification use a *password-specific KDF* such as Argon2id where appropriate, or scrypt/PBKDF2 under operational constraints. Do not use fast SHA-256 alone.

## 13. Exercises and failure-case answers

**A:** Flip one byte of an AES-GCM ciphertext. Decryption should fail authentication, not return altered plaintext.

**B:** Reuse the *same* nonce with the *same* key in an illustration only and explain the risk without publishing a real attack. Answer: security guarantees can be catastrophically compromised; never do this in a real application.

**C:** Explain why `nonce` is not itself confidential. It is a uniqueness input, not a secret key; authentication still requires correct key handling.

**D:** Design a key-rotation manifest containing key identifier, creation time, algorithm, ownership and retirement status—but **no key material**.

**E:** Explain why `hashlib.sha256(password)` is unsuitable for production password verification. Answer: computationally cheap for offline guessing; use memory/time-hard KDF with salts and configuration.

**F:** In a multi-tenant store, explain what AAD solves (mix-and-match authenticated context) and what it does not (per-user access authorization).

**External references:** [cryptography.io AEAD](https://cryptography.io/en/stable/hazmat/primitives/aead/), [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
