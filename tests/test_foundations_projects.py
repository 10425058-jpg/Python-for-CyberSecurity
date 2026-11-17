"""Regression tests for the local-only Python Foundations 01–02 project ladder."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from projects.foundations.auth_summary import (
    Event, parse_event, read_events, summarize, atomic_json_report, MAX_LINE_BYTES,
)
from projects.foundations.window_detector import detect, analyze

ROOT = Path(__file__).resolve().parent.parent


def event_bytes(
    event_id="e1", second=0, *,
    source="toy-idp", actor="alex", action="login_failure",
):
    timestamp = datetime(2026, 1, 1, 10, tzinfo=timezone.utc) + timedelta(
        seconds=second
    )
    return (json.dumps({
        "source": source,
        "event_id": event_id,
        "timestamp": timestamp.isoformat(),
        "actor": actor,
        "action": action,
    }) + "\n").encode("utf-8")


class StrictParsingTests(unittest.TestCase):
    def test_valid_normalized_aware_time(self):
        event = parse_event(
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T17:00:00+07:00","actor":"alex","action":"login_failure"}'
        )
        self.assertEqual(event.timestamp_utc.isoformat(),
                         "2026-01-01T10:00:00+00:00")

    def test_malformed_schema_and_types(self):
        invalid = [
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex"}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":null,"action":"login_failure"}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":true}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"unknown"}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00","actor":"alex","action":"login_failure"}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"login_failure","extra":1}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"login_failure","actor":"bob"}',
            b'{"source":"toy","event_id":"1","timestamp":"2026-01-01T10:00:00Z","actor":"alex","action":"login_failure","x":NaN}',
            b"\xff",
            b"x" * (MAX_LINE_BYTES + 1),
        ]
        for raw in invalid:
            with self.subTest(raw=raw[:65]), self.assertRaises(ValueError):
                parse_event(raw)

    def test_duplicate_replay_and_source_qualification(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "log.jsonl"
            path.write_bytes(event_bytes("same") + event_bytes("same") +
                             event_bytes("same", source="other"))
            events, duplicates, digest = read_events(path)
            self.assertEqual(len(events), 2)
            self.assertEqual(duplicates, 1)
            self.assertEqual(len(digest), 64)

    def test_conflicting_id_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "log.jsonl"
            path.write_bytes(event_bytes("same", actor="alex") +
                             event_bytes("same", actor="sam"))
            with self.assertRaisesRegex(ValueError, "conflicting event ID"):
                read_events(path)

    def test_record_limit_and_bad_line_fail(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.jsonl"
            p.write_bytes(event_bytes("a") + event_bytes("b"))
            with self.assertRaises(ValueError):
                read_events(p, max_records=1)
            p.write_bytes(event_bytes("a") + b"\xff\n")
            with self.assertRaisesRegex(ValueError, "line 2"):
                read_events(p)

    def test_unauthorized_symlink_input_rejected_if_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "original"
            original.write_bytes(event_bytes("a"))
            link = root / "link"
            try:
                link.symlink_to(original)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaises(ValueError):
                read_events(link)


class SummaryProjectTests(unittest.TestCase):
    def test_reference_fixture(self):
        report = summarize(ROOT / "fixtures/foundations-auth.jsonl")
        self.assertTrue(report["complete"])
        self.assertEqual(report["input_unique_events"], 8)
        self.assertEqual(report["login_success_events"], 1)
        self.assertEqual(report["failures_by_actor"], {"alex": 7})

    def test_actor_cap(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "events.jsonl"
            p.write_bytes(
                b"".join(event_bytes(f"e-{i}", actor=f"a{i}") for i in range(501))
            )
            with self.assertRaisesRegex(ValueError, "cardinality"):
                summarize(p)

    def test_atomic_report_preserves_previous_on_invalid_input(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.jsonl"
            report = Path(td) / "report.json"
            path.write_bytes(
                (ROOT / "fixtures/foundations-invalid-third.jsonl").read_bytes()
            )
            report.write_text("PRIOR_COMPLETE_REPORT\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "projects.foundations.auth_summary",
                 "--input", str(path), "--output", str(report)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INCOMPLETE", proc.stderr)
            self.assertEqual(report.read_text(encoding="utf-8"),
                             "PRIOR_COMPLETE_REPORT\n")

    def test_atomic_success_and_same_file_denial(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "log.jsonl"
            dest = Path(td) / "report.json"
            p.write_bytes(event_bytes())
            output = summarize(p)
            atomic_json_report(dest, output)
            self.assertEqual(json.loads(dest.read_text())["input_unique_events"], 1)
            proc = subprocess.run(
                [sys.executable, "-m", "projects.foundations.auth_summary",
                 "--input", str(p), "--output", str(p)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(p.read_bytes(), event_bytes())


class WindowProjectTests(unittest.TestCase):
    def test_two_alerts_and_no_boundary_duplicate(self):
        report = analyze(ROOT / "fixtures/foundations-auth.jsonl")
        self.assertEqual(len(report["alerts"]), 2)
        self.assertEqual(
            [a["supporting_event_ids"] for a in report["alerts"]],
            [
                ["toy-idp:e0", "toy-idp:e30", "toy-idp:e60"],
                ["toy-idp:e200", "toy-idp:e210", "toy-idp:e220"],
            ],
        )

    def test_boundary_exclusive_after_sixty(self):
        moments = [0, 30, 61]
        events = [parse_event(event_bytes(f"t{n}", second=n)) for n in moments]
        self.assertEqual(detect(events), [])

    def test_strict_event_order(self):
        events = [
            parse_event(event_bytes("late", second=60)),
            parse_event(event_bytes("early", second=0)),
        ]
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            detect(events)

    def test_per_actor_cap(self):
        events = [
            parse_event(event_bytes(f"e{i}", second=i)) for i in range(3)
        ]
        with self.assertRaisesRegex(ValueError, "queue cap"):
            detect(events, threshold=2, max_per_actor=2)

    def test_detector_rejects_overspecified_threshold(self):
        with self.assertRaisesRegex(ValueError, "threshold"):
            detect([], threshold=3, max_per_actor=2)

    def test_detector_preserves_old_report_on_corrupt_source(self):
        with tempfile.TemporaryDirectory() as td:
            old = Path(td) / "alerts.json"
            old.write_text("previous complete\n", encoding="utf-8")
            src = ROOT / "fixtures/foundations-invalid-third.jsonl"
            proc = subprocess.run(
                [sys.executable, "-m", "projects.foundations.window_detector",
                 "--input", str(src), "--output", str(old)],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(old.read_text(encoding="utf-8"),
                             "previous complete\n")


if __name__ == "__main__":
    unittest.main()
