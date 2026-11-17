"""Execute all 50 independent worked solutions and validate numbering.

A green syntax check alone would miss failing assertions and incorrect
examples. This runner executes the 50 local, standard-library reference
snippets independently under a per-snippet deadline in Python 3.11+.
"""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")
HEADING = re.compile(r"(?m)^## Solution (0[12])\.(\d{2}) — ")


class FoundationsSolutionExecutionTests(unittest.TestCase):
    def test_50_solution_snippets_execute(self):
        for unit, name in (
            ("01", "01-LANGUAGE-FOUNDATIONS-SOLUTIONS.md"),
            ("02", "02-DATA-STRUCTURES-ALGORITHMS-SOLUTIONS.md"),
        ):
            content = (ROOT / "python/solutions" / name).read_text(
                encoding="utf-8"
            )
            parts = re.split(
                rf"(?=^## Solution {unit}\.\d{{2}} — )",
                content, flags=re.M,
            )
            numbered = set()
            for part in parts:
                match = HEADING.search(part)
                if match is None:
                    continue
                chapter, number = match.groups()
                self.assertEqual(chapter, unit)
                n = int(number)
                self.assertNotIn(n, numbered, "duplicate solution")
                numbered.add(n)
                snippets = FENCE.findall(part)
                self.assertEqual(
                    len(snippets), 1,
                    f"expected one complete code block for {unit}.{number}",
                )
                with self.subTest(exercise=f"{unit}.{number}"):
                    result = subprocess.run(
                        [sys.executable, "-c", snippets[0]],
                        cwd=ROOT,
                        text=True, capture_output=True, timeout=10,
                    )
                    self.assertEqual(
                        result.returncode, 0,
                        f"solution {unit}.{number} failed:\n"
                        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                    )
            self.assertEqual(numbered, set(range(1, 26)))


if __name__ == "__main__":
    unittest.main()
