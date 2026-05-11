"""Strip row-specific outer display close delimiters from joined equation Zs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--joined", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    joined_path = resolve(args.joined)
    out_path = resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(joined_path)
    out_rows = []
    changed = []
    for row in rows:
        z_b = str(row.get("z_B", ""))
        stripped, close = strip_outer_close(z_b, str(row["env"]))
        new_row = {
            **row,
            "z_B_original": z_b,
            "z_raw_original": row.get("z_raw", ""),
            "z_B": stripped,
            "z_outer_close_stripped": stripped != z_b,
            "z_outer_close": close if stripped != z_b else "",
            "zB_len_original": len(z_b),
            "zB_len": len(stripped),
        }
        out_rows.append(new_row)
        if stripped != z_b:
            changed.append(
                {
                    "dataset_row_index": row["dataset_row_index"],
                    "env": row["env"],
                    "close": close,
                    "old_len": len(z_b),
                    "new_len": len(stripped),
                    "old_tail": z_b[-160:],
                    "new_tail": stripped[-160:],
                }
            )

    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in out_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/strip_equation_outer_close_from_joined.py",
        "joined_path": str(joined_path.relative_to(ROOT)),
        "out_path": str(out_path.relative_to(ROOT)),
        "row_count": len(rows),
        "changed_count": len(changed),
        "changed": changed,
    }
    summary_path = out_path.with_suffix(".strip_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def outer_close(env: str) -> str:
    return r"\]" if env == "bracket-display" else f"\\end{{{env}}}"


def strip_outer_close(text: str, env: str) -> tuple[str, str]:
    close = outer_close(env)
    pattern = re.compile(rf"(?P<body>.*?)(?:\s*{re.escape(close)}\s*)+\Z", re.DOTALL)
    match = pattern.fullmatch(text)
    if not match:
        return text, close
    return match.group("body").rstrip(), close


if __name__ == "__main__":
    main()
