from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments" / "2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0"
BAREB = ROOT / "experiments" / "2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0"
OUT = EXP / "analysis"

MODEL_ORDER = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "gpt54_nano_low",
    "gpt54_nano_medium",
    "gpt54_nano_high",
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def text_field(row: dict, names: tuple[str, ...]) -> str:
    for name in names:
        if name in row:
            return row[name]
    raise KeyError(f"none of {names} in {sorted(row)}")


def stderr(series: pd.Series) -> float:
    if len(series) <= 1:
        return float("nan")
    return float(series.std(ddof=1) / math.sqrt(len(series)))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def score_paths(window: int) -> tuple[Path, Path]:
    forecast_run = (
        "qwen3_8b_forecast_scaffold_y200_clip2resid005_nanolmh_r32_e4_v0"
        if window == 200
        else "qwen3_8b_forecast_scaffold_y1000_clip2resid005_nanolmh_r32_e2_v0"
    )
    bare_run = (
        "qwen3_8b_bareB_y200_softresid005_r32_e8_v0"
        if window == 200
        else "qwen3_8b_bareB_y1000_softresid005_r32_e8_v0"
    )
    return (
        EXP
        / "runs_remote"
        / forecast_run
        / f"best_checkpoint_eval_all_realz_y{window}_scores_full_offset"
        / "completion_scores.csv",
        BAREB
        / "runs_remote"
        / bare_run
        / f"best_checkpoint_eval_y{window}_scores_full_offset"
        / "completion_scores.csv",
    )


