from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = (
    ROOT
    / "experiments"
    / "2026-04-27_fresh40_cut_manifest_tex_suffix_v2_anchor_views_p20_gap100_minpre10000_nonoverlap1800"
    / "generation_runs"
    / "2026-04-27_model_direct_y_3_p10000"
)
SCORING_DIR = RUN_DIR / "small_qwen_scoring"
DEFAULT_SOURCE_BUNDLES = [
    SCORING_DIR / "available_gpt55_model_direct_y3_len1600_bundle" / "pair_data_long.jsonl",
    SCORING_DIR / "gpt55_high_full_model_direct_y3_len1600_bundle" / "pair_data_long.jsonl",
    SCORING_DIR / "nano_full_model_direct_y3_len1600_bundle" / "pair_data_long.jsonl",
]
REFERENCE_SPLIT = ROOT / "experiments" / "2026-04-28_fresh40_consumer_lora_realz_v1" / "dataset_v1"
DEFAULT_OUTPUT = (
    ROOT
    / "experiments"
    / "2026-05-02_fresh40_scaffold_judge_sft_nanolow_xb2000_xtail2000_z1000_v0"
    / "eval_prompts_v1"
)
DEFAULT_MODELS = [
    "gpt54_nano_low",
    "gpt54_nano_medium",
    "gpt54_nano_high",
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
]
DEFAULT_CONDITIONS = [
    "bare_x_base_plus_z",
    "scaffold_empty",
    "scaffold_z_prev_to_tail",
    "scaffold_z_tail_end",
    "scaffold_model_z",
]


def main() -> None:
    args = parse_args()
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    split = load_paper_split(resolve(args.reference_split_dir) / "paper_split.jsonl")
    source_rows = load_source_rows([resolve(path) for path in args.source_pair_data])
    rows = build_eval_rows(source_rows, split, args)

    write_jsonl(output_dir / "selected_examples.jsonl", rows)
    write_manifest(output_dir / "manifest.json", args, rows)
    write_readme(output_dir / "README.md", args, rows)
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "rows": len(rows),
                "counts": count_rows(rows),
            },
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build held-out eval prompt/completion rows for a scaffold-aware Qwen LoRA."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--reference-split-dir", default=str(REFERENCE_SPLIT))
    parser.add_argument(
        "--source-pair-data",
        nargs="+",
        default=[str(path) for path in DEFAULT_SOURCE_BUNDLES],
    )
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--eval-split", choices=["eval", "train", "all"], default="eval")
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


def load_paper_split(path: Path) -> dict[str, str]:
    return {row["paper"]: row["split"] for row in load_jsonl(path)}


def load_source_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(load_jsonl(path))
    return rows


