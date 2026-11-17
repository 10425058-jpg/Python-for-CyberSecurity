"""Offline regression tests for third-edition worked code."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from examples.chapter_cases import (
    LoginPolicy, Principal, Report, can_read, detection_metrics,
    import_synthetic_jsonl, parse_login_policy, parse_toy_log,
)


def valid_event(
    event_id="1", *,
    timestamp="2026-01-01T10:00:00Z", source="lab",
    action="login_failure", actor="alex",
) -> bytes:
    return (json.dumps({
        "event_id": event_id, "source": source, "timestamp": timestamp,
        "actor": actor, "action": action,
    }) + "\n").encode("utf-8")


class PolicyTests(unittest.TestCase):
    def test_valid_policy(self):
        p = parse_login_policy(b'{"enabled":true,"max_attempts":5,"user":"alex"}')
        self.assertEqual(p, LoginPolicy(True, 5, "alex"))

    def test_boolean_is_not_numeric_attempt(self):
        with self.assertRaises(ValueError):
            parse_login_policy(
                b'{"enabled":true,"max_attempts":true,"user":"alex"}'
            )

    def test_numeric_enabled_rejected(self):
        with self.assertRaises(ValueError):
            parse_login_policy(b'{"enabled":1,"max_attempts":5,"user":"alex"}')

    def test_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            parse_login_policy(b'{"enabled":true,"max_attempts":5}')

    def test_duplicate_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_login_policy(
                b'{"enabled":false,"enabled":true,"max_attempts":5,"user":"alex"}'
            )

    def test_non_json_constant_rejected(self):
        with self.assertRaises(ValueError):
            parse_login_policy(
                b'{"enabled":true,"max_attempts":NaN,"user":"alex"}'
            )

    def test_byte_cap_rejected(self):
        with self.assertRaises(ValueError):
            parse_login_policy(b" " * 3000)


class LogTests(unittest.TestCase):
    def test_valid_timezone(self):
        result = parse_toy_log(
            "time=2026-01-01T17:00:00+07:00 user=alex action=login_failure"
        )
        self.assertEqual(result["time_utc"], "2026-01-01T10:00:00+00:00")

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            parse_toy_log(
                "time=2026-01-01T10:00:00 user=alex action=login_failure"
            )

    def test_suffix_rejected(self):
        with self.assertRaises(ValueError):
            parse_toy_log(
                "time=2026-01-01T10:00:00Z user=alex action=login_failure injected"
            )

    def test_long_line_rejected(self):
        with self.assertRaises(ValueError):
            parse_toy_log("x" * 1000)


class AuthorizationTests(unittest.TestCase):
    def test_owner_with_permission(self):
        alex = Principal("alex", "A", frozenset({"report:read-own"}))
        report = Report("r-1", "A", "alex", "personal")
        self.assertTrue(can_read(alex, report))

    def test_owner_without_permission(self):
        alex = Principal("alex", "A", frozenset())
        report = Report("r-1", "A", "alex", "personal")
        self.assertFalse(can_read(alex, report))

    def test_cross_tenant_denied(self):
        auditor = Principal("sam", "B", frozenset({"report:read-org"}))
        report = Report("r-1", "A", "alex", "organization")
        self.assertFalse(can_read(auditor, report))

    def test_same_tenant_org_only(self):
        auditor = Principal("sam", "A", frozenset({"report:read-org"}))
        self.assertTrue(can_read(
            auditor, Report("r-1", "A", "alex", "organization")
        ))
        self.assertFalse(can_read(
            auditor, Report("r-2", "A", "alex", "personal")
        ))


class MetricsTests(unittest.TestCase):
    def test_base_rate(self):
        r = detection_metrics(90, 4995, 10, 94905)
        self.assertAlmostEqual(r["precision"], 0.017699115, places=6)
        self.assertEqual(r["recall"], 0.9)
        self.assertEqual(r["false_positive_rate"], 0.05)

    def test_undefined(self):
        r = detection_metrics(0, 0, 0, 10)
        self.assertIsNone(r["precision"])
        self.assertIsNone(r["recall"])
        self.assertIsNone(r["f1"])

    def test_invalid_counts(self):
        for values in [(-1, 0, 0, 10), (True, 0, 0, 10), (1.5, 0, 0, 10)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                detection_metrics(*values)


class TransactionTests(unittest.TestCase):
    def test_success_and_utc_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "events.jsonl"
            p.write_bytes(
                valid_event("1")
                + valid_event("2", timestamp="2026-01-01T17:01:00+07:00")
            )
            conn = sqlite3.connect(":memory:")
            try:
                self.assertEqual(import_synthetic_jsonl(p, conn), 2)
                timestamps = [
                    x[0] for x in conn.execute(
                        "SELECT event_time_utc FROM auth_events ORDER BY event_id"
                    )
                ]
                self.assertEqual(
                    timestamps, [
                        "2026-01-01T10:00:00+00:00",
                        "2026-01-01T10:01:00+00:00"
                    ]
                )
            finally:
                conn.close()

    def test_malformed_record_rolls_back_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.jsonl"
            p.write_bytes(valid_event("1") + b"not-json\n")
            conn = sqlite3.connect(":memory:")
            try:
                with self.assertRaises(ValueError):
                    import_synthetic_jsonl(p, conn)
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM auth_events"
                ).fetchone()[0], 0)
            finally:
                conn.close()

    def test_duplicate_event_rolls_back_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.jsonl"
            p.write_bytes(valid_event("1") + valid_event("1"))
            conn = sqlite3.connect(":memory:")
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    import_synthetic_jsonl(p, conn)
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM auth_events"
                ).fetchone()[0], 0)
            finally:
                conn.close()

    def test_record_cap_rolls_back_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.jsonl"
            p.write_bytes(valid_event("1") + valid_event("2"))
            conn = sqlite3.connect(":memory:")
            try:
                with self.assertRaises(ValueError):
                    import_synthetic_jsonl(p, conn, max_records=1)
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM auth_events"
                ).fetchone()[0], 0)
            finally:
                conn.close()

    def test_line_byte_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "huge.jsonl"
            p.write_bytes(b"x" * 9000 + b"\n")
            conn = sqlite3.connect(":memory:")
            try:
                with self.assertRaisesRegex(ValueError, "bytes"):
                    import_synthetic_jsonl(p, conn)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
