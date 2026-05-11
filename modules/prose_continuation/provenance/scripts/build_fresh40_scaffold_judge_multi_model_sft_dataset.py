from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAIR_DATA = (
    ROOT
    / "experiments"
    / "2026-04-27_fresh40_cut_manifest_tex_suffix_v2_anchor_views_p20_gap100_minpre10000_nonoverlap1800"
    / "generation_runs"
    / "2026-04-27_model_direct_y_3_p10000"
    / "small_qwen_scoring"
    / "nano_full_model_direct_y3_len1600_bundle"
    / "pair_data_long.jsonl"
)
REFERENCE_SPLIT = ROOT / "experiments" / "2026-04-28_fresh40_consumer_lora_realz_v1" / "dataset_v1"
DEFAULT_OUTPUT = (
    ROOT
    / "experiments"
    / "2026-05-02_fresh40_scaffold_judge_sft_nano_lmh_xb2000_xtail2000_z1000_v0"
    / "dataset_v1"
)


def main() -> None:
    args = parse_args()
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    split = load_paper_split(resolve(args.reference_split_dir) / "paper_split.jsonl")
    rows = load_rows(resolve(args.source_pair_data), parse_list(args.train_models), args.z_field)
    examples = build_examples(rows, split, args)

    write_jsonl(output_dir / "selected_examples.jsonl", examples)
    write_jsonl(output_dir / "train_completion.jsonl", [row for row in examples if row["split"] == "train"])
    write_jsonl(output_dir / "eval_completion.jsonl", [row for row in examples if row["split"] == "eval"])
    write_jsonl(output_dir / "paper_split.jsonl", [{"paper": paper, "split": part} for paper, part in sorted(split.items())])
    write_manifest(output_dir / "manifest.json", args, examples)
    write_readme(output_dir / "README.md", args, examples)
    print(json.dumps({"output_dir": str(output_dir), "counts": counts(examples)}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build multi-nano-model scaffold-aware judge SFT data.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--source-pair-data", default=str(SOURCE_PAIR_DATA))
    parser.add_argument("--reference-split-dir", default=str(REFERENCE_SPLIT))
    parser.add_argument("--train-models", default="gpt54_nano_low,gpt54_nano_medium,gpt54_nano_high")
    parser.add_argument("--x-source-field", default="predictor_x_text")
    parser.add_argument("--z-field", default="model_direct_y_3")
    parser.add_argument("--base-x-chars", type=int, default=2000)
    parser.add_argument("--x-tail-chars", type=int, default=2000)
    parser.add_argument("--z-budget-chars", type=int, default=1000)
    parser.add_argument("--notes-header", default="Notes about what's next:")
    parser.add_argument("--return-header", default="Returning to the paper text:")
    return parser.parse_args()


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_paper_split(path: Path) -> dict[str, str]:
    return {row["paper"]: row["split"] for row in load_jsonl(path)}


def load_rows(path: Path, models: list[str], z_field: str) -> list[dict[str, Any]]:
    model_set = set(models)
    rows = [
        row
        for row in load_jsonl(path)
        if row.get("model") in model_set
        and isinstance(row.get(z_field), str)
        and row.get(z_field, "").strip()
    ]
    rows.sort(key=lambda row: (int(row["pair_index"]), row["model"]))
    return rows


def build_examples(rows: list[dict[str, Any]], split: dict[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    examples = []
    for row in rows:
        paper = row["paper"]
        paper_split = split.get(paper)
        if paper_split is None:
            continue
        x_full = row[args.x_source_field]
        x_base = x_full[-args.base_x_chars :]
        x_tail = x_base[-args.x_tail_chars :] if args.x_tail_chars else ""
        z_raw = row[args.z_field].strip()
        z_text = z_raw[: args.z_budget_chars]
        y_prefix_ws, y_body = split_leading_whitespace(row["y_text"])
        prompt = scaffold_prompt(x_base, z_text, x_tail, y_prefix_ws, args)
        examples.append(
            {
                "split": paper_split,
                "dataset_row_index": -1,
                "paper": paper,
                "paper_id": paper,
                "pair_index": int(row["pair_index"]),
                "cut_id": int(row["pair_index"]),
                "source_pair_index": row.get("source_pair_index"),
                "cut_index": row.get("cut_index"),
                "section": row.get("section"),
                "train_model": row.get("model"),
                "condition": "scaffold_model_z",
                "predictor_model": row.get("model"),
                "x_source_field": args.x_source_field,
                "z_field": args.z_field,
                "base_x_chars": args.base_x_chars,
                "x_tail_chars": args.x_tail_chars,
                "z_budget_chars": args.z_budget_chars,
                "z_chars_used": len(z_text),
                "prompt_chars": len(prompt),
                "target_chars": len(y_body),
                "prompt": prompt,
                "completion": y_body,
                "target": y_body,
            }
        )
    for index, row in enumerate(examples):
        row["dataset_row_index"] = index
    return examples


def scaffold_prompt(x_base: str, z_text: str, x_tail: str, y_prefix_ws: str, args: argparse.Namespace) -> str:
    notes = f"% {args.notes_header}\n" + comment_lines(z_text) + "\n\n"
    return f"{x_base}\n\n{notes}% {args.return_header}\n{x_tail}{y_prefix_ws}"


def comment_lines(text: str) -> str:
    return "\n".join("% " + line.rstrip() for line in text.strip().splitlines())


def split_leading_whitespace(text: str) -> tuple[str, str]:
    match = re.match(r"\s*", text)
    prefix = match.group(0) if match else ""
    return prefix, text[len(prefix) :]


def write_manifest(path: Path, args: argparse.Namespace, examples: list[dict[str, Any]]) -> None:
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variant": "fresh40_scaffold_judge_sft_nano_lmh_v0",
        "purpose": "Larger scaffold-aware judge SFT using nano low/medium/high forecast Z on train papers.",
        "args": vars(args),
        "counts": counts(examples),
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_readme(path: Path, args: argparse.Namespace, examples: list[dict[str, Any]]) -> None:
    lines = [
        "# Fresh40 Scaffold-Aware Judge SFT: Nano Low/Medium/High v0",
        "",
        "This is a higher-volume sibling of the nano-low canonical SFT. It trains",
        "on `model_direct_y_3` forecast notes from nano low, medium, and high on",
        "train papers only, then leaves GPT-5.5 lanes as cleaner held-out",
        "benchmark-style probes.",
        "",
        "Settings:",
        f"- Models: `{args.train_models}`.",
        f"- X base chars: `{args.base_x_chars}`.",
        f"- X tail chars: `{args.x_tail_chars}`.",
        f"- Z budget chars: `{args.z_budget_chars}`.",
        "- Loss should be raw target-token NLL.",
        "- Boundary mode should be `full_offset`.",
        "",
        "Counts:",
        "```json",
        json.dumps(counts(examples), indent=2),
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def counts(examples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(examples),
        "cuts": len({row["pair_index"] for row in examples}),
        "by_split": dict(Counter(row["split"] for row in examples)),
        "by_model": dict(Counter(row["train_model"] for row in examples)),
        "by_split_model": dict(Counter(f"{row['split']}::{row['train_model']}" for row in examples)),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
