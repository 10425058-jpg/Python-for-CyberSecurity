"""Project 1: bounded local file integrity inventory (read-only acquisition).

The tool never follows symlinks intentionally, and does not write into source
directories. It is educational, not a forensic-grade race-free snapshotter.
Use only on directories you own or are authorized to inspect.

Usage:
    python -m projects.builds.integrity_inventory ROOT --max-files 1000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

MAX_ALLOWED_FILES = 100_000
MAX_ALLOWED_BYTES = 1024 * 1024 * 1024


def _file_sha256(path: Path, *, max_bytes: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            size += len(chunk)
            if size > max_bytes:
                raise ValueError(f"file size limit exceeded for {path.name}")
            digest.update(chunk)
    return digest.hexdigest(), size


def inventory(root: Path, *, max_files: int = 1000,
              max_file_bytes: int = 10_000_000) -> dict:
    """Return a deterministic inventory. An error invalidates the entire run."""
    if type(max_files) is not int or not 1 <= max_files <= MAX_ALLOWED_FILES:
        raise ValueError("max_files outside allowed range")
    if type(max_file_bytes) is not int or not 1 <= max_file_bytes <= MAX_ALLOWED_BYTES:
        raise ValueError("max_file_bytes outside allowed range")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("root must be a real directory (not a symlink)")
    root = root.resolve()
    records = []
    def onerror(error):
        raise error
    for parent, dirs, files in os.walk(root, topdown=True, followlinks=False,
                                       onerror=onerror):
        here = Path(parent)
        dirs[:] = sorted(
            d for d in dirs if not (here / d).is_symlink()
        )
        for name in sorted(files):
            path = here / name
            if path.is_symlink():
                continue
            if not path.is_file():
                continue
            if len(records) >= max_files:
                raise ValueError("file count limit exceeded")
            digest, count = _file_sha256(path, max_bytes=max_file_bytes)
            records.append({
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": count,
                "sha256": digest,
            })
    records.sort(key=lambda row: row["relative_path"])
    return {"format": "toy-integrity-v1", "complete": True,
            "root_label": root.name, "files": records}


def compare(before: dict, after: dict) -> dict:
    """Describe changed, added and removed files; assume validated manifests."""
    if before.get("format") != "toy-integrity-v1" or after.get("format") != "toy-integrity-v1":
        raise ValueError("unsupported manifest version")
    if before.get("root_label") != after.get("root_label"):
        raise ValueError("snapshots have different root labels")
    for m in (before, after):
        if m.get("complete") is not True or type(m.get("files")) is not list:
            raise ValueError("incomplete or invalid inventory")
        if len(m["files"]) > MAX_ALLOWED_FILES:
            raise ValueError("manifest too large")
        for row in m["files"]:
            if type(row) is not dict or set(row) != {"relative_path","size_bytes","sha256"}:
                raise ValueError("bad manifest record")
            if type(row["relative_path"]) is not str or len(row["relative_path"]) > 4096:
                raise ValueError("bad path")
            if type(row["size_bytes"]) is not int or row["size_bytes"] < 0:
                raise ValueError("bad size")
            if type(row["sha256"]) is not str or len(row["sha256"]) != 64:
                raise ValueError("bad digest")
    old = {r["relative_path"]: r for r in before["files"]}
    new = {r["relative_path"]: r for r in after["files"]}
    if len(old) != len(before["files"]) or len(new) != len(after["files"]):
        raise ValueError("duplicate paths in manifest")
    return {
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "changed": sorted(
            k for k in old.keys() & new.keys()
            if old[k]["sha256"] != new[k]["sha256"] or
               old[k]["size_bytes"] != new[k]["size_bytes"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--max-files", type=int, default=1000)
    ap.add_argument("--max-file-bytes", type=int, default=10_000_000)
    args = ap.parse_args(argv)
    try:
        result = inventory(args.root, max_files=args.max_files,
                           max_file_bytes=args.max_file_bytes)
    except (ValueError, OSError) as exc:
        print(f"incomplete inventory: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
