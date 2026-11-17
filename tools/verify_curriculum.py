"""Validate fenced Python snippets and local Markdown navigation.

Syntax-only: textbook snippets are not executed here.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
COURSE = ROOT / "course"

PYTHON_FENCES = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")
LOCAL_LINKS = re.compile(r"\]\(([^)\s]+)(?:\s+[^)]*)?\)")


def main() -> int:
    failures = []
    chapters = sorted(COURSE.glob("[0-9][0-9]-*.md"))
    if len(chapters) != 22:
        failures.append(f"expected 22 chapters, found {len(chapters)}")

    python_blocks = 0
    for path in chapters:
        body = path.read_text(encoding="utf-8")
        blocks = PYTHON_FENCES.findall(body)
        if not blocks:
            failures.append(f"{path.relative_to(ROOT)}: no Python examples")
        for number, source in enumerate(blocks, 1):
            python_blocks += 1
            try:
                ast.parse(source, filename=f"{path.name} snippet {number}")
            except SyntaxError as exc:
                failures.append(
                    f"{path.relative_to(ROOT)} snippet {number}: "
                    f"{exc.msg} line {exc.lineno}"
                )

    for path in [ROOT / "README.md", COURSE / "README.md",
                 ROOT / "reference" / "CHAPTER-INDEX.md", *chapters]:
        body = path.read_text(encoding="utf-8")
        without_fences = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", body)
        for target in LOCAL_LINKS.findall(without_fences):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            location = target.split("#", 1)[0].split("?", 1)[0]
            if not location:
                continue
            candidate = (path.parent / location).resolve()
            if not candidate.is_relative_to(ROOT) or not candidate.exists():
                failures.append(f"{path.relative_to(ROOT)} missing {target}")

    if failures:
        for item in failures:
            print("ERROR:", item, file=sys.stderr)
        return 1
    print(f"Validated {len(chapters)} chapters, {python_blocks} Python snippets "
          "and local Markdown links (syntax/navigation only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
