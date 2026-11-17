"""Offline reproducibility tests for portfolio stages 3 and 4."""
import tempfile
from pathlib import Path
import unittest

from projects.builds.incident_timeline import build_timeline
from projects.builds.detection_evaluator import evaluate_cases, read_cases


class TimelineProjectTests(unittest.TestCase):
    def test_two_provider_timeline(self):
        sources = [
            Path("fixtures/project-linux.jsonl"),
            Path("fixtures/project-windows.jsonl"),
        ]
        report = build_timeline(sources)
        self.assertTrue(report["complete"])
        self.assertEqual(len(report["events"]), 4)
        self.assertEqual(
            [x["event_id"] for x in report["events"]],
            ["lin-1","win-1","win-2","lin-2"]
        )
        self.assertEqual(len(report["sources"][0]["sha256"]), 64)

    def test_bad_provider_and_naive_time(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"bad.jsonl"
            path.write_text(
                '{"provider":"unknown","event_id":"1","time":"2026-01-01T10:00:00Z","actor":"x","kind":"failure"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_timeline([path])
            path.write_text(
                '{"provider":"lab-linux","event_id":"1","time":"2026-01-01T10:00:00","actor":"x","kind":"failure"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_timeline([path])

    def test_duplicate_ids_across_files_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"dup.jsonl"
            line='{"provider":"lab-linux","event_id":"one","time":"2026-01-01T10:00:00Z","actor":"x","kind":"failure"}\n'
            p.write_text(line+line,encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                build_timeline([p])

    def test_oversize_and_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.jsonl"
            p.write_bytes(b"x"*9000)
            with self.assertRaises(ValueError):
                build_timeline([p])
            p.write_text(
                '{"provider":"lab-linux","provider":"lab-linux","event_id":"1","time":"2026-01-01T10:00:00Z","actor":"x","kind":"failure"}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                build_timeline([p])


class EvaluationProjectTests(unittest.TestCase):
    def test_reference_fixture(self):
        result=evaluate_cases(read_cases(Path("fixtures/project-labels.jsonl")))
        self.assertEqual(result["counts"], {"tp":2,"fp":1,"fn":1,"tn":2})
        self.assertAlmostEqual(result["precision"], 2/3)
        self.assertAlmostEqual(result["recall"], 2/3)

    def test_labels_and_id_validation(self):
        for bad in (
            {"case_id":"x","actual":True,"predicted":1},
            {"case_id":"x","actual":2,"predicted":1},
            {"case_id":"x","actual":0},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evaluate_cases([bad])

    def test_duplicate_case_id(self):
        row={"case_id":"same","actual":1,"predicted":1}
        with self.assertRaisesRegex(ValueError,"duplicate"):
            evaluate_cases([row,row])

    def test_empty_denominators_are_undefined(self):
        result=evaluate_cases([{"case_id":"1","actual":0,"predicted":0}])
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["recall"])
        self.assertIsNone(result["f1"])

    def test_read_bad_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.jsonl"
            p.write_text('{"case_id":"1"}\nnot-json\n',encoding="utf-8")
            with self.assertRaises(ValueError):
                read_cases(p)


if __name__=="__main__":
    unittest.main()
