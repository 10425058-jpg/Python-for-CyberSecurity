"""Standard-library integration tests for progressive offline portfolio projects."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from projects.builds.integrity_inventory import inventory, compare
from projects.builds.indicator_quality import normalize, ingest


NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)


class IntegrityProjectTests(unittest.TestCase):
    def test_added_removed_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"owned"
            root.mkdir()
            (root/"a.txt").write_text("first",encoding="utf-8")
            old = inventory(root)
            (root/"a.txt").write_text("modified",encoding="utf-8")
            (root/"b.txt").write_text("new",encoding="utf-8")
            new = inventory(root)
            diff = compare(old,new)
            self.assertEqual(diff["changed"],["a.txt"])
            self.assertEqual(diff["added"],["b.txt"])
            self.assertEqual(diff["removed"],[])

    def test_symlink_skipped_where_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"owned"
            root.mkdir()
            (root/"a").write_text("lab")
            alias=root/"alias"
            try:
                alias.symlink_to(root/"a")
            except (OSError,NotImplementedError):
                self.skipTest("symlink creation restricted")
            result=inventory(root)
            self.assertEqual([r["relative_path"] for r in result["files"]],["a"])

    def test_file_and_count_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"data"
            root.mkdir()
            (root/"a").write_text("more")
            (root/"b").write_text("data")
            with self.assertRaisesRegex(ValueError,"file count"):
                inventory(root,max_files=1)
            with self.assertRaisesRegex(ValueError,"file size"):
                inventory(root,max_file_bytes=1)

    def test_compare_rejects_partial(self):
        good={"format":"toy-integrity-v1","complete":True,"root_label":"lab","files":[]}
        bad={**good,"complete":False}
        with self.assertRaises(ValueError):
            compare(good,bad)


class IndicatorsProjectTests(unittest.TestCase):
    def test_normalize_and_expiry(self):
        row={"ip":"2001:0db8::1","source":"lab","observed_at":"2026-01-01T00:00:00Z",
             "ttl_days":5,"confidence":"low"}
        result=normalize(row,as_of=NOW)
        self.assertEqual(result["ip"],"2001:db8::1")
        self.assertTrue(result["expired"])

    def test_wrong_ttl_type(self):
        row={"ip":"192.0.2.1","source":"lab","observed_at":"2026-01-01T00:00:00Z",
             "ttl_days":True,"confidence":"low"}
        with self.assertRaises(ValueError):
            normalize(row,as_of=NOW)

    def test_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"i.jsonl"
            line=b'{"ip":"192.0.2.5","source":"lab","observed_at":"2026-01-01T00:00:00Z","ttl_days":5,"confidence":"low"}\n'
            p.write_bytes(line*2)
            report=ingest(p,as_of=NOW)
            self.assertEqual(report["duplicates"],1)
            self.assertEqual(len(report["indicators"]),1)

    def test_conflicts_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"i.jsonl"
            a=b'{"ip":"192.0.2.5","source":"lab","observed_at":"2026-01-01T00:00:00Z","ttl_days":5,"confidence":"low"}\n'
            b=b'{"ip":"192.0.2.5","source":"lab","observed_at":"2026-01-01T00:00:00Z","ttl_days":7,"confidence":"high"}\n'
            p.write_bytes(a+b)
            with self.assertRaisesRegex(ValueError,"conflicting"):
                ingest(p,as_of=NOW)

    def test_truncated_invalid_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"i.jsonl"
            p.write_bytes(b"x"*9000)
            with self.assertRaises(ValueError):
                ingest(p,as_of=NOW)


if __name__=="__main__":
    unittest.main()
