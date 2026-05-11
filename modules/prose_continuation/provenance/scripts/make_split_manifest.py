"""Create a fixed shuffled split manifest for a rendered cut view."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def prefix_tags(order_index: int, dev_cut: int) -> list[str]:
    tags = []
    if order_index < 10:
        tags.append("smoke10")
    if order_index < 20:
        tags.append("pilot20")
    if order_index < 60:
        tags.append("pilot60")
    if order_index < 100:
        tags.append("dev100")
    if order_index < dev_cut:
        tags.append("dev_half")
    else:
        tags.append("light_holdout_half")
    return tags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuts-jsonl", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260427)
    parser.add_argument("--view-name", required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.cuts_jsonl)
    rng = random.Random(args.seed)
    order = list(range(len(rows)))
    rng.shuffle(order)
    dev_cut = len(order) // 2

    output_rows = []
    for rank, source_index in enumerate(order):
        row = rows[source_index]
        split = "dev" if rank < dev_cut else "light_holdout"
        output_row = {
            "order_index": rank,
            "source_row_index": source_index,
            "split": split,
            "prefixes": prefix_tags(rank, dev_cut),
            "view_name": args.view_name,
            "paper_id": row["paper_id"],
            "cut_index": row["cut_index"],
            "section": row["section"],
            "judge_x_chars": row["judge_x_chars"],
            "predictor_x_chars": row["predictor_x_chars"],
            "y_chars": row["y_chars"],
            "has_equation": row["has_equation"],
            "has_theorem_like": row["has_theorem_like"],
            "has_proof": row["has_proof"],
        }
        for key in (
            "split_mode",
            "would_balance_reject",
            "split_inside_environment",
            "split_environment_stack",
        ):
            if key in row:
                output_row[key] = row[key]
        output_rows.append(output_row)

    write_jsonl(args.output_jsonl, output_rows)
    print(f"wrote {args.output_jsonl}")
    print(f"rows={len(output_rows)} dev={dev_cut} light_holdout={len(output_rows) - dev_cut}")
    for row in output_rows[:10]:
        print(f"{row['order_index']}: {row['paper_id']} cut={row['cut_index']} {row['section']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
