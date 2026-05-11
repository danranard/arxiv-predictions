from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT
    / "data"
    / "frozen"
    / "scores"
    / "heldout33_softresid_no_z_control"
    / "data_holdout33_seed20260501_v0"
)


def main() -> None:
    args = parse_args()
    dataset_dir = resolve(args.dataset_dir)
    selected_path = dataset_dir / "selected_examples.jsonl"
    if not selected_path.exists():
        raise SystemExit(f"Missing selected_examples.jsonl in {dataset_dir}")

    selected = read_jsonl(selected_path)
    completion_rows = {
        split: read_jsonl(dataset_dir / f"{split}_completion.jsonl")
        for split in ["train", "eval", "test"]
        if (dataset_dir / f"{split}_completion.jsonl").exists()
    }

    first_by_split = [row for row in selected if int(row.get("repeat_index", 0)) == 0]
    summary: dict[str, Any] = {
        "dataset_dir": str(dataset_dir),
        "selected_rows": len(selected),
        "unique_cuts": len({cut_key(row) for row in selected}),
        "splits": {},
        "paper_overlap": {},
        "reconstruction_failures": 0,
        "completion_file_mismatches": 0,
        "warnings": [],
    }

    split_papers: dict[str, set[str]] = {}
    for split in ["train", "eval", "test"]:
        rows = [row for row in selected if row.get("split") == split]
        first = [row for row in rows if int(row.get("repeat_index", 0)) == 0]
        split_papers[split] = {row["paper_id"] for row in rows}
        summary["splits"][split] = split_summary(rows, first, completion_rows.get(split, []))

    for left in ["train", "eval", "test"]:
        for right in ["train", "eval", "test"]:
            if left >= right:
                continue
            overlap = sorted(split_papers[left] & split_papers[right])
            summary["paper_overlap"][f"{left}_{right}"] = overlap
            if overlap:
                summary["warnings"].append(f"paper overlap {left}/{right}: {overlap}")

    completion_counters: dict[str, Counter[tuple[str, str]]] = {}
    for split, rows in completion_rows.items():
        completion_counters[split] = Counter((row["prompt"], row["completion"]) for row in rows)

    for row in selected:
        expected = row.get("expected_full_for_audit")
        if expected is not None and row["prompt"] + row["completion"] != expected:
            summary["reconstruction_failures"] += 1
        split = row["split"]
        pair = (row["prompt"], row["completion"])
        if pair not in completion_counters.get(split, Counter()):
            summary["completion_file_mismatches"] += 1

    if summary["reconstruction_failures"]:
        summary["warnings"].append("prompt + completion reconstruction failures present")
    if summary["completion_file_mismatches"]:
        summary["warnings"].append("selected_examples rows missing from *_completion files")

    out = json.dumps(summary, indent=2)
    if args.output:
        output = resolve(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(out + "\n", encoding="utf-8")
    print(out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sanity-check no-Z SFT raw-completion data for clip2 LoRA training.")
    parser.add_argument("--dataset-dir", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output")
    return parser.parse_args()


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    return ROOT / candidate


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cut_key(row: dict[str, Any]) -> tuple[str, int, int]:
    return (row["paper_id"], int(row["equation_index"]), int(row["cut_id"]))


def split_summary(
    rows: list[dict[str, Any]],
    first_rows: list[dict[str, Any]],
    completion_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt_lens = [len(row["prompt"]) for row in rows]
    completion_lens = [len(row["completion"]) for row in rows]
    repeat_counts = Counter(int(row.get("repeat_count", 1)) for row in rows)
    return {
        "selected_rows": len(rows),
        "completion_rows": len(completion_rows),
        "unique_cuts": len({cut_key(row) for row in rows}),
        "unique_papers": len({row["paper_id"] for row in rows}),
        "repeat_count_values": dict(sorted(repeat_counts.items())),
        "prompt_chars": length_stats(prompt_lens),
        "completion_chars": length_stats(completion_lens),
        "y_prefix_ws_counts": dict(Counter(row.get("y_prefix_ws_repr", "") for row in first_rows)),
        "boundary_pairs": {
            f"{left} -> {right}": count
            for (left, right), count in Counter(
                (repr(row["prompt"][-1:] if row["prompt"] else ""), repr(row["completion"][:1])) for row in first_rows
            ).items()
        },
    }


def length_stats(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    n = len(ordered)
    return {
        "min": ordered[0],
        "p10": ordered[int(0.1 * (n - 1))],
        "median": ordered[n // 2],
        "p90": ordered[int(0.9 * (n - 1))],
        "max": ordered[-1],
        "mean": round(sum(ordered) / n, 2),
    }


if __name__ == "__main__":
    main()
