# Deep Dive 04 — Bytes, Unicode, binary protocols and untrusted parsers

**Level:** intermediate · **Estimated study:** 8–12 hours · **Prerequisites:** types, functions, file I/O.

## Objective
Most cybersecurity data is not a friendly text string. Packets, archives, compiled files, crypto messages and even modern logs can contain arbitrary bytes. You will learn to parse byte sequences without confusing encodings, lengths or endianness.

## 1. Bytes are not characters

`b"A"` stores 0x41 (decimal 65). A Python `str` stores Unicode code points and does not have an inherent wire encoding. UTF-8 represents many characters with multiple bytes.

```python
text = "café"
encoded = text.encode("utf-8")
assert len(text) == 4
assert len(encoded) == 5
assert encoded[-2:] == b"\xc3\xa9"
```

Protocol fields count *bytes* unless the specification explicitly says otherwise. A maximum 64-character username is not the same as a maximum 64-byte username.

### Error handling
`bytes.decode("utf-8", "strict")` raises on malformed sequences. `"replace"` inserts replacement characters and destroys exact byte fidelity. `"ignore"` drops data silently. For evidence preservation, store original bytes separately and document any derived human-readable text.

## 2. Hex, Base64 and endianness

Hex and Base64 are **encodings**, not secrecy mechanisms. Big-endian is most significant byte first; network byte order is conventionally big-endian. Little-endian reverses byte significance for multi-byte integers.

```python
import base64
assert bytes.fromhex("01ff") == b"\x01\xff"
assert base64.b64decode(base64.b64encode(b"hello")) == b"hello"
assert int.from_bytes(b"\x01\x00", "big") == 256
assert int.from_bytes(b"\x01\x00", "little") == 1
```

## 3. Parsing network-style binary headers

Assume an invented **toy protocol**:
- 2 bytes: magic `b"SC"`.
- 1 byte: version (must equal 1).
- 1 byte: message type (1 = status, 2 = alert).
- 2 bytes: unsigned big-endian payload length, capped at 1024.
- N bytes: UTF-8 JSON payload.

The wire format is not a real security protocol; no authentication is provided. It is designed purely to learn safe parsing.

```text
Offset  Size  Field
0       2     magic
2       1     version
3       1     message_type
4       2     payload_length
6       N     JSON bytes
```

### Correct parser (complete example)

```python
import json
import struct

HEADER_SIZE = 6

def parse_toy_frame(raw: bytes) -> dict:
    if not isinstance(raw, bytes):
        raise TypeError("frame must be bytes")
    if len(raw) < HEADER_SIZE:
        raise ValueError("truncated header")
    magic, version, msg_type, size = struct.unpack("!2sBBH", raw[:HEADER_SIZE])
    if magic != b"SC":
        raise ValueError("bad magic")
    if version != 1 or msg_type not in (1, 2):
        raise ValueError("unsupported version or type")
    if size > 1024:
        raise ValueError("payload exceeds cap")
    if len(raw) != HEADER_SIZE + size:
        raise ValueError("length mismatch or trailing bytes")
    try:
        payload = json.loads(raw[HEADER_SIZE:].decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")
    return {"type": msg_type, "payload": payload}

payload = b'{"ok":true}'
frame = struct.pack("!2sBBH", b"SC", 1, 1, len(payload)) + payload
assert parse_toy_frame(frame)["payload"] == {"ok": True}
```

### Walkthrough, one condition at a time
1. Check that the function received bytes.
2. Reject less than six bytes *before* unpacking to avoid a struct error.
3. Parse a fixed-size header with network endianness: `!`.
4. Reject unknown magic/version/type: never "guess" a format.
5. Enforce an upper bound on the advertised payload length **before allocating**.
6. Confirm the actual input length matches the advertised size exactly.
7. Decode with strict UTF-8; then parse JSON as data, never execute it.
8. Require the intended JSON top-level shape.

### Why length checks are security checks
A malicious or corrupt frame might claim to contain 65,535 bytes when only 3 are present. A naive parser could wait forever for additional bytes or allocate huge buffers based on the claim. A robust network implementation checks a header size cap and uses a read-exactly method with an overall deadline.

## 4. Message framing over TCP

TCP is a byte stream, not a series of messages. If the sender calls `sendall` once, the receiver might get half the bytes with one `recv`, or several messages together. The parser above handles *complete frames*; a TCP receiver must first gather exactly the six header bytes, inspect size, and then gather exactly the specified payload length.

For asyncio code, `reader.readexactly(6)` raises when the connection ends too soon. Ensure a timeout wraps the entire operation; avoid waiting forever for a missing payload.

## 5. Memory views and copying

`memoryview` exposes a window into a bytes-like object without necessarily copying the payload. This is useful for large captures and performant parsers, but the underlying object's lifetime and mutability matter.

```python
raw = b"abcdef"
view = memoryview(raw)
assert bytes(view[2:4]) == b"cd"
```

Never assume a slice refers to a safe, immutable snapshot if the underlying storage is mutable.

## 6. Integrity versus authenticity

`hashlib.sha256(data).digest()` can detect accidental changes when compared against a trusted previously stored digest. It does not prove the sender. HMAC requires a shared secret, signatures require trustworthy key identity, and authenticated encryption protects both secrecy and message integrity under the intended protocol design.

## 7. Fuzz your parser locally

```python
bad_inputs = [
    b"", b"S", b"SC", b"XX\x01\x01\x00\x00",
    b"SC\x09\x01\x00\x00", b"SC\x01\x01\xff\xff",
    b"SC\x01\x01\x00\x01x",
]
for sample in bad_inputs:
    try:
        parse_toy_frame(sample)
    except ValueError:
        continue
    raise AssertionError(f"unexpected accepted input: {sample!r}")
```

A more mature test suite should vary lengths, unexpected types, Unicode and extra bytes. Fuzz only a local pure function under your control, with resource budgets.

## 8. Common parser bugs

| Bug | Consequence |
|---|---|
| Wrong byte order | misinterpreted lengths/ports |
| Trusting claimed length | excessive allocation or stalled I/O |
| Decoding bytes as text too early | offsets and evidence corrupted |
| Suppressing parse errors | lost or misclassified records |
| Using `eval` / `pickle.loads` on data | arbitrary code execution risk |
| Reading entire input without a cap | memory exhaustion |
| Parsing a network stream with one `recv` | truncated frames or message smearing |
| Unverified checksums as signatures | false attribution |

## 9. Lab and assessments

**Lab:** save the toy frame above as `frame.bin`, hex-dump it, modify the version byte and verify rejection. Truncate one payload byte and confirm the length mismatch. Append a byte and confirm it also rejects trailing data.

**Exercise A:** extend the format with a four-byte big-endian sequence number; update header size, tests and diagrams. **Answer check:** `struct.unpack("!2sBBHI", ...)` now needs 10 bytes.

**Exercise B:** prove that `len("é")` differs from `len("é".encode("utf-8"))` and discuss an ASCII-only protocol field.

**Exercise C:** design a "read_exactly" loop that will not exceed a total deadline, even when the sender slowly drip-feeds bytes. Explain why a per-read timeout alone can be insufficient.

**Exercise D:** write unit tests for every rejection path in `parse_toy_frame` and show that all errors are predictable, not crashes.

**References:** [struct](https://docs.python.org/3/library/struct.html), [socket](https://docs.python.org/3/library/socket.html), [Unicode HOWTO](https://docs.python.org/3/howto/unicode.html).
