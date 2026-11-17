# Deep Dive 04 — Bytes, Unicode, binary protocols and untrusted parsers

> **Hands-on:** [Chapter 04 Guided Lab](../lab-manual/04-GUIDED-LAB.md) · [100 numbered worked answers](../solutions/by-exercise/README.md). Complete the lab's negative tests before moving on.

**Level:** intermediate · **Estimated study:** 8–12 hours · **Prerequisites:** types, functions, file I/O.

## Objective
Most cybersecurity data is not a friendly text string. Packets, archives, compiled files, crypto messages and even modern logs can contain arbitrary bytes. You will learn to parse byte sequences without confusing encodings, lengths or endianness.

## Masterclass — complete message parsing versus transport reads

A binary parser receives a **complete** message buffer; a transport receiver must determine where that complete buffer ends. These are separate correctness claims. For a made-up lab frame, use two-byte magic `SC`, one-byte version, one-byte kind, two-byte unsigned big-endian payload size and a bounded UTF-8 JSON object. The header itself is six bytes.

A decoder that merely checks `len(data) >= 6` is unsafe if it then trusts the declared length. Conversely, a TCP receiver that reads `recv(1024)` once may receive only half a frame or several frames joined together. Design and test both layers separately.

| Header `53 43 01 01 00 07` | Interpretation |
|---|---|
| `53 43` | ASCII "SC" |
| `01` | protocol version 1 |
| `01` | message kind 1 |
| `00 07` | exactly seven payload bytes |

**Runnable, pure parser with duplicate-field rejection:**

```python
# MASTERCLASS_RUNNABLE
import json
import struct

HEADER = struct.Struct("!2sBBH")
MAX_PAYLOAD = 256

def unique_keys(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON field")
        result[name] = value
    return result

def parse_frame(data: bytes) -> dict:
    if type(data) is not bytes or len(data) < HEADER.size:
        raise ValueError("missing complete header")
    magic, version, kind, length = HEADER.unpack_from(data)
    if magic != b"SC" or version != 1 or kind != 1:
        raise ValueError("unsupported frame")
    if length > MAX_PAYLOAD or len(data) != HEADER.size + length:
        raise ValueError("invalid declared length")
    try:
        value = json.loads(
            data[HEADER.size:].decode("utf-8", "strict"),
            object_pairs_hook=unique_keys,
            parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid payload encoding") from exc
    if type(value) is not dict:
        raise ValueError("expected an object")
    return value

payload = b'{"ok":1}'
good = HEADER.pack(b"SC", 1, 1, len(payload)) + payload
assert parse_frame(good) == {"ok": 1}

for malformed in (good[:-1], good + b"x", b"XX" + good[2:]):
    try:
        parse_frame(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid frame accepted")
duplicate = b'{"ok":1,"ok":2}'
bad = HEADER.pack(b"SC", 1, 1, len(duplicate)) + duplicate
try:
    parse_frame(bad)
except ValueError:
    pass
else:
    raise AssertionError("ambiguous JSON accepted")
```

**Read the invariants in order.** (1) Check raw type/header length. (2) Verify magic, supported version and kind. (3) Check declared length **and** actual buffer equality. (4) Decode UTF-8 strictly. (5) Reject duplicate JSON keys; some default JSON parsers accept the last value. (6) Require a top-level object. Passing these checks does **not** authenticate who sent the message.

**Exercise:** a sender writes a header then sends payload in three pieces. Sketch `readexactly(6)` followed by `readexactly(length)`, with one overall timeout, peer limits and cancellation. Why does a separate `len(data)` check still belong inside the pure decoder? Because transport and parser are independent trust boundaries, and separate callers may hand in malformed complete buffers.


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


## 10. Detailed protocol audit: parsing header length is not sufficient

The six-byte toy header from this chapter is intentionally simple: magic (2), version (1), type (1), length (2). Real protocol parsing also needs a transport layer, strict resource limits, integrity/authentication, and uncertainty handling.

