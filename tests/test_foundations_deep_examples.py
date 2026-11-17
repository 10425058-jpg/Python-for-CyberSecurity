"""Execute all newly added Deep Core 01/02 examples, not just syntax-check them."""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
FENCES = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")
CHAPTERS = (
    ("01-LANGUAGE-FOUNDATIONS.md", 9),
    ("02-DATA-STRUCTURES-ALGORITHMS.md", 10),
)


class DeepCoreExecutableExamples(unittest.TestCase):
    def test_every_tagged_code_block_executes(self):
        for name, expected in CHAPTERS:
            doc = ROOT / "python" / name
            contents = doc.read_text(encoding="utf-8")
            snippets = [
                snippet for snippet in FENCES.findall(contents)
                if snippet.lstrip().startswith("# DEEP_CORE_RUNNABLE")
            ]
            self.assertEqual(len(snippets), expected, name)
            for index, snippet in enumerate(snippets, 1):
                with self.subTest(chapter=name, sample=index):
                    self.assertIn("assert ", snippet)
                    result = subprocess.run(
                        [sys.executable, "-c", snippet],
                        cwd=ROOT, capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(
                        result.returncode, 0,
                        f"{name} sample {index}\n"
                        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                    )

    def test_deep_core_exercises_and_project_links_exist(self):
        docs = [
            ROOT / "python/exercises/01-LANGUAGE-FOUNDATIONS-EXERCISES.md",
            ROOT / "python/exercises/02-DATA-STRUCTURES-ALGORITHMS-EXERCISES.md",
            ROOT / "python/solutions/01-LANGUAGE-FOUNDATIONS-SOLUTIONS.md",
            ROOT / "python/solutions/02-DATA-STRUCTURES-ALGORITHMS-SOLUTIONS.md",
            ROOT / "projects/foundations/auth_summary.py",
            ROOT / "projects/foundations/window_detector.py",
        ]
        for doc in docs:
            with self.subTest(path=str(doc)):
                self.assertTrue(doc.is_file())
                self.assertGreater(doc.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
