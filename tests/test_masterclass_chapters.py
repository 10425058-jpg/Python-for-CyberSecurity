"""Execute the explicitly tagged masterclass examples in all 22 Deep Dive chapters.

Purpose: distinguish truly executable instructional examples from syntax-only
fragments. Each masterclass is local, synthetic and standard-library only.
The checks exercise positive/negative assertions; they do not prove production
security or complete coverage of arbitrary input.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "course"
PYTHON_FENCES = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")


class MasterclassQualityTests(unittest.TestCase):
    def test_every_deep_dive_chapter_has_an_executable_teaching_case(self):
        chapters = sorted(COURSE.glob("[0-9][0-9]-*.md"))
        self.assertEqual(len(chapters), 22, "expected 22 deep-dive chapter files")
        for chapter in chapters:
            with self.subTest(chapter=chapter.name):
                body = chapter.read_text(encoding="utf-8")
                self.assertIn("## Masterclass", body)
                blocks = [
                    block for block in PYTHON_FENCES.findall(body)
                    if block.lstrip().startswith("# MASTERCLASS_RUNNABLE")
                ]
                self.assertEqual(
                    len(blocks), 1,
                    "each chapter needs one self-contained tested masterclass",
                )
                self.assertIn("assert ", blocks[0], "runnable case must assert behavior")
                # The masterclass is not just a code dump: check explanation and
                # student challenge are present in the section itself.
                section = body.split("## Masterclass", 1)[1].split("\n## ", 1)[0]
                self.assertGreater(
                    len(section.split()), 280,
                    "masterclass must contain substantial explanatory prose",
                )
                self.assertIn("**", section, "explanations/labels required")
                self.assertIn("|", section, "case tables or other structured comparisons needed")
                self.assertTrue(
                    any(keyword in section.lower() for keyword in
                        ("exercise", "challenge", "your turn", "task", "question")),
                    "need a learner exercise or transfer question",
                )

    def test_each_masterclass_example_runs_offline(self):
        chapters = sorted(COURSE.glob("[0-9][0-9]-*.md"))
        self.assertEqual(len(chapters), 22)
        for chapter in chapters:
            body = chapter.read_text(encoding="utf-8")
            blocks = [
                block for block in PYTHON_FENCES.findall(body)
                if block.lstrip().startswith("# MASTERCLASS_RUNNABLE")
            ]
            self.assertEqual(len(blocks), 1, chapter.name)
            with self.subTest(chapter=chapter.name):
                result = subprocess.run(
                    [sys.executable, "-c", blocks[0]],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(
                    result.returncode, 0,
                    f"{chapter.name} failed to run\n"
                    f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                )


if __name__ == "__main__":
    unittest.main()
