"""Check education assets: 22 chapters, 22 labs, 100 answers, Python syntax and links.

This is a syntax/navigation audit. It does NOT itself execute every snippet;
tests/test_curriculum_examples.py executes the safe standard-library examples.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"(?ms)^```python[^\n]*\n(.*?)^```\s*$")
LINK = re.compile(r"\]\(([^)\s]+)(?:\s+[^)]*)?\)")
ANY_FENCE = re.compile(r"(?ms)^```[^\n]*\n.*?^```\s*$")
SOLUTION_HEADER = re.compile(r"(?m)^## (?:Exercise )?(\d{3}) — ")


def audit() -> tuple[list[str], dict[str, int]]:
    errors = []
    chapters = sorted((ROOT / "course").glob("[0-9][0-9]-*.md"))
    labs = sorted((ROOT / "lab-manual").glob("[0-9][0-9]-GUIDED-LAB.md"))
    answers = sorted((ROOT / "solutions" / "by-exercise").glob("[0-9][0-9][0-9]-[0-9][0-9][0-9].md"))
    if len(chapters) != 22:
        errors.append(f"expected 22 chapters, found {len(chapters)}")
    if len(labs) != 22:
        errors.append(f"expected 22 labs, found {len(labs)}")
    if len(answers) != 10:
        errors.append(f"expected 10 answer volumes, found {len(answers)}")

    all_files = chapters + labs + answers
    snippets = 0
    answered = []
    for doc in all_files:
        text = doc.read_text(encoding="utf-8")
        blocks = FENCE.findall(text)
        if not blocks:
            errors.append(f"{doc.relative_to(ROOT)} has no Python snippets")
        for i, sample in enumerate(blocks, 1):
            snippets += 1
            try:
                ast.parse(sample, filename=f"{doc.name} snippet {i}")
            except SyntaxError as exc:
                errors.append(f"{doc.relative_to(ROOT)} snippet {i}: {exc}")
        if doc in answers:
            answered.extend(int(x) for x in SOLUTION_HEADER.findall(text))

    if sorted(answered) != list(range(1, 101)):
        errors.append("answer numbering is missing, duplicate or out of range")

    # Every exercise must have a numbered reference to a worked answer.
    prompts = (ROOT / "reference" / "100-EXERCISES.md").read_text(encoding="utf-8")
    if len(re.findall(r"(?m)^\d+\. \*\*Exercise \d{3} — ", prompts)) != 100:
        errors.append("100 exercises missing from prompt bank")
    if prompts.count("[worked answer]") != 100:
        errors.append("prompt-to-answer link count is not 100")

    nav = [
        ROOT / "README.md", ROOT / "course/README.md",
        ROOT / "lab-manual/README.md", ROOT / "solutions/by-exercise/README.md",
        ROOT / "reference/CHAPTER-INDEX.md",
        ROOT / "reference/100-EXERCISES.md",
        ROOT / "projects/BUILD-PATH.md",
    ] + all_files
    links_count = 0
    for path in nav:
        text = ANY_FENCE.sub("", path.read_text(encoding="utf-8"))
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            location = target.split("#", 1)[0].split("?", 1)[0]
            if not location:
                continue
            dest = (path.parent / location).resolve()
            links_count += 1
            if not dest.is_relative_to(ROOT) or not dest.exists():
                errors.append(f"{path.relative_to(ROOT)} missing link {target}")

    return errors, {
        "chapters": len(chapters), "labs": len(labs),
        "answer_volumes": len(answers), "answered_exercises": len(answered),
        "python_blocks": snippets, "local_links": links_count,
    }


def main() -> int:
    errors, summary = audit()
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("Curriculum audit passed:", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
