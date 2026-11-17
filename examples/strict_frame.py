"""Strict parser/encoder for an invented lab-only binary protocol.

Format: 2-byte magic 'SC', 1-byte version 1, 1-byte message type (1 or 2),
2-byte unsigned big-endian payload length, followed by UTF-8 JSON object.

No network I/O, executable interpretation, or real security protocol implied.
"""
from __future__ import annotations

import json
import struct
from typing import Any

_HEADER = "!2sBBH"
HEADER_SIZE = struct.calcsize(_HEADER)
MAGIC = b"SC"
MAX_PAYLOAD = 1024
_VALID_TYPES = frozenset({1, 2})


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant: {value}")


def decode_frame(frame: bytes) -> dict:
    """Decode a complete frame; reject truncation, trailing bytes and bad JSON."""
    if not isinstance(frame, bytes):
        raise TypeError("frame must be bytes")
    if len(frame) < HEADER_SIZE:
        raise ValueError("truncated frame header")
    magic, version, msg_type, length = struct.unpack(
        _HEADER, frame[:HEADER_SIZE]
    )
    if magic != MAGIC:
        raise ValueError("invalid magic")
    if version != 1:
        raise ValueError("unsupported version")
    if msg_type not in _VALID_TYPES:
        raise ValueError("unsupported message type")
    if length > MAX_PAYLOAD:
        raise ValueError("payload limit exceeded")
    if len(frame) != HEADER_SIZE + length:
        raise ValueError("frame length mismatch")
    try:
        obj = json.loads(
            frame[HEADER_SIZE:].decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON payload") from exc
    if not isinstance(obj, dict):
        raise ValueError("JSON object required")
    return {"version": version, "message_type": msg_type, "payload": obj}


def encode_frame(message_type: int, payload: dict) -> bytes:
    """Encode a toy frame; no authentication or confidentiality is provided."""
    if type(message_type) is not int or message_type not in _VALID_TYPES:
        raise ValueError("invalid message type")
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")
    try:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("payload cannot be encoded as strict JSON") from exc
    if len(body) > MAX_PAYLOAD:
        raise ValueError("payload limit exceeded")
    return struct.pack(_HEADER, MAGIC, 1, message_type, len(body)) + body


if __name__ == "__main__":
    demo = encode_frame(1, {"source": "local-lab", "status": "ok"})
    print("hex:", demo.hex())
    print("decoded:", decode_frame(demo))
