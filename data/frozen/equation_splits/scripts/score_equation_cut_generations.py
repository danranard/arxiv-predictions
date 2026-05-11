"""Score equation-cut predictor generations with an OpenAI-compatible logprob judge."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rlvr_forecast.judges.openai_completions import (  # noqa: E402
    OpenAICompletionLogprobJudge,
    extract_prompt_logprobs_for_choices,
    normalized_text_offsets,
)


DEFAULT_JOINED = (
    ROOT
    / "experiments"
    / "2026-04-30_equation_cut_pilot_5papers_p20_v0"
    / "generation_runs"
    / "2026-04-30_gpt55_none_equation_suffix_v0"
    / "gpt55_none_generations_joined.jsonl"
)
DEFAULT_OUT = (
    ROOT
    / "experiments"
    / "2026-04-30_equation_cut_pilot_5papers_p20_v0"
    / "generation_runs"
    / "2026-04-30_gpt55_none_equation_suffix_v0"
    / "small_qwen_scoring"
    / "copy_scaffold_controls_body_plus_close_v0"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--joined", type=Path, default=DEFAULT_JOINED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--judge-model", default="accounts/fireworks/models/qwen3-8b")
    parser.add_argument("--base-url", default="https://api.fireworks.ai/inference/v1")
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument(
        "--target-mode",
        choices=["body", "body_plus_close"],
        default="body_plus_close",
        help="Score just Y, or Y plus the newline and display-equation close delimiter.",
    )
    parser.add_argument(
        "--bare-multipliers",
        type=float,
        nargs="+",
        default=[1.0],
        help="Raw contiguous controls to score, as multiples of B=len(Y)+slack.",
    )
    parser.add_argument("--no-bare-controls", action="store_true", help="Do not score any bare-context controls.")
    parser.add_argument(
        "--comparison-baseline",
        default="bare_B",
        help="Condition to subtract from scaffold_z_predictor in the headline summary.",
    )
    parser.add_argument(
        "--scaffold-variant",
        choices=[
            "current",
            "same_final_version",
            "same_or_slight_variant",
            "commented_draft_final",
        ],
        default="current",
        help="Text scaffold used for conditions that insert Z before the scored equation.",
    )
    parser.add_argument(
        "--include-scaffold-raw-precontext",
        action="store_true",
        help="Also score a same-scaffold condition with raw_precontext_budget inserted into the Z slot.",
    )
    parser.add_argument("--limit", type=int, default=0, help="If positive, only score the first N joined rows.")
    parser.add_argument("--no-scaffold-empty", action="store_true", help="Do not score the no-Z scaffold condition.")
    parser.add_argument("--no-oracle", action="store_true", help="Do not score the scaffold oracle-Y condition.")
    parser.add_argument(
        "--only-conditions",
        nargs="+",
        default=None,
        help="After constructing jobs, keep only these condition names. Useful for fast model-vs-model updates.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing output CSVs and skip row/condition pairs already scored in this output dir.",
    )
    parser.add_argument(
        "--force-row-ids",
        type=int,
        nargs="+",
        default=[],
        help=(
            "When used with --resume, drop existing score/token rows for these dataset_row_index values "
            "and re-score them. Useful after replacing predictor generations."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    joined_path = resolve(args.joined)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(joined_path)
    if args.limit:
        rows = rows[: args.limit]
    jobs = build_jobs(
        rows,
        target_mode=args.target_mode,
        bare_multipliers=[] if args.no_bare_controls else args.bare_multipliers,
        scaffold_variant=args.scaffold_variant,
        include_scaffold_empty=not args.no_scaffold_empty,
        include_oracle=not args.no_oracle,
        include_scaffold_raw_precontext=args.include_scaffold_raw_precontext,
    )
    if args.only_conditions:
        wanted_conditions = set(args.only_conditions)
        known_conditions = {job["condition"] for job in jobs}
        missing_conditions = sorted(wanted_conditions - known_conditions)
        if missing_conditions:
            raise SystemExit(
                "Unknown --only-conditions entries: "
                + ", ".join(missing_conditions)
                + ". Known: "
                + ", ".join(sorted(known_conditions))
            )
        jobs = [job for job in jobs if job["condition"] in wanted_conditions]

    existing_score_rows: list[dict[str, Any]] = []
    existing_token_rows: list[dict[str, Any]] = []
    skipped_existing = 0
    if args.resume:
        existing_score_rows = read_csv(output_dir / "equation_scores.csv")
        existing_token_rows = read_csv(output_dir / "equation_target_token_logprobs.csv")
        force_row_ids = set(args.force_row_ids)
        if force_row_ids:
            existing_score_rows = [
                row for row in existing_score_rows if int(row["dataset_row_index"]) not in force_row_ids
            ]
            existing_token_rows = [
                row for row in existing_token_rows if int(row["dataset_row_index"]) not in force_row_ids
            ]
        done_keys = {
            (int(row["dataset_row_index"]), row["condition"], row.get("target_mode", args.target_mode))
            for row in existing_score_rows
        }
        before = len(jobs)
        jobs = [
            job
            for job in jobs
            if (int(job["dataset_row_index"]), job["condition"], job["target_mode"]) not in done_keys
        ]
        skipped_existing = before - len(jobs)

    conditions = sorted({job["condition"] for job in jobs})
    write_json(output_dir / "run_plan.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/score_equation_cut_generations.py",
        "joined_path": str(joined_path.relative_to(ROOT)),
        "judge_model": args.judge_model,
        "base_url": args.base_url,
        "batch_size": args.batch_size,
        "target_mode": args.target_mode,
        "bare_multipliers": [] if args.no_bare_controls else args.bare_multipliers,
        "include_bare_controls": not args.no_bare_controls,
        "comparison_baseline": args.comparison_baseline,
        "scaffold_variant": args.scaffold_variant,
        "limit": args.limit,
        "include_scaffold_empty": not args.no_scaffold_empty,
        "include_oracle": not args.no_oracle,
        "include_scaffold_raw_precontext": args.include_scaffold_raw_precontext,
        "only_conditions": args.only_conditions,
        "resume": args.resume,
        "force_row_ids": args.force_row_ids,
        "existing_score_rows": len(existing_score_rows),
        "existing_token_rows": len(existing_token_rows),
        "skipped_existing_jobs": skipped_existing,
        "conditions": conditions,
        "row_count": len(rows),
        "job_count": len(jobs),
        "jobs_preview": [
            {k: job[k] for k in ("dataset_row_index", "paper_id", "equation_index", "condition", "prompt_chars", "target_chars")}
            for job in jobs[:8]
        ],
    })
    write_prompt_previews(output_dir / "prompt_previews", jobs[:8])
    if args.dry_run:
        print(json.dumps(
            {
                "dry_run": True,
                "rows": len(rows),
                "jobs_to_score": len(jobs),
                "skipped_existing_jobs": skipped_existing,
                "output_dir": str(output_dir),
            },
            indent=2,
        ))
        return

    score_rows: list[dict[str, Any]] = existing_score_rows.copy()
    token_rows: list[dict[str, Any]] = existing_token_rows.copy()
    started = time.time()
    if not jobs:
        summary = summarize(score_rows, token_rows, baseline_condition=args.comparison_baseline)
        write_json(output_dir / "summary.json", summary)
        write_readme(output_dir, args, summary, elapsed=0.0)
        print(json.dumps({**summary, "scored_now": 0, "skipped_existing_jobs": skipped_existing}, indent=2, ensure_ascii=False))
        return

    judge = OpenAICompletionLogprobJudge(
        model=args.judge_model,
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
    )

    for start in range(0, len(jobs), args.batch_size):
        chunk = jobs[start : start + args.batch_size]
        chunk_scores, chunk_tokens = score_chunk(judge, chunk, args.judge_model)
        score_rows.extend(chunk_scores)
        token_rows.extend(chunk_tokens)
        print(
            f"[{datetime.now(timezone.utc).isoformat()}] "
            f"scored {min(start + len(chunk), len(jobs))}/{len(jobs)} "
            f"elapsed={time.time() - started:.1f}s",
            flush=True,
        )

    write_csv(output_dir / "equation_scores.csv", score_rows)
    write_csv(output_dir / "equation_target_token_logprobs.csv", token_rows)
    summary = summarize(score_rows, token_rows, baseline_condition=args.comparison_baseline)
    write_json(output_dir / "summary.json", summary)
    write_readme(output_dir, args, summary, elapsed=time.time() - started)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def env_open(env: str) -> str:
    return r"\[" if env == "bracket-display" else f"\\begin{{{env}}}"


def env_close(env: str) -> str:
    return r"\]" if env == "bracket-display" else f"\\end{{{env}}}"


def split_leading_whitespace(text: str) -> tuple[str, str]:
    match = re.match(r"\s*", text)
    prefix = match.group(0) if match else ""
    return prefix, text[len(prefix):]


def comment_tex_block(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return "%"
    return "\n".join(f"% {line}" if line else "%" for line in lines)


def scaffold_prefix(row: dict[str, Any], z: str, variant: str) -> str:
    first_equation = (
        f"{env_open(row['env'])}\n"
        f"{row['x_eq']}{z}\n"
        f"{env_close(row['env'])}"
    )
    second_equation_prefix = f"{env_open(row['env'])}\n{row['x_eq']}"

    if variant == "current":
        return (
            "% First equation:\n"
            f"{first_equation}\n\n"
            "% Same equation:\n"
            f"{second_equation_prefix}"
        )
    if variant == "same_final_version":
        return (
            "% First equation:\n"
            f"{first_equation}\n\n"
            "% Same equation, final version:\n"
            f"{second_equation_prefix}"
        )
    if variant == "same_or_slight_variant":
        return (
            "% First equation:\n"
            f"{first_equation}\n\n"
            "% Same equation or slight variant:\n"
            f"{second_equation_prefix}"
        )
    if variant == "commented_draft_final":
        return (
            "% Draft:\n"
            f"{comment_tex_block(first_equation)}\n\n"
            "% Final:\n"
            f"{second_equation_prefix}"
        )
    raise ValueError(f"Unknown scaffold variant {variant!r}")


def bare_condition_name(multiplier: float) -> str:
    if abs(multiplier - 1.0) < 1e-9:
        return "bare_B"
    if float(multiplier).is_integer():
        return f"bare_{int(multiplier)}B"
    return f"bare_{multiplier:g}B"


def bare_prefix(row: dict[str, Any], multiplier: float) -> str:
    if abs(multiplier - 1.0) < 1e-9:
        return row["bare_b_judge_prompt_prefix"]
    tail_chars = max(0, int(math.ceil(float(row["budget_chars"]) * multiplier)))
    context = row["predictor_context"][-tail_chars:].rstrip()
    return f"{context}\n{env_open(row['env'])}\n{row['x_eq']}"


def target_text_for_mode(row: dict[str, Any], y_body: str, target_mode: str) -> str:
    if target_mode == "body":
        return y_body
    if target_mode == "body_plus_close":
        return f"{y_body}\n{env_close(row['env'])}"
    raise ValueError(f"Unknown target_mode={target_mode!r}")


def build_jobs(
    rows: list[dict[str, Any]],
    target_mode: str,
    bare_multipliers: list[float],
    scaffold_variant: str,
    include_scaffold_empty: bool,
    include_oracle: bool,
    include_scaffold_raw_precontext: bool,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for row in rows:
        y_prefix_ws, y_body = split_leading_whitespace(row["y"])
        target = target_text_for_mode(row, y_body, target_mode)
        conditions = {"scaffold_z_predictor": scaffold_prefix(row, z=row["z_B"], variant=scaffold_variant)}
        if include_scaffold_empty:
            conditions["scaffold_empty"] = scaffold_prefix(row, z="", variant=scaffold_variant)
        if include_oracle:
            conditions["scaffold_oracle_Y"] = scaffold_prefix(row, z=row["y"], variant=scaffold_variant)
        if include_scaffold_raw_precontext:
            conditions["scaffold_raw_precontext_B"] = scaffold_prefix(
                row,
                z=row["raw_precontext_budget"],
                variant=scaffold_variant,
            )
        for multiplier in bare_multipliers:
            conditions[bare_condition_name(multiplier)] = bare_prefix(row, multiplier)
        for condition, prefix in conditions.items():
            prompt = prefix + y_prefix_ws
            jobs.append(
                {
                    "condition": condition,
                    "prompt": prompt,
                    "target": target,
                    "target_mode": target_mode,
                    "y_prefix_ws_repr": repr(y_prefix_ws),
                    "dataset_row_index": row["dataset_row_index"],
                    "paper_id": row["paper_id"],
                    "equation_index": row["equation_index"],
                    "cut_id": row["cut_id"],
                    "cut_source_line": row["cut_source_line"],
                    "y_len": row["y_len"],
                    "budget_chars": row["budget_chars"],
                    # Historical schema note: this records the equation-body
                    # suffix length only. Under target_mode=body_plus_close,
                    # the literal scored target is longer by "\n" plus the
                    # display close delimiter.
                    "target_chars": len(y_body),
                    "prompt_chars": len(prompt),
                    "z_len": len(row.get("z_B", "")),
                    "z_common_prefix": row.get("common_prefix"),
                }
            )
    return jobs


def score_chunk(
    judge: OpenAICompletionLogprobJudge,
    jobs: list[dict[str, Any]],
    judge_model: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    full_prompts = [job["prompt"] + job["target"] for job in jobs]
    data = judge._completion_request(full_prompts[0] if len(full_prompts) == 1 else full_prompts)  # noqa: SLF001
    payloads = extract_prompt_logprobs_for_choices(data, expected_count=len(jobs))

    now = datetime.now(timezone.utc).isoformat()
    score_rows: list[dict[str, Any]] = []
    token_rows: list[dict[str, Any]] = []
    for job, full_prompt, payload in zip(jobs, full_prompts, payloads):
        rows = extract_target_tokens(job, full_prompt, payload)
        if not rows:
            raise RuntimeError(f"No target tokens for row={job['dataset_row_index']} condition={job['condition']}")
        score = sum(row["token_logprob"] for row in rows)
        score_rows.append(
            {
                **common_fields(job, judge_model),
                "target_tokens": len(rows),
                "body_score": score,
                "body_score_per_token": score / len(rows),
                "prompt_chars": job["prompt_chars"],
                "target_chars": job["target_chars"],
                "y_prefix_ws_repr": job["y_prefix_ws_repr"],
                "completed_utc": now,
            }
        )
        for token_row in rows:
            token_rows.append({**common_fields(job, judge_model), **token_row, "completed_utc": now})
    return score_rows, token_rows


def extract_target_tokens(
    job: dict[str, Any],
    full_prompt: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    boundary = len(job["prompt"])
    target_end = len(full_prompt)
    tokens = payload.get("tokens") or []
    token_ids = payload.get("token_ids") or [""] * len(tokens)
    token_logprobs = payload["token_logprobs"]
    offsets = normalized_text_offsets(payload, full_prompt)
    if offsets is None:
        raise RuntimeError("Judge response lacks text_offset")

    rows: list[dict[str, Any]] = []
    target_index = 0
    for full_position, (token, token_id, token_logprob, offset) in enumerate(
        zip(tokens, token_ids, token_logprobs, offsets)
    ):
        offset = int(offset)
        if boundary <= offset < target_end and token_logprob is not None:
            rows.append(
                {
                    "body_token_index": target_index,
                    "full_token_position": full_position,
                    "text_offset": offset,
                    "relative_text_offset": offset - boundary,
                    "token": token,
                    "token_id": token_id,
                    "token_logprob": float(token_logprob),
                }
            )
            target_index += 1
    return rows


def common_fields(job: dict[str, Any], judge_model: str) -> dict[str, Any]:
    return {
        "dataset_row_index": job["dataset_row_index"],
        "paper_id": job["paper_id"],
        "equation_index": job["equation_index"],
        "cut_id": job["cut_id"],
        "cut_source_line": job["cut_source_line"],
        "condition": job["condition"],
        "target_mode": job["target_mode"],
        "judge_model": judge_model,
        "y_len": job["y_len"],
        "budget_chars": job["budget_chars"],
        "z_len": job["z_len"],
        "z_common_prefix": job["z_common_prefix"],
    }


def summarize(
    score_rows: list[dict[str, Any]],
    token_rows: list[dict[str, Any]],
    baseline_condition: str,
) -> dict[str, Any]:
    by_key: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in score_rows:
        by_key[int(row["dataset_row_index"])][row["condition"]] = row
    diffs = []
    positives = 0
    for idx, conds in by_key.items():
        if "scaffold_z_predictor" not in conds or baseline_condition not in conds:
            continue
        diff = float(conds["scaffold_z_predictor"]["body_score_per_token"]) - float(conds[baseline_condition]["body_score_per_token"])
        diffs.append({"dataset_row_index": idx, "diff_per_token": diff})
        positives += int(diff > 0)

    by_condition = defaultdict(list)
    for row in score_rows:
        by_condition[row["condition"]].append(float(row["body_score_per_token"]))
    by_paper = defaultdict(list)
    for item in diffs:
        paper = by_key[item["dataset_row_index"]][baseline_condition]["paper_id"]
        by_paper[paper].append(item["diff_per_token"])

    return {
        "n_pairs": len(diffs),
        "comparison": f"scaffold_z_predictor - {baseline_condition}",
        "mean_diff_per_token": mean([d["diff_per_token"] for d in diffs]),
        "stderr_diff_per_token": stderr([d["diff_per_token"] for d in diffs]),
        "median_diff_per_token": median([d["diff_per_token"] for d in diffs]),
        "positive_count": positives,
        "positive_rate": positives / len(diffs) if diffs else None,
        "condition_means": {
            condition: {
                "n": len(values),
                "mean_score_per_token": mean(values),
                "stderr": stderr(values),
                "median": median(values),
            }
            for condition, values in sorted(by_condition.items())
        },
        "by_paper_diff": {
            paper: {
                "n": len(values),
                "mean_diff_per_token": mean(values),
                "stderr": stderr(values),
                "positive_rate": sum(v > 0 for v in values) / len(values),
            }
            for paper, values in sorted(by_paper.items())
        },
        "diffs": sorted(diffs, key=lambda x: x["dataset_row_index"]),
    }


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def stderr(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return statistics.stdev(values) / math.sqrt(len(values))


def write_prompt_previews(path: Path, jobs: list[dict[str, Any]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        preview = (
            f"dataset_row_index: {job['dataset_row_index']}\n"
            f"paper_id: {job['paper_id']}\n"
            f"equation_index: {job['equation_index']}\n"
            f"condition: {job['condition']}\n"
            f"prompt_chars: {job['prompt_chars']}\n"
            f"target_chars: {job['target_chars']}\n"
            "\n=== PROMPT ===\n"
            f"{job['prompt']}\n"
            "\n=== TARGET ===\n"
            f"{job['target']}\n"
        )
        filename = f"row{job['dataset_row_index']:04d}_{job['condition']}.txt"
        (path / filename).write_text(preview, encoding="utf-8")


def write_readme(output_dir: Path, args: argparse.Namespace, summary: dict[str, Any], elapsed: float) -> None:
    lines = [
        "# Equation-Cut Scoring: Copy Scaffold Controls",
        "",
        f"Created: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Judge: `{args.judge_model}` via `{args.base_url}`.",
        f"Elapsed seconds: {elapsed:.1f}.",
        f"Target mode: `{args.target_mode}`.",
        f"Scaffold variant: `{args.scaffold_variant}`.",
        f"Bare multipliers: `{args.bare_multipliers}`.",
        f"Headline comparison baseline: `{args.comparison_baseline}`.",
        "",
        "Target-mode definitions:",
        "",
        "- `body`: score only the held-out equation suffix `Y`.",
        "- `body_plus_close`: score `Y` plus newline and the display close delimiter, e.g. `\\end{equation*}` or `\\]`.",
        "",
        "Conditions:",
        "",
        "- `bare_B`: last `B=len(Y)+40` chars before the equation plus equation prefix.",
        "- `bare_3B`: last `3*B` chars before the equation plus equation prefix, when requested.",
        "- `scaffold_empty`: original copy scaffold with an empty first-equation suffix.",
        "- `scaffold_oracle_Y`: original copy scaffold with true `Y` in the first equation.",
        "- `scaffold_z_predictor`: original copy scaffold with GPT-5.5 generated `Z_B`, then same equation prefix.",
        "- `scaffold_raw_precontext_B`: same scaffold with the previous `B` raw pre-cut characters inserted in the Z slot, when requested.",
        "",
        "Headline:",
        "",
        f"- n pairs: {summary['n_pairs']}",
        f"- mean diff per token (`{summary['comparison']}`): {summary['mean_diff_per_token']}",
        f"- stderr: {summary['stderr_diff_per_token']}",
        f"- positive rate: {summary['positive_rate']}",
        "",
        "Files:",
        "",
        "- `equation_scores.csv`",
        "- `equation_target_token_logprobs.csv`",
        "- `summary.json`",
        "- `prompt_previews/`",
    ]
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
