"""Prepare OpenAI Batch requests for equation-cut predictor generations.

This is a dry-run/prep script by default: it writes the JSONL requests and
human-readable prompt previews, but does not upload or submit anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = (
    ROOT
    / "experiments"
    / "2026-04-30_equation_cut_pilot_5papers_p20_v0"
    / "equation_cut_dataset_5papers_p20_v0.jsonl"
)
DEFAULT_OUT_DIR = (
    ROOT
    / "experiments"
    / "2026-04-30_equation_cut_pilot_5papers_p20_v0"
    / "generation_runs"
    / "2026-04-30_gpt55_none_equation_suffix_v0"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--model", default="gpt-5.5-2026-04-23")
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument(
        "--prompt-variant",
        choices=["dataset", "actual_paper_style"],
        default="dataset",
        help="Use the prompt stored in the dataset, or build a new prompt variant from row fields.",
    )
    parser.add_argument("--preview-count", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0, help="If positive, only prepare first N rows.")
    parser.add_argument("--row-ids", type=int, nargs="*", help="If supplied, only prepare these dataset_row_index values.")
    parser.add_argument("--exclude-row-ids", type=int, nargs="*", default=[], help="Dataset row IDs to exclude.")
    args = parser.parse_args()

    dataset_path = resolve(args.dataset)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir = out_dir / "prompt_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(dataset_path)
    if args.row_ids is not None:
        wanted = set(args.row_ids)
        rows = [row for row in rows if int(row["dataset_row_index"]) in wanted]
        missing = sorted(wanted - {int(row["dataset_row_index"]) for row in rows})
        if missing:
            raise RuntimeError(f"Dataset does not contain requested row IDs: {missing}")
    if args.exclude_row_ids:
        excluded = set(args.exclude_row_ids)
        rows = [row for row in rows if int(row["dataset_row_index"]) not in excluded]
    if args.limit:
        rows = rows[: args.limit]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    request_path = out_dir / f"openai_batch_requests_{stamp}.jsonl"
    manifest_path = out_dir / f"openai_batch_manifest_{stamp}.json"

    requests: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for row in rows:
        custom_id = (
            f"eq_suffix|row-{row['dataset_row_index']:04d}|"
            f"{row['paper_id']}|eq-{row['equation_index']:04d}|cut-{row['cut_id']:04d}"
        )
        prompt = build_predictor_prompt(row, args.prompt_variant)
        request = build_request(
            custom_id=custom_id,
            model=args.model,
            prompt=prompt,
            max_output_tokens=args.max_output_tokens,
            reasoning_effort=args.reasoning_effort,
        )
        requests.append(request)
        tasks.append(
            {
                "custom_id": custom_id,
                "dataset_row_index": row["dataset_row_index"],
                "paper_id": row["paper_id"],
                "equation_index": row["equation_index"],
                "cut_id": row["cut_id"],
                "cut_source_line": row["cut_source_line"],
                "y_len": row["y_len"],
                "target_chars": row["target_chars"],
                "budget_chars": row["budget_chars"],
                "prompt_chars": len(prompt),
                "prompt_variant": args.prompt_variant,
                "predictor_context_chars": len(row.get("predictor_context", "")),
            }
        )

    with request_path.open("w", encoding="utf-8", newline="\n") as handle:
        for request in requests:
            handle.write(json.dumps(request, ensure_ascii=True) + "\n")

    for row, task in zip(rows[: args.preview_count], tasks[: args.preview_count]):
        preview_path = preview_dir / f"{task['dataset_row_index']:04d}_{task['paper_id']}_eq{task['equation_index']:04d}.txt"
        preview_path.write_text(render_preview(row, task), encoding="utf-8")

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/prepare_equation_openai_generation_batch.py",
        "purpose": "Equation-cut predictor generations.",
        "dataset_path": str(dataset_path.relative_to(ROOT)),
        "request_jsonl_path": str(request_path.relative_to(ROOT)),
        "preview_dir": str(preview_dir.relative_to(ROOT)),
        "endpoint": "/v1/responses",
        "completion_window": "24h",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens,
        "prompt_variant": args.prompt_variant,
        "row_ids": args.row_ids,
        "exclude_row_ids": args.exclude_row_ids,
        "request_count": len(requests),
        "dataset_sha256": sha256_file(dataset_path),
        "request_jsonl_sha256": sha256_file(request_path),
        "tasks": tasks,
        "submitted": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "request_count": len(requests),
        "request_jsonl": str(request_path),
        "manifest": str(manifest_path),
        "preview_dir": str(preview_dir),
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens,
    }, indent=2))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_predictor_prompt(row: dict[str, Any], variant: str) -> str:
    if variant == "dataset":
        return str(row["predictor_prompt"])
    if variant == "actual_paper_style":
        return (
            "You are given recent context from a technical paper and the beginning of a LaTeX display equation.\n\n"
            "Continue the equation exactly as you expect it is actually written in this paper. "
            "Match the paper's local notation, formatting, level of detail, and authorial style. "
            "Do not replace the paper's likely continuation with a cleaner or more complete derivation.\n\n"
            f"Continue from exactly where the equation stops, in about {row['budget_chars']} characters or fewer.\n\n"
            "Write only the continuation. Do not write explanatory prose. Do not write the closing display delimiter.\n\n"
            "Recent paper context:\n"
            f"{row['predictor_context']}\n\n"
            "Equation prefix:\n"
            f"{env_open(str(row['env']))}\n"
            f"{row['x_eq']}"
        )
    raise ValueError(f"Unknown prompt variant: {variant}")


def env_open(env: str) -> str:
    return r"\[" if env == "bracket-display" else f"\\begin{{{env}}}"


def build_request(
    *,
    custom_id: str,
    model: str,
    prompt: str,
    max_output_tokens: int,
    reasoning_effort: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "store": False,
        "tools": [],
    }
    if reasoning_effort:
        body["reasoning"] = {"effort": reasoning_effort}
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",
        "body": body,
    }


def render_preview(row: dict[str, Any], task: dict[str, Any]) -> str:
    prompt = build_predictor_prompt(row, str(task.get("prompt_variant", "dataset")))
    return (
        f"custom_id: {task['custom_id']}\n"
        f"paper_id: {row['paper_id']}\n"
        f"dataset_row_index: {row['dataset_row_index']}\n"
        f"equation_index: {row['equation_index']}\n"
        f"cut_source_line: {row['cut_source_line']}\n"
        f"y_len: {row['y_len']}\n"
        f"target_chars: {row['target_chars']}\n"
        f"budget_chars: {row['budget_chars']}\n"
        f"prompt_variant: {task.get('prompt_variant', 'dataset')}\n"
        f"prompt_chars: {task['prompt_chars']}\n"
        "\n"
        "=== PROMPT SENT TO OPENAI ===\n"
        f"{prompt}\n"
        "\n"
        "=== TRUE Y, NOT SENT TO PREDICTOR ===\n"
        f"{row['y']}\n"
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    main()
