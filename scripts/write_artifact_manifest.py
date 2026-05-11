from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.io_utils import sha256_file, write_json


SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
SKIP_FILES = {"ARTIFACT_MANIFEST.json"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a sha256 manifest for the clean artifact.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=ROOT / "ARTIFACT_MANIFEST.json")
    args = parser.parse_args()
    root = args.root if args.root.is_absolute() else ROOT / args.root
    out = args.out if args.out.is_absolute() else ROOT / args.out
    files = []
    out_resolved = out.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.resolve() == out_resolved:
            continue
        rel = path.relative_to(root).as_posix()
        if path.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": ".",
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "excluded_dirs": sorted(SKIP_DIRS),
        "files": files,
    }
    write_json(out, manifest)
    print(json.dumps({"out": str(out), "file_count": manifest["file_count"], "total_bytes": manifest["total_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