def audit_window(window: int) -> dict:
    forecast_rows = read_jsonl(EXP / "dataset_v1" / f"eval_all_realz_y{window}_completion.jsonl")
    bare_rows = read_jsonl(BAREB / "dataset_v1" / f"eval_y{window}_completion.jsonl")

    bare_by_key = {(str(r["paper_id"]), int(r["cut_id"])): r for r in bare_rows}
    forecast_keys = [
        (str(r["paper_id"]), int(r["cut_id"]), r["predictor_model"]) for r in forecast_rows
    ]
    bare_keys = [(str(r["paper_id"]), int(r["cut_id"])) for r in bare_rows]

    matched_by_model = {}
    missing_by_model = {}
    target_mismatches = []
    prompt_scaffold_missing = 0
    prompt_lengths = []
    target_lengths = []

    for model in MODEL_ORDER:
        rows = [r for r in forecast_rows if r.get("predictor_model") == model]
        matched = [r for r in rows if (str(r["paper_id"]), int(r["cut_id"])) in bare_by_key]
        matched_by_model[model] = len(matched)
        missing_by_model[model] = len(rows) - len(matched)

    for row in forecast_rows:
        key = (str(row["paper_id"]), int(row["cut_id"]))
        if key not in bare_by_key:
            continue
        forecast_target = text_field(row, ("target", "completion", "target_text"))
        bare_target = text_field(bare_by_key[key], ("target", "completion", "target_text"))
        if forecast_target != bare_target:
            target_mismatches.append(
                {
                    "paper_id": key[0],
                    "cut_id": key[1],
                    "predictor_model": row.get("predictor_model"),
                    "forecast_len": len(forecast_target),
                    "bare_len": len(bare_target),
                }
            )
        target_lengths.append(len(forecast_target))
        prompt = text_field(row, ("prompt", "input", "prompt_text"))
        prompt_lengths.append(len(prompt))
        if "% Notes about what's next:" not in prompt or "% Returning to the paper text:" not in prompt:
            prompt_scaffold_missing += 1

    bare_prompt_lengths = [len(text_field(row, ("prompt", "input", "prompt_text"))) for row in bare_rows]
    forecast_score_path, bare_score_path = score_paths(window)
    forecast_scores = pd.read_csv(forecast_score_path, dtype={"paper_id": str})
    bare_scores = pd.read_csv(bare_score_path, dtype={"paper_id": str})

    joined = pd.read_csv(
        OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv", dtype={"paper_id": str}
    )
    joined = joined[joined["window_chars"] == window]

    return {
        "window_chars": window,
        "forecast_rows": len(forecast_rows),
        "bare_rows": len(bare_rows),
        "forecast_predictor_counts": dict(Counter(r.get("predictor_model") for r in forecast_rows)),
        "forecast_duplicate_full_keys": len(forecast_keys) - len(set(forecast_keys)),
        "bare_duplicate_cut_keys": len(bare_keys) - len(set(bare_keys)),
        "matched_by_model": matched_by_model,
        "missing_control_by_model": missing_by_model,
        "target_mismatch_count": len(target_mismatches),
        "target_mismatch_examples": target_mismatches[:5],
        "target_lengths": {
            "min": min(target_lengths),
            "median": sorted(target_lengths)[len(target_lengths) // 2],
            "max": max(target_lengths),
        },
        "forecast_prompt_missing_scaffold_markers": prompt_scaffold_missing,
        "forecast_prompt_chars": {
            "min": min(prompt_lengths),
            "median": sorted(prompt_lengths)[len(prompt_lengths) // 2],
            "max": max(prompt_lengths),
        },
        "bare_prompt_chars": {
            "min": min(bare_prompt_lengths),
            "median": sorted(bare_prompt_lengths)[len(bare_prompt_lengths) // 2],
            "max": max(bare_prompt_lengths),
        },
        "forecast_score_rows": len(forecast_scores),
        "bare_score_rows": len(bare_scores),
        "forecast_score_target_chars": sorted(int(x) for x in forecast_scores["target_chars"].unique()),
        "bare_score_target_chars": sorted(int(x) for x in bare_scores["target_chars"].unique()),
        "forecast_boundary_modes": sorted(str(x) for x in forecast_scores["boundary_mode"].unique()),
        "bare_boundary_modes": sorted(str(x) for x in bare_scores["boundary_mode"].unique()),
        "joined_rows": len(joined),
        "joined_null_predictor_labels": int(joined["predictor_model"].isna().sum()),
        "joined_duplicate_keys": int(
            joined.duplicated(["window_chars", "predictor_model", "paper_id", "cut_id"]).sum()
        ),
        "joined_counts_by_model": joined.groupby("predictor_model").size().to_dict(),
    }


def split_audit() -> dict:
    forecast_train = read_jsonl(EXP / "dataset_v1" / "train_y200_completion.jsonl")
    forecast_eval = read_jsonl(EXP / "dataset_v1" / "eval_all_realz_y200_completion.jsonl")
    bare_train = read_jsonl(BAREB / "dataset_v1" / "train_y200_completion.jsonl")
    bare_eval = read_jsonl(BAREB / "dataset_v1" / "eval_y200_completion.jsonl")

    def papers(rows: list[dict]) -> set[str]:
        return {str(r["paper_id"]) for r in rows}

    def cuts(rows: list[dict]) -> set[tuple[str, int]]:
        return {(str(r["paper_id"]), int(r["cut_id"])) for r in rows}

    return {
        "forecast_train_rows": len(forecast_train),
        "forecast_train_papers": len(papers(forecast_train)),
        "forecast_train_cuts": len(cuts(forecast_train)),
        "forecast_eval_rows": len(forecast_eval),
        "forecast_eval_papers": len(papers(forecast_eval)),
        "forecast_eval_cuts": len(cuts(forecast_eval)),
        "forecast_train_eval_paper_overlap": sorted(papers(forecast_train) & papers(forecast_eval)),
        "forecast_train_eval_cut_overlap_count": len(cuts(forecast_train) & cuts(forecast_eval)),
        "bare_train_rows": len(bare_train),
        "bare_train_papers": len(papers(bare_train)),
        "bare_train_cuts": len(cuts(bare_train)),
        "bare_eval_rows": len(bare_eval),
        "bare_eval_papers": len(papers(bare_eval)),
        "bare_eval_cuts": len(cuts(bare_eval)),
        "bare_train_eval_paper_overlap": sorted(papers(bare_train) & papers(bare_eval)),
        "bare_train_eval_cut_overlap_count": len(cuts(bare_train) & cuts(bare_eval)),
    }


def headline_summary() -> dict:
    joined = pd.read_csv(
        OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv", dtype={"paper_id": str}
    )
    rows = {}
    for window in (200, 1000):
        window_df = joined[joined["window_chars"] == window].copy()
        window_df["family"] = window_df["predictor_model"].map(
            lambda x: "gpt55" if str(x).startswith("gpt55") else "nano"
        )
        for family, group in window_df.groupby("family"):
            rows[f"{window}_{family}"] = {
                "n": int(len(group)),
                "raw_delta_mean": float(group["delta_raw_mean_logprob"].mean()),
                "raw_delta_stderr": stderr(group["delta_raw_mean_logprob"]),
                "clip2_delta_mean": float(group["delta_clip2_mean_logprob"].mean()),
                "clip2_delta_stderr": stderr(group["delta_clip2_mean_logprob"]),
                "clip2_pct_positive": float((group["delta_clip2_mean_logprob"] > 0).mean()),
            }
    return rows


def main() -> None:
    OUT.mkdir(exist_ok=True)
    key_files = [
        OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv",
        OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_summary.csv",
        EXP / "dataset_v1" / "manifest.json",
        BAREB / "dataset_v1" / "manifest.json",
    ]
    audit = {
        "created": "2026-05-03",
        "experiment": str(EXP.relative_to(ROOT)),
        "bare_context_experiment": str(BAREB.relative_to(ROOT)),
        "split_audit": split_audit(),
        "windows": {str(window): audit_window(window) for window in (200, 1000)},
        "headline_summary": headline_summary(),
        "file_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in key_files},
    }
    out_path = OUT / "audit_summary.json"
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")

    problems = []
    for window, info in audit["windows"].items():
        if info["forecast_duplicate_full_keys"]:
            problems.append(f"window {window}: forecast duplicate full keys")
        if info["bare_duplicate_cut_keys"]:
            problems.append(f"window {window}: bare duplicate cut keys")
        if info["target_mismatch_count"]:
            problems.append(f"window {window}: target mismatches")
        if info["forecast_prompt_missing_scaffold_markers"]:
            problems.append(f"window {window}: forecast prompt missing scaffold markers")
        if info["forecast_score_target_chars"] != [int(window)]:
            problems.append(f"window {window}: bad forecast target chars")
        if info["bare_score_target_chars"] != [int(window)]:
            problems.append(f"window {window}: bad bare target chars")
        if info["forecast_boundary_modes"] != ["full_offset"] or info["bare_boundary_modes"] != [
            "full_offset"
        ]:
            problems.append(f"window {window}: non-full_offset boundary mode")
        if info["joined_null_predictor_labels"]:
            problems.append(f"window {window}: null predictor labels")
        if info["joined_duplicate_keys"]:
            problems.append(f"window {window}: duplicate joined keys")

    if audit["split_audit"]["forecast_train_eval_paper_overlap"]:
        problems.append("forecast train/eval paper overlap")
    if audit["split_audit"]["bare_train_eval_paper_overlap"]:
        problems.append("bare train/eval paper overlap")
    if audit["split_audit"]["forecast_train_eval_cut_overlap_count"]:
        problems.append("forecast train/eval cut overlap")
    if audit["split_audit"]["bare_train_eval_cut_overlap_count"]:
        problems.append("bare train/eval cut overlap")

    print(f"wrote {out_path}")
    if problems:
        print("AUDIT PROBLEMS:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("AUDIT OK")
    for key, row in audit["headline_summary"].items():
        print(
            f"{key}: clip2={row['clip2_delta_mean']:+.6f} +/- {row['clip2_delta_stderr']:.6f}; "
            f"raw={row['raw_delta_mean']:+.6f} +/- {row['raw_delta_stderr']:.6f}; n={row['n']}"
        )


if __name__ == "__main__":
    main()
