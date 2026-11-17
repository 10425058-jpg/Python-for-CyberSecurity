"""Unit and integration tests for deep course examples (offline only)."""
import json
import struct
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from examples.strict_frame import (
    HEADER_SIZE, MAX_PAYLOAD, decode_frame, encode_frame,
)
from examples.mini_soc_pipeline import (
    parse_event, read_events, detect_bursts, write_findings_atomic,
)


def event_line(when, actor="alice", *, action="login_failure",
               event_id=None, source="lab"):
    obj = {"timestamp": when, "actor": actor, "action": action, "source": source}
    if event_id is not None:
        obj["event_id"] = event_id
    return json.dumps(obj).encode("utf-8") + b"\n"


def as_events(lines):
    return iter(
        parse_event(line, line_number=i, default_source="synthetic")
        for i, line in enumerate(lines, 1)
    )


class StrictFrameTests(unittest.TestCase):
    def test_round_trip_with_unicode(self):
        encoded = encode_frame(2, {"status": "café", "count": 3})
        self.assertEqual(decode_frame(encoded)["payload"]["status"], "café")
        self.assertEqual(len(encoded) - HEADER_SIZE,
                         struct.unpack("!2sBBH", encoded[:HEADER_SIZE])[3])

    def test_short_headers(self):
        for count in range(HEADER_SIZE):
            with self.subTest(count=count), self.assertRaises(ValueError):
                decode_frame(b"SC\x01\x01\x00\x00"[:count])

    def test_bad_magic(self):
        valid = encode_frame(1, {"ok": True})
        with self.assertRaisesRegex(ValueError, "magic"):
            decode_frame(b"XX" + valid[2:])

    def test_bad_version(self):
        valid = bytearray(encode_frame(1, {"ok": True}))
        valid[2] = 99
        with self.assertRaisesRegex(ValueError, "version"):
            decode_frame(bytes(valid))

    def test_bad_type(self):
        with self.assertRaises(ValueError):
            encode_frame(0, {"ok": True})

    def test_length_mismatch(self):
        valid = encode_frame(1, {"ok": True})
        for bad in (valid + b"x", valid[:-1]):
            with self.assertRaisesRegex(ValueError, "length"):
                decode_frame(bad)

    def test_size_cap(self):
        with self.assertRaises(ValueError):
            encode_frame(1, {"x": "A" * (MAX_PAYLOAD + 1)})
        frame = struct.pack("!2sBBH", b"SC", 1, 1, MAX_PAYLOAD + 1)
        with self.assertRaisesRegex(ValueError, "limit"):
            decode_frame(frame)

    def test_duplicate_json_keys(self):
        payload = b'{"a":1,"a":2}'
        frame = struct.pack("!2sBBH", b"SC", 1, 1, len(payload)) + payload
        with self.assertRaisesRegex(ValueError, "duplicate"):
            decode_frame(frame)

    def test_reject_nonfinite(self):
        payload = b'{"a":NaN}'
        frame = struct.pack("!2sBBH", b"SC", 1, 1, len(payload)) + payload
        with self.assertRaises(ValueError):
            decode_frame(frame)

    def test_wrong_types(self):
        with self.assertRaises(TypeError):
            decode_frame("not bytes")
        with self.assertRaises(ValueError):
            encode_frame(True, {})


class MiniSocTests(unittest.TestCase):
    def test_timezones_are_normalized(self):
        record = parse_event(
            event_line("2026-01-01T17:00:00+07:00"),
            line_number=1, default_source="synthetic",
        )
        self.assertEqual(record.timestamp_utc,
                         datetime(2026, 1, 1, 10, tzinfo=timezone.utc))

    def test_wrong_type_and_duplicate_key(self):
        for line in (
            b'{"timestamp":"2026-01-01T00:00:00Z","actor":true,"action":"login_failure"}',
            b'{"timestamp":"2026-01-01T00:00:00Z","actor":"a","actor":"b","action":"login_failure"}',
            b'{"timestamp":"2026-01-01T00:00:00","actor":"a","action":"login_failure"}',
            b'{"timestamp":"2026-01-01T00:00:00Z","actor":"a","action":"wrong"}',
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_event(line, line_number=1, default_source="lab")

    def test_threshold_crossing_and_rearm(self):
        rows = [
            event_line("2026-01-01T10:00:00Z", event_id="1"),
            event_line("2026-01-01T10:01:00Z", event_id="2"),
            event_line("2026-01-01T10:02:00Z", event_id="3"),
            event_line("2026-01-01T10:10:00Z", event_id="4"),
            event_line("2026-01-01T10:11:00Z", event_id="5"),
            event_line("2026-01-01T10:12:00Z", event_id="6"),
        ]
        alerts = list(detect_bursts(as_events(rows), threshold=3))
        self.assertEqual(len(alerts), 2)
        self.assertEqual(alerts[0]["supporting_event_ids"],
                         ["lab:1", "lab:2", "lab:3"])

    def test_dedup_replayed_event(self):
        rows = [
            event_line("2026-01-01T10:00:00Z", event_id="duplicate"),
            event_line("2026-01-01T10:00:00Z", event_id="duplicate"),
            event_line("2026-01-01T10:01:00Z", event_id="other"),
        ]
        alerts = list(detect_bursts(as_events(rows), threshold=3))
        self.assertEqual(alerts, [])

    def test_out_of_order(self):
        rows = [
            event_line("2026-01-01T10:05:00Z"),
            event_line("2026-01-01T10:01:00Z"),
        ]
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            list(detect_bursts(as_events(rows), threshold=2))

    def test_line_size_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.jsonl"
            source.write_bytes(b"A" * 20_000 + b"\n")
            with self.assertRaisesRegex(ValueError, "byte cap"):
                list(read_events(source))

    def test_atomic_report_no_partial_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "events.jsonl"
            out = Path(tmp) / "report.jsonl"
            out.write_text("original\n", encoding="utf-8")
            inp.write_bytes(
                event_line("2026-01-01T10:00:00Z", event_id="1")
                + event_line("2026-01-01T10:00:01Z", event_id="2")
                + event_line("2026-01-01T10:00:02Z", event_id="3")
                + b"invalid-json\n"
            )
            with self.assertRaises(ValueError):
                write_findings_atomic(inp, out, threshold=3)
            self.assertEqual(out.read_text(encoding="utf-8"), "original\n")
            inp.write_bytes(
                event_line("2026-01-01T10:00:00Z", event_id="1")
                + event_line("2026-01-01T10:00:01Z", event_id="2")
                + event_line("2026-01-01T10:00:02Z", event_id="3")
            )
            self.assertEqual(write_findings_atomic(inp, out, threshold=3), 1)
            data = json.loads(out.read_text(encoding="utf-8").strip())
            self.assertEqual(data["rule_id"], "AUTH-BURST-001")


if __name__ == "__main__":
    unittest.main()