def build_eval_rows(
    rows: list[dict[str, Any]],
    paper_split: dict[str, str],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    wanted_models = parse_list(args.models)
    conditions = parse_list(args.conditions)
    rows_by_cut_model: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        paper = row["paper"]
        split = paper_split.get(paper)
        if split is None:
            continue
        if args.eval_split != "all" and split != args.eval_split:
            continue
        row = dict(row)
        row["_paper_split"] = split
        model = row.get("model")
        if model not in wanted_models:
            continue
        if not row.get(args.z_field):
            continue
        rows_by_cut_model[int(row["pair_index"])][model] = row

    out: list[dict[str, Any]] = []
    for pair_index in sorted(rows_by_cut_model):
        model_rows = rows_by_cut_model[pair_index]
        base_row = next(iter(model_rows.values()))
        x_full = base_row[args.x_source_field]
        x_base = x_full[-args.base_x_chars :]
        x_tail = x_base[-args.x_tail_chars :] if args.x_tail_chars else ""
        y_prefix_ws, y_body = split_leading_whitespace(base_row["y_text"])
        control_z = {
            "scaffold_empty": "",
            "scaffold_z_prev_to_tail": context_before_tail(
                x_full, args.x_tail_chars, args.z_budget_chars
            ),
            "scaffold_z_tail_end": x_base[-args.z_budget_chars :],
        }
        for condition in conditions:
            if condition == "bare_x_base_plus_z":
                prompt = x_full[-(args.base_x_chars + args.z_budget_chars) :] + y_prefix_ws
                out.append(row_record(base_row, args, condition, "control", prompt, y_body, ""))
            elif condition in control_z:
                z_text = control_z[condition]
                prompt = scaffold_prompt(x_base, z_text, x_tail, y_prefix_ws, args)
                out.append(row_record(base_row, args, condition, "control", prompt, y_body, z_text))
            elif condition == "scaffold_model_z":
                for model in wanted_models:
                    row = model_rows.get(model)
                    if not row:
                        continue
                    z_text = row[args.z_field].strip()[: args.z_budget_chars]
                    prompt = scaffold_prompt(x_base, z_text, x_tail, y_prefix_ws, args)
                    out.append(row_record(row, args, condition, model, prompt, y_body, z_text))
            else:
                raise ValueError(f"unknown condition={condition!r}")
    for index, row in enumerate(out):
        row["dataset_row_index"] = index
    return out


def row_record(
    source: dict[str, Any],
    args: argparse.Namespace,
    condition: str,
    predictor_model: str,
    prompt: str,
    completion: str,
    z_text: str,
) -> dict[str, Any]:
    split = source.get("_paper_split", args.eval_split)
    return {
        "split": split,
        "dataset_row_index": -1,
        "paper": source["paper"],
        "paper_id": source["paper"],
        "pair_index": int(source["pair_index"]),
        "cut_id": int(source["pair_index"]),
        "source_pair_index": source.get("source_pair_index"),
        "cut_index": source.get("cut_index"),
        "section": source.get("section"),
        "condition": condition,
        "predictor_model": predictor_model,
        "source_model": source.get("model"),
        "x_source_field": args.x_source_field,
        "z_field": args.z_field,
        "base_x_chars": args.base_x_chars,
        "x_tail_chars": args.x_tail_chars,
        "z_budget_chars": args.z_budget_chars,
        "z_chars_used": len(z_text),
        "prompt_chars": len(prompt),
        "target_chars": len(completion),
        "prompt": prompt,
        "completion": completion,
        "target": completion,
    }


def context_before_tail(context: str, x_tail_chars: int, z_budget_chars: int) -> str:
    if x_tail_chars <= 0:
        return context[-z_budget_chars:]
    tail_start = max(0, len(context) - x_tail_chars)
    chunk_start = max(0, tail_start - z_budget_chars)
    return context[chunk_start:tail_start]


def scaffold_prompt(
    x_base: str,
    z_text: str,
    x_tail: str,
    y_prefix_ws: str,
    args: argparse.Namespace,
) -> str:
    if z_text.strip():
        notes = f"% {args.notes_header}\n" + comment_lines(z_text) + "\n\n"
    else:
        notes = f"% {args.notes_header}\n\n"
    return f"{x_base}\n\n{notes}% {args.return_header}\n{x_tail}{y_prefix_ws}"


def comment_lines(text: str) -> str:
    return "\n".join("% " + line.rstrip() for line in text.strip().splitlines())


def split_leading_whitespace(text: str) -> tuple[str, str]:
    match = re.match(r"\s*", text)
    prefix = match.group(0) if match else ""
    return prefix, text[len(prefix) :]


def parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def write_manifest(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variant": "fresh40_scaffold_judge_sft_eval_prompts_v1",
        "purpose": "Held-out prompt/completion rows for scoring the scaffold-aware Qwen LoRA.",
        "args": vars(args),
        "counts": count_rows(rows),
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_readme(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Fresh40 Scaffold-Aware Judge Eval Prompts v1",
        "",
        "Held-out prompt/completion rows for scoring the canonical nano-low",
        "scaffold-aware Qwen LoRA. These are not training rows.",
        "",
        "Settings:",
        "",
        f"- Eval split: `{args.eval_split}`.",
        f"- X source field: `{args.x_source_field}`.",
        f"- X base chars: `{args.base_x_chars}`.",
        f"- X tail chars: `{args.x_tail_chars}`.",
        f"- Z budget chars: `{args.z_budget_chars}`.",
        "",
        "Counts:",
        "",
        "```json",
        json.dumps(count_rows(rows), indent=2),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def count_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "cuts": len({row["pair_index"] for row in rows}),
        "by_condition": dict(Counter(row["condition"] for row in rows)),
        "by_predictor_model": dict(Counter(row["predictor_model"] for row in rows)),
        "by_condition_model": dict(
            Counter(f"{row['condition']}::{row['predictor_model']}" for row in rows)
        ),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
