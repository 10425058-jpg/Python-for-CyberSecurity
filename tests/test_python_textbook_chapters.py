"""Execute 12 safe, explicitly tagged Python textbook examples in isolation.

This is separate from the 22 Deep Dive curriculum tests and its lab suite.
Only tagged standard-library, local-first snippets are executed.
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    "00-START-HERE.md", "01-LANGUAGE-FOUNDATIONS.md",
    "02-DATA-STRUCTURES-ALGORITHMS.md", "03-FUNCTIONS-MODULES-TYPING.md",
    "04-FILES-ENCODING-PARSING.md", "05-EXCEPTIONS-TESTING-DEBUGGING.md",
    "06-OOP-AND-ARCHITECTURE.md", "07-ITERATORS-ASYNC-FOUNDATIONS.md",
    "08-CONCURRENCY-AND-ASYNCIO.md", "09-OS-AND-AUTOMATION.md",
    "10-CLI-PACKAGING-DEPENDENCIES.md",
    "11-INTERNALS-PERFORMANCE-ADVANCED.md",
]
FENCE = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")


class PythonTextbookTests(unittest.TestCase):
    def test_all_12_chapters_have_new_in_depth_material(self):
        self.assertEqual(len(FILES), 12)
        for filename in FILES:
            with self.subTest(chapter=filename):
                body = (ROOT / "python" / filename).read_text(encoding="utf-8")
                self.assertIn("## Extended textbook", body)
                self.assertGreater(len(body), 6500)
                self.assertTrue(any(w in body.lower()
                    for w in ("exercise", "practice", "challenge")))
                self.assertTrue(any(w in body.lower()
                    for w in ("invalid", "failure", "security", "limit")))

    def test_all_12_tagged_examples_execute_on_this_interpreter(self):
        for filename in FILES:
            with self.subTest(chapter=filename):
                body = (ROOT / "python" / filename).read_text(encoding="utf-8")
                snippets = [
                    block for block in FENCE.findall(body)
                    if block.lstrip().startswith("# TEXTBOOK_RUNNABLE")
                ]
                self.assertEqual(len(snippets), 1, filename)
                self.assertIn("assert ", snippets[0])
                outcome = subprocess.run(
                    [sys.executable, "-c", snippets[0]], cwd=ROOT,
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(outcome.returncode, 0,
                    f"{filename} failed\\nSTDOUT:\\n{outcome.stdout}"
                    f"\\nSTDERR:\\n{outcome.stderr}")


if __name__ == "__main__":
    unittest.main()