**Threat model:** a peer may send arbitrary bytes, declare a huge length, disconnect mid-frame, stall for minutes, send concatenated frames, or trick a parser with duplicate JSON keys. Our parser must not execute contents, must not read unbounded amounts and must report exactly which invariant failed.

### Binary structure and example trace

```text
Byte offsets:
00  01  02  03  04  05 | 06...N
 S   C   01  02   00  0b | (11 payload bytes)
 |magic|version|kind|length| payload |

Header: 53 43 01 02 00 0b
Magic  = b"SC"
Version = 1
Kind    = 2
Length  = 11 (big-endian)
```

Consider why `!` in `struct.unpack("!2sBBH", header)` matters: for bytes `01 00`, a two-byte big-endian length is 256, while little-endian interprets 1. An attacker exploiting an endianness disagreement might bypass one component's size checks.

### Full client-side decoder with exact framing

```python
import asyncio
import struct
import json

MAX_BYTES = 1024

async def read_lab_frame(reader: asyncio.StreamReader) -> dict:
    header = await asyncio.wait_for(reader.readexactly(6), timeout=2)
    magic, version, kind, count = struct.unpack("!2sBBH", header)
    if magic != b"SC" or version != 1 or kind not in (1, 2):
        raise ValueError("invalid toy protocol header")
    if count > MAX_BYTES:
        raise ValueError("declared payload exceeds limit")
    body = await asyncio.wait_for(reader.readexactly(count), timeout=2)
    value = json.loads(body.decode("utf-8", errors="strict"))
    if type(value) is not dict:
        raise ValueError("payload must be an object")
    return {"kind": kind, "data": value}
```

This is a learning-only read helper, **not** a complete secure protocol. The two separate timeouts are **not a total deadline** (a peer may exploit multiple stages); a production service needs a *single overall timeout*, connection limits, strict JSON handling, authentication and error integration.

### Test the transport separately from the parser

```python
from examples.strict_frame import encode_frame, decode_frame

valid = encode_frame(2, {"event":"training"})
assert decode_frame(valid)["message_type"] == 2

for bad in [valid[:-1], valid + b"!", b"XY" + valid[2:]]:
    try:
        decode_frame(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("bad frame was accepted")
```

**Why tests belong at two layers:** `decode_frame` verifies an already complete byte string. `read_lab_frame` verifies framed I/O over an asynchronous byte stream. Passing one set of tests does not prove the other is correct. Particularly test partial transport reads, cancellation and EOF.

## 11. Attacker-controlled JSON ambiguities

JSON keys can be duplicated in a raw document. Python's default `json.loads` accepts the duplicate and generally keeps the last value; two downstream components using different parsers may disagree about an authorization field. In strict security contexts, reject duplicate keys with `object_pairs_hook`. The [reference implementation](../examples/strict_frame.py) does that and rejects nonstandard NaN/Infinity constants.

A byte-size cap protects against one class of exhaustion, but not arbitrary computation complexity or deeply nested data. Consider JSON nesting, supported max object entries, timeouts, and upstream body limits.

## 12. Exercises and answers

1. **Manual decode:** `53 43 01 01 00 05`. The header declares **5** payload bytes. If only 4 exist, reject. Why? Truncated frame violates the wire contract.
2. **Unicode:** JSON `{"x":"é"}` is longer in UTF-8 than its visible character count. Compute the exact bytes in Python rather than assuming ASCII.
3. **TCP:** if the sender writes two frames with two `sendall` calls, can the receiver get both in one `recv`? Yes; TCP does not preserve write boundaries.
4. **Security:** an unauthenticated peer sends a syntactically valid frame. Is it authorized? No; parsing data and authorizing a sender are separate tasks.
5. **Stress:** fuzz `decode_frame` locally with truncated prefixes of valid frames; every prefix shorter than full frame must reject. Run with CPU/time limits.

**Design review:** where would you insert a message authentication check, and which exact bytes would it cover? Consider header fields, message type, replay prevention and key identity. Use a vetted protocol instead of inventing production cryptography.
