"""Execute the standalone local standard-library labs and worked solutions.

Runs each snippet in a separate subprocess from repo root with a deadline.
Do not add arbitrary network-dependent or credential-reading snippets here.
Optional package-only exercises 055-056 are syntax checked but not executed.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
BLOCKS = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")
HEADERS = re.compile(r"(?m)^## (?:Exercise )?(\d{3}) — ")


def snippet(doc: Path) -> str:
    blocks = BLOCKS.findall(doc.read_text(encoding="utf-8"))
    if len(blocks) != 1:
        raise AssertionError(f"{doc}: expected exactly one complete lab snippet")
    return blocks[0]


class GuidedLabExecutionTests(unittest.TestCase):
    def test_all_22_guided_labs(self):
        docs = sorted((ROOT / "lab-manual").glob("[0-9][0-9]-GUIDED-LAB.md"))
        self.assertEqual(len(docs), 22)
        for doc in docs:
            with self.subTest(lab=doc.name):
                self._run(snippet(doc))

    def _run(self, source: str):
        result = subprocess.run(
            [sys.executable, "-c", source], cwd=ROOT, capture_output=True,
            text=True, timeout=12,
        )
        self.assertEqual(result.returncode, 0,
                         f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")


class WorkedSolutionsExecutionTests(unittest.TestCase):
    def test_98_standard_library_solutions(self):
        docs = sorted((ROOT / "solutions/by-exercise").glob("[0-9][0-9][0-9]-[0-9][0-9][0-9].md"))
        self.assertEqual(len(docs), 10)
        seen = set()
        for doc in docs:
            text = doc.read_text(encoding="utf-8")
            parts = re.split(r"(?=^## (?:Exercise )?\d{3} — )", text, flags=re.M)
            for part in parts:
                match = HEADERS.search(part)
                if match is None:
                    continue
                num = int(match.group(1))
                self.assertNotIn(num, seen)
                seen.add(num)
                blocks = BLOCKS.findall(part)
                self.assertEqual(len(blocks), 1, f"{doc}: exercise {num}")
                if num in (55, 56):  # optional cryptography dependency
                    continue
                with self.subTest(exercise=num):
                    result = subprocess.run(
                        [sys.executable, "-c", blocks[0]], cwd=ROOT,
                        capture_output=True, text=True, timeout=12,
                    )
                    self.assertEqual(
                        result.returncode, 0,
                        f"exercise {num}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                    )
        self.assertEqual(seen, set(range(1, 101)))


if __name__ == "__main__":
    unittest.main()
