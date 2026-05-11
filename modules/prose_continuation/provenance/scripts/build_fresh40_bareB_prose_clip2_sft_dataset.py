"""Build prose bare-context SFT datasets for clip2 hard-control runs.

This creates plain continuation examples analogous to the equation-split
``bare_B`` control. For the current prose geometry, the prompt is the final
3000 contiguous chars before the cut: the ordinary 2000-char local context plus
an extra 1000 chars matching the forecast-Z budget.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PAIR_DATA = (
    ROOT
    / "experiments"
    / "2026-04-27_fresh40_cut_manifest_tex_suffix_v2_anchor_views_p20_gap100_minpre10000_nonoverlap1800"
    / "generation_runs"
    / "2026-04-27_model_direct_y_3_p10000"
    / "small_qwen_scoring"
    / "nano_full_model_direct_y3_len1600_bundle"
    / "pair_data_long.jsonl"
)
DEFAULT_REFERENCE_SPLIT_DIR = (
    ROOT
    / "experiments"
    / "2026-05-02_fresh40_scaffold_judge_sft_nanolow_xb2000_xtail2000_z1000_v0"
    / "dataset_v1"
)
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0"
    / "dataset_v1"
)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    split_rows = read_jsonl(Path(args.reference_split_dir) / "selected_examples.jsonl")
    split_by_key = {
        key_for(row): {
            "split": row["split"],
            "dataset_row_index": row["dataset_row_index"],
            "target": row["target"],
            "target_chars": row["target_chars"],
        }
        for row in split_rows
    }

    source_rows = []
    for row in read_jsonl(Path(args.source_pair_data)):
        if row.get("model") != args.source_model:
            continue
        key = (row["paper"], row["pair_index"], row["source_pair_index"])
        if key not in split_by_key:
            continue
        split_meta = split_by_key[key]
        target = row["y_text"].lstrip()
        if target != split_meta["target"]:
            raise ValueError(f"target mismatch for {key}")
        x_full = row["predictor_x_text"]
        prompt = x_full[-args.context_chars :]
        if len(prompt) != args.context_chars:
            raise ValueError(f"short prompt for {key}: {len(prompt)}")
        if row["x_text"][-args.local_context_chars :] != prompt[-args.local_context_chars :]:
            raise ValueError(f"local-context tail mismatch for {key}")
        source_rows.append(
            {
                "split": split_meta["split"],
                "dataset_row_index": split_meta["dataset_row_index"],
                "paper": row["paper"],
                "paper_id": row["paper"],
                "pair_index": row["pair_index"],
                "cut_id": row["pair_index"],
                "source_pair_index": row["source_pair_index"],
                "cut_index": row["cut_index"],
                "section": row["section"],
                "model": "control",
                "source_model": args.source_model,
                "condition": "bare_B_prose_x3000",
                "prompt": prompt,
                "target": target,
                "completion": target,
                "prompt_chars": len(prompt),
                "target_chars": len(target),
                "context_chars": args.context_chars,
                "local_context_chars": args.local_context_chars,
                "extra_budget_context_chars": args.context_chars - args.local_context_chars,
                "view_name": row["view_name"],
            }
        )

    source_rows.sort(key=lambda row: (row["split"], row["paper"], row["pair_index"]))
    if len(source_rows) != len(split_by_key):
        raise ValueError(f"expected {len(split_by_key)} rows, got {len(source_rows)}")

    write_jsonl(output_dir / "selected_examples.jsonl", source_rows)
    for target_chars in args.target_windows:
        for split in ("train", "eval"):
            rows = [make_completion_row(row, target_chars) for row in source_rows if row["split"] == split]
            write_jsonl(output_dir / f"{split}_y{target_chars}_completion.jsonl", rows)
    for eval_chars in args.eval_windows:
        rows = [make_completion_row(row, eval_chars) for row in source_rows if row["split"] == "eval"]
        write_jsonl(output_dir / f"eval_y{eval_chars}_completion.jsonl", rows)

    by_split = Counter(row["split"] for row in source_rows)
    by_split_paper = Counter(f"{row['split']}::{row['paper']}" for row in source_rows)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variant": "fresh40_bareB_prose_clip2_sft_x3000_v0",
        "purpose": (
            "Prose hard-control SFT analogous to equation bare_B: train Qwen3-8B "
            "on plain 3000-char pre-target continuation, with clip2/residual objectives."
        ),
        "source_pair_data": str(Path(args.source_pair_data).resolve()),
        "reference_split_dir": str(Path(args.reference_split_dir).resolve()),
        "source_model": args.source_model,
        "context_chars": args.context_chars,
        "local_context_chars": args.local_context_chars,
        "extra_budget_context_chars": args.context_chars - args.local_context_chars,
        "target_windows": args.target_windows,
        "eval_windows": args.eval_windows,
        "split_counts": dict(by_split),
        "split_paper_counts": dict(sorted(by_split_paper.items())),
        "files": {
            "selected_examples": "selected_examples.jsonl",
            "train_y200": "train_y200_completion.jsonl",
            "train_y1000": "train_y1000_completion.jsonl",
            "eval_y100": "eval_y100_completion.jsonl",
            "eval_y200": "eval_y200_completion.jsonl",
            "eval_y500": "eval_y500_completion.jsonl",
            "eval_y1000": "eval_y1000_completion.jsonl",
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_preview(output_dir / "PREVIEW.md", source_rows)
    print(json.dumps({"output_dir": str(output_dir), "rows": len(source_rows), "split_counts": dict(by_split)}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-pair-data", default=str(DEFAULT_SOURCE_PAIR_DATA))
    parser.add_argument("--reference-split-dir", default=str(DEFAULT_REFERENCE_SPLIT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--source-model", default="gpt54_nano_low")
    parser.add_argument("--context-chars", type=int, default=3000)
    parser.add_argument("--local-context-chars", type=int, default=2000)
    parser.add_argument("--target-windows", type=int, nargs="+", default=[200, 1000])
    parser.add_argument("--eval-windows", type=int, nargs="+", default=[100, 200, 500, 1000])
    return parser.parse_args()


def key_for(row: dict) -> tuple[str, int, int]:
    return (row["paper"], row["pair_index"], row["source_pair_index"])


def make_completion_row(row: dict, target_chars: int) -> dict:
    completion = row["target"][:target_chars]
    return {
        **{key: row[key] for key in (
            "split",
            "dataset_row_index",
            "paper",
            "paper_id",
            "pair_index",
            "cut_id",
            "source_pair_index",
            "cut_index",
            "section",
            "model",
            "source_model",
            "condition",
            "context_chars",
            "local_context_chars",
            "extra_budget_context_chars",
            "view_name",
        )},
        "target_window_chars": target_chars,
        "prompt": row["prompt"],
        "completion": completion,
        "target": completion,
        "prompt_chars": len(row["prompt"]),
        "target_chars": len(completion),
    }


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write_preview(path: Path, rows: list[dict]) -> None:
    sample = rows[:3]
    lines = [
        "# Bare-B Prose SFT Dataset Preview",
        "",
        "Prompt is the final 3000 contiguous chars before the cut.",
        "The extra 1000 chars beyond the local 2000-char context match the Z budget.",
        "",
    ]
    for row in sample:
        lines.extend(
            [
                f"## {row['split']} {row['paper']} pair {row['pair_index']}",
                "",
                "Prompt tail:",
                "",
                "```text",
                row["prompt"][-1200:],
                "```",
                "",
                "Target head:",
                "",
                "```text",
                row["target"][:1000],
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
