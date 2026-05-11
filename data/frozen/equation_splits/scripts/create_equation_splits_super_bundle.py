#!/usr/bin/env python3
"""Create the integrated equation-splits super bundle.

This is a thin, provenance-preserving integration layer over:

- bundles/2026-05-01_equation_splits_premier_v1
- experiments/2026-05-03_equation_cut_prevweek_strict25_all80_fulltexcmd_640_v0

It intentionally does not rewrite either source bundle. It copies the cut
universes and finalized generation lanes, folds in the May 3 nano-high repair
for the old bundle, folds in canonical Anthropic Opus 4.7 lanes staged under
diagnostics/anthropic_claude_smoke, and recomputes aggregate lift/comparison
tables.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundles" / "2026-05-03_equation_splits_super_v0"
OLD = ROOT / "bundles" / "2026-05-01_equation_splits_premier_v1"
NEW = ROOT / "experiments" / "2026-05-03_equation_cut_prevweek_strict25_all80_fulltexcmd_640_v0"
ANTHROPIC = ROOT / "diagnostics" / "anthropic_claude_smoke"

MODEL_LANES = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "nano_low",
    "nano_medium",
    "nano_high",
]

OPUS_LANES = [
    "opus47_low",
    "opus47_medium",
]

COMPARISONS = [
    ("gpt55_low", "gpt55_none"),
    ("gpt55_medium", "gpt55_none"),
    ("gpt55_high", "gpt55_none"),
    ("gpt55_medium", "gpt55_low"),
    ("gpt55_high", "gpt55_low"),
    ("gpt55_high", "gpt55_medium"),
    ("nano_medium", "nano_low"),
    ("nano_high", "nano_low"),
    ("nano_high", "nano_medium"),
    ("opus47_medium", "opus47_low"),
]

NEW_QWEN_SCORE_DIRS = {
    lane: NEW / "qwen_scores" / f"{lane}_direct_bareB_full632_v0"
    for lane in MODEL_LANES
}
NEW_KIMI_SCORE_DIRS = {
    lane: NEW / "qwen_scores" / "kimi_k2p6_current_available_v0" / f"{lane}_current_z_vs_bareB"
    for lane in MODEL_LANES
}

OLD_GEN_PATHS = {
    "gpt55_none": OLD / "generations" / "gpt55_none" / "gpt55_none_joined_stripped.jsonl",
    "gpt55_low": OLD / "generations" / "gpt55_low" / "gpt55_low_joined_stripped.jsonl",
    "gpt55_medium": OLD / "generations" / "gpt55_medium" / "gpt55_medium_joined_stripped.jsonl",
    "gpt55_high": OLD / "generations" / "gpt55_high" / "gpt55_high_joined_stripped.jsonl",
    "nano_low": OLD / "generations" / "nano_low" / "nano_low_joined_stripped.jsonl",
    "nano_medium": OLD / "generations" / "nano_medium" / "nano_medium_joined_stripped.jsonl",
    # Repaired 731-row lane, staged after the original bundle was created.
    "nano_high": OLD
    / "generations"
    / "nano_high_repair_2026-05-03"
    / "nano_high_joined_repaired731_stripped.jsonl",
}

NEW_GEN_PATHS = {
    "gpt55_none": NEW
    / "generation_runs"
    / "2026-05-03_gpt55_none_actual_paper_style_no_exact_y_prompt_match_v0"
    / "gpt55_none_joined_stripped.jsonl",
    "gpt55_low": NEW
    / "generation_runs"
    / "2026-05-03_gpt55_low_actual_paper_style_no_exact_y_prompt_match_v0"
    / "gpt55_low_joined_stripped.jsonl",
    "gpt55_medium": NEW
    / "generation_runs"
    / "2026-05-03_gpt55_medium_actual_paper_style_no_exact_y_prompt_match_with_retry9_v0"
    / "gpt55_medium_joined_stripped.jsonl",
    "gpt55_high": NEW
    / "generation_runs"
    / "2026-05-03_gpt55_high_actual_paper_style_no_exact_y_prompt_match_32k_v0"
    / "gpt55_high_joined_stripped.jsonl",
    "nano_low": NEW
    / "generation_runs"
    / "2026-05-03_gpt54nano_low_med_high_3shard_actual_paper_style_no_exact_y_v0"
    / "nano_low"
    / "nano_low_joined_stripped.jsonl",
    "nano_medium": NEW
    / "generation_runs"
    / "2026-05-03_gpt54nano_low_med_high_3shard_actual_paper_style_no_exact_y_v0"
    / "nano_medium"
    / "nano_medium_joined_with_retry5_stripped.jsonl",
    "nano_high": NEW
    / "generation_runs"
    / "2026-05-03_gpt54nano_low_med_high_3shard_actual_paper_style_no_exact_y_v0"
    / "nano_high"
    / "nano_high_joined_with_retry35_stripped.jsonl",
}

OPUS_GEN_PATHS = {
    ("old731", "opus47_medium"): ANTHROPIC
    / "2026-05-03_opus47_medium_eq_superbundle_partial_current"
    / "claude_opus47_medium_partial_joined.jsonl",
    ("old731", "opus47_low"): ANTHROPIC
    / "2026-05-03_opus47_low_eq_full731_partial_current"
    / "claude_opus47_low_partial_joined.jsonl",
    ("new632", "opus47_medium"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "claude_opus47_medium_new632_current_joined.jsonl",
    ("new632", "opus47_low"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "claude_opus47_low_new632_current_joined.jsonl",
}

OPUS_SCORE_DIRS = {
    ("old731", "Qwen", "opus47_medium"): ANTHROPIC
    / "2026-05-03_opus47_medium_eq_superbundle_partial_current"
    / "small_qwen_current_body_plus_close_zonly",
    ("old731", "Qwen", "opus47_low"): ANTHROPIC
    / "2026-05-03_opus47_low_eq_full731_partial_current"
    / "small_qwen_current_body_plus_close_zonly",
    ("old731", "Kimi", "opus47_medium"): ANTHROPIC
    / "2026-05-03_opus47_medium_eq_superbundle_partial_current"
    / "kimi_k2p6_current_body_plus_close_zonly",
    ("old731", "Kimi", "opus47_low"): ANTHROPIC
    / "2026-05-03_opus47_low_eq_full731_partial_current"
    / "kimi_k2p6_current_body_plus_close_zonly",
    ("new632", "Qwen", "opus47_medium"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "medium_new632_qwen_body_plus_close_zonly",
    ("new632", "Qwen", "opus47_low"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "low_new632_qwen_body_plus_close_zonly",
    ("new632", "Kimi", "opus47_medium"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "medium_new632_kimi_body_plus_close_zonly",
    ("new632", "Kimi", "opus47_low"): ANTHROPIC
    / "2026-05-04_opus47_second_subbundle_plan_v0"
    / "low_new632_kimi_body_plus_close_zonly",
}

JUDGE_DIR_NAMES = {
    "Qwen": "qwen3_8b",
    "Kimi": "kimi_k2p6",
}


def main() -> None:
    BUNDLE.mkdir(parents=True, exist_ok=True)
    remove_stale_files()
    manifest: dict[str, Any] = {
        "created_utc": now(),
        "script": "scripts/create_equation_splits_super_bundle.py",
        "bundle": rel(BUNDLE),
        "source_components": {
            "old731": rel(OLD),
            "new632": rel(NEW),
        },
        "judges": {
            "Qwen": "accounts/fireworks/models/qwen3-8b",
            "Kimi": "accounts/fireworks/models/kimi-k2p6",
        },
        "files": [],
    }

    cuts_old = read_jsonl(OLD / "data" / "cuts_731.jsonl")
    cuts_new_source = read_jsonl(NEW / "equation_cut_dataset.jsonl")
    exact_new = json.loads((NEW / "exact_y_prompt_match_rows.json").read_text(encoding="utf-8"))
    exact_new_keys = {row_key(r) for r in exact_new["rows"]}
    cuts_new = [r for r in cuts_new_source if row_key(r) not in exact_new_keys]

    write_jsonl(BUNDLE / "data" / "cuts_old731.jsonl", tag_rows(cuts_old, "old731"))
    write_jsonl(BUNDLE / "data" / "cuts_new632.jsonl", tag_rows(cuts_new, "new632"))
    write_jsonl(BUNDLE / "data" / "cuts_all1363.jsonl", tag_rows(cuts_old, "old731") + tag_rows(cuts_new, "new632"))
    copy_if_exists(NEW / "exact_y_prompt_match_rows.json", BUNDLE / "data" / "new632_exact_y_prompt_match_rows.json")
    copy_if_exists(OLD / "AUDIT_REPORT.json", BUNDLE / "data" / "old731_audit_report.json")
    write_paper_list(cuts_old, cuts_new)
    write_exclusions(cuts_new_source, exact_new["rows"])

    copy_generations(manifest)
    copy_score_sources(manifest)
    copy_docs_and_scripts(manifest)

    repair_dirs = {
        "Qwen": BUNDLE / "scores" / "repair_old731_nano_high_missing10" / "qwen3_8b",
        "Kimi": BUNDLE / "scores" / "repair_old731_nano_high_missing10" / "kimi_k2p6",
    }
    for judge, path in repair_dirs.items():
        if not (path / "equation_target_token_logprobs.csv").exists():
            raise FileNotFoundError(
                f"Missing repaired nano-high {judge} scores: {path}. "
                "Run scripts/score_equation_cut_generations.py on "
                "generations/nano_high_repair_2026-05-03/nano_high_missing10_repair_joined.jsonl first."
            )

    lifts = build_all_lifts(repair_dirs)
    write_csv_df(BUNDLE / "derived" / "row_lifts_clip2_raw.csv", lifts)
    model_summaries = summarize_models(lifts)
    comparisons = summarize_comparisons(lifts)
    write_csv_df(BUNDLE / "derived" / "model_summaries.csv", model_summaries)
    write_csv_df(BUNDLE / "derived" / "thinking_comparisons.csv", comparisons)
    write_csv_df(
        BUNDLE / "derived" / "thinking_comparisons_clip2_paper_clustered.csv",
        comparisons[(comparisons["metric"] == "clip2") & (comparisons["bundle"] == "combined")],
    )

    manifest["counts"] = collect_counts(cuts_old, cuts_new, lifts)
    manifest["files"] = collect_file_manifest()
    write_json(BUNDLE / "MANIFEST.json", manifest)
    write_readme(manifest, model_summaries, comparisons)
    print(json.dumps(manifest["counts"], indent=2, ensure_ascii=False))


def remove_stale_files() -> None:
    for rel_path in [
        "OPUS_INTEGRATION_PLAN_2026-05-04.md",
    ]:
        path = BUNDLE / rel_path
        if path.exists():
            path.unlink()


def build_all_lifts(repair_dirs: dict[str, Path]) -> pd.DataFrame:
    parts = [
        old_lifts(
            OLD / "scores" / "small_qwen_current_full731" / "combined_target_token_logprobs.csv",
            "Qwen",
            repair_dirs["Qwen"] / "equation_target_token_logprobs.csv",
        ),
        old_lifts(
            OLD / "scores" / "kimi_k2p6_current_full731" / "combined_target_token_logprobs.csv",
            "Kimi",
            repair_dirs["Kimi"] / "equation_target_token_logprobs.csv",
        ),
        per_lane_new_lifts(NEW_QWEN_SCORE_DIRS, "Qwen"),
        per_lane_new_lifts(NEW_KIMI_SCORE_DIRS, "Kimi"),
        opus_lifts(),
    ]
    out = pd.concat(parts, ignore_index=True)
    out["super_key"] = out["bundle"] + ":" + out["paper_id"].astype(str) + ":" + out["cut_id"].astype(str)
    return out


def old_lifts(token_csv: Path, judge: str, repair_token_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(
        token_csv,
        usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob", "model_lane"],
        dtype={"paper_id": str},
    )
    repair = pd.read_csv(
        repair_token_csv,
        usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob"],
        dtype={"paper_id": str},
    )
    repair["model_lane"] = "nano_high"

    means = token_means(df)
    repair_means = token_means(repair)
    # Existing old bundle stores bare_B once under controls, while z rows live
    # under each model lane. The repair also includes bare_B, but controls
    # already contain all 731 bare rows; only the repaired z rows are needed.
    bare = means[(means["model_lane"] == "controls") & (means["condition"] == "bare_B")]
    bare = bare.rename(columns={"clip2": "bare_clip2", "raw": "bare_raw", "n_tokens": "bare_tokens"})
    bare = bare[["dataset_row_index", "paper_id", "cut_id", "bare_clip2", "bare_raw", "bare_tokens"]]

    rows = []
    for lane in MODEL_LANES:
        z = means[(means["model_lane"] == lane) & (means["condition"] == "scaffold_z_predictor")]
        if lane == "nano_high":
            rz = repair_means[
                (repair_means["model_lane"] == "nano_high")
                & (repair_means["condition"] == "scaffold_z_predictor")
            ]
            z = pd.concat([z, rz], ignore_index=True)
            z = z.drop_duplicates(["dataset_row_index", "paper_id", "cut_id"], keep="last")
        z = z.rename(columns={"clip2": "z_clip2", "raw": "z_raw", "n_tokens": "z_tokens"})
        z = z[["dataset_row_index", "paper_id", "cut_id", "z_clip2", "z_raw", "z_tokens"]]
        merged = z.merge(bare, on=["dataset_row_index", "paper_id", "cut_id"], how="inner")
        merged["bundle"] = "old731"
        merged["judge"] = judge
        merged["model_lane"] = lane
        rows.append(finish_lift_frame(merged))
    return pd.concat(rows, ignore_index=True)


def per_lane_new_lifts(score_dirs: dict[str, Path], judge: str) -> pd.DataFrame:
    rows = []
    for lane, score_dir in score_dirs.items():
        df = pd.read_csv(
            score_dir / "equation_target_token_logprobs.csv",
            usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob"],
            dtype={"paper_id": str},
        )
        df["model_lane"] = lane
        means = token_means(df)
        wide = means.pivot_table(
            index=["dataset_row_index", "paper_id", "cut_id"],
            columns="condition",
            values=["clip2", "raw", "n_tokens"],
            aggfunc="first",
        ).reset_index()
        wide.columns = ["_".join([str(c) for c in col if c]).strip("_") for col in wide.columns.values]
        merged = pd.DataFrame(
            {
                "dataset_row_index": wide["dataset_row_index"],
                "paper_id": wide["paper_id"],
                "cut_id": wide["cut_id"],
                "z_clip2": wide["clip2_scaffold_z_predictor"],
                "bare_clip2": wide["clip2_bare_B"],
                "z_raw": wide["raw_scaffold_z_predictor"],
                "bare_raw": wide["raw_bare_B"],
                "z_tokens": wide["n_tokens_scaffold_z_predictor"],
                "bare_tokens": wide["n_tokens_bare_B"],
                "bundle": "new632",
                "judge": judge,
                "model_lane": lane,
            }
        )
        rows.append(finish_lift_frame(merged))
    return pd.concat(rows, ignore_index=True)


def opus_lifts() -> pd.DataFrame:
    rows = []
    old_bare_sources = {
        "Qwen": OLD / "scores" / "small_qwen_current_full731" / "combined_target_token_logprobs.csv",
        "Kimi": OLD / "scores" / "kimi_k2p6_current_full731" / "combined_target_token_logprobs.csv",
    }
    new_bare_sources = {
        "Qwen": NEW_QWEN_SCORE_DIRS["gpt55_none"] / "equation_target_token_logprobs.csv",
        "Kimi": NEW_KIMI_SCORE_DIRS["gpt55_none"] / "equation_target_token_logprobs.csv",
    }
    for judge in ["Qwen", "Kimi"]:
        rows.append(
            opus_lifts_for_bundle(
                "old731",
                judge,
                bare_means_from_old_controls(old_bare_sources[judge]),
            )
        )
        rows.append(
            opus_lifts_for_bundle(
                "new632",
                judge,
                bare_means_from_score_dir(new_bare_sources[judge]),
            )
        )
    return pd.concat(rows, ignore_index=True)


def opus_lifts_for_bundle(bundle_name: str, judge: str, bare: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lane in OPUS_LANES:
        score_dir = OPUS_SCORE_DIRS[(bundle_name, judge, lane)]
        z = pd.read_csv(
            score_dir / "equation_target_token_logprobs.csv",
            usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob"],
            dtype={"paper_id": str},
        )
        z["model_lane"] = lane
        z_means = token_means(z)
        z_means = z_means[z_means["condition"] == "scaffold_z_predictor"]
        z_means = z_means.rename(columns={"clip2": "z_clip2", "raw": "z_raw", "n_tokens": "z_tokens"})
        z_means = z_means[["dataset_row_index", "paper_id", "cut_id", "z_clip2", "z_raw", "z_tokens"]]
        merged = z_means.merge(bare, on=["dataset_row_index", "paper_id", "cut_id"], how="inner")
        merged["bundle"] = bundle_name
        merged["judge"] = judge
        merged["model_lane"] = lane
        rows.append(finish_lift_frame(merged))
    return pd.concat(rows, ignore_index=True)


def bare_means_from_old_controls(token_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(
        token_csv,
        usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob", "model_lane"],
        dtype={"paper_id": str},
    )
    means = token_means(df)
    bare = means[(means["model_lane"] == "controls") & (means["condition"] == "bare_B")]
    return format_bare_means(bare)


def bare_means_from_score_dir(token_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(
        token_csv,
        usecols=["dataset_row_index", "paper_id", "cut_id", "condition", "token_logprob"],
        dtype={"paper_id": str},
    )
    df["model_lane"] = "controls"
    means = token_means(df)
    bare = means[(means["model_lane"] == "controls") & (means["condition"] == "bare_B")]
    return format_bare_means(bare)


def format_bare_means(bare: pd.DataFrame) -> pd.DataFrame:
    bare = bare.rename(columns={"clip2": "bare_clip2", "raw": "bare_raw", "n_tokens": "bare_tokens"})
    return bare[["dataset_row_index", "paper_id", "cut_id", "bare_clip2", "bare_raw", "bare_tokens"]]


def token_means(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["clip2_token_logprob"] = df["token_logprob"].clip(lower=-2.0)
    return (
        df.groupby(["model_lane", "dataset_row_index", "paper_id", "cut_id", "condition"], as_index=False)
        .agg(
            raw=("token_logprob", "mean"),
            clip2=("clip2_token_logprob", "mean"),
            n_tokens=("token_logprob", "size"),
        )
    )


def finish_lift_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["lift_clip2"] = df["z_clip2"] - df["bare_clip2"]
    df["lift_raw"] = df["z_raw"] - df["bare_raw"]
    return df[
        [
            "bundle",
            "judge",
            "model_lane",
            "dataset_row_index",
            "paper_id",
            "cut_id",
            "z_clip2",
            "bare_clip2",
            "lift_clip2",
            "z_raw",
            "bare_raw",
            "lift_raw",
            "z_tokens",
            "bare_tokens",
        ]
    ]


def summarize_models(lifts: pd.DataFrame) -> pd.DataFrame:
    records = []
    for judge, metric, bundle, lane, group in iter_metric_groups(lifts):
        values = group[f"lift_{metric}"]
        records.append(
            {
                "judge": judge,
                "metric": metric,
                "bundle": bundle,
                "model_lane": lane,
                "n_cuts": len(group),
                "n_papers": group["paper_id"].nunique(),
                "mean": values.mean(),
                "se_cut": se(values),
                "se_paper_clustered": se_clustered_mean(values, group["paper_id"]),
                "se_paper_level_equal_weight": se_paper_level(values, group["paper_id"]),
                "median": values.median(),
                "pos_rate": (values > 0).mean(),
            }
        )
    return pd.DataFrame(records)


def summarize_comparisons(lifts: pd.DataFrame) -> pd.DataFrame:
    records = []
    for judge in ["Qwen", "Kimi"]:
        for metric in ["clip2", "raw"]:
            col = f"lift_{metric}"
            sub = lifts[lifts["judge"] == judge]
            for bundle in ["old731", "new632", "combined"]:
                bsub = sub if bundle == "combined" else sub[sub["bundle"] == bundle]
                for left, right in COMPARISONS:
                    left_df = bsub[bsub["model_lane"] == left][
                        ["bundle", "dataset_row_index", "paper_id", "cut_id", col]
                    ].rename(columns={col: "left"})
                    right_df = bsub[bsub["model_lane"] == right][
                        ["bundle", "dataset_row_index", "paper_id", "cut_id", col]
                    ].rename(columns={col: "right"})
                    merged = left_df.merge(
                        right_df,
                        on=["bundle", "dataset_row_index", "paper_id", "cut_id"],
                        how="inner",
                    )
                    if merged.empty:
                        continue
                    diff = merged["left"] - merged["right"]
                    records.append(
                        {
                            "judge": judge,
                            "metric": metric,
                            "bundle": bundle,
                            "comparison": f"{left}_minus_{right}",
                            "n_cuts": len(merged),
                            "n_papers": merged["paper_id"].nunique(),
                            "mean": diff.mean(),
                            "se_cut_paired": se(diff),
                            "se_paper_clustered": se_clustered_mean(diff, merged["paper_id"]),
                            "se_paper_level_equal_weight": se_paper_level(diff, merged["paper_id"]),
                            "median": diff.median(),
                            "pos_rate": (diff > 0).mean(),
                        }
                    )
    return pd.DataFrame(records)


def iter_metric_groups(lifts: pd.DataFrame):
    for judge in ["Qwen", "Kimi"]:
        for metric in ["clip2", "raw"]:
            for bundle in ["old731", "new632", "combined"]:
                sub = lifts[lifts["judge"] == judge] if bundle == "combined" else lifts[
                    (lifts["judge"] == judge) & (lifts["bundle"] == bundle)
                ]
                for lane, group in sub.groupby("model_lane"):
                    yield judge, metric, bundle, lane, group


def se(values: pd.Series) -> float:
    if len(values) < 2:
        return float("nan")
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def se_clustered_mean(values: pd.Series, clusters: pd.Series) -> float:
    values_np = values.to_numpy(dtype=float)
    clusters_np = clusters.to_numpy()
    n = len(values_np)
    labels = sorted(set(clusters_np))
    g = len(labels)
    if g < 2:
        return float("nan")
    mu = values_np.mean()
    meat = 0.0
    for label in labels:
        residual_sum = (values_np[clusters_np == label] - mu).sum()
        meat += residual_sum * residual_sum
    return math.sqrt((g / (g - 1)) * meat / (n * n))


def se_paper_level(values: pd.Series, papers: pd.Series) -> float:
    means = pd.DataFrame({"value": values, "paper": papers}).groupby("paper")["value"].mean()
    return se(means)


def copy_generations(manifest: dict[str, Any]) -> None:
    generation_records = []
    for bundle_name, paths in [("old731", OLD_GEN_PATHS), ("new632", NEW_GEN_PATHS)]:
        for lane, src in paths.items():
            dst = BUNDLE / "generations" / bundle_name / lane / src.name
            copy_if_exists(src, dst)
            generation_records.append(
                {
                    "bundle": bundle_name,
                    "model_lane": lane,
                    "source": rel(src),
                    "copied_to": rel(dst),
                    "rows": count_jsonl(dst),
                    "bytes": dst.stat().st_size,
                    "sha256": sha256(dst),
                }
            )
    for (bundle_name, lane), src in OPUS_GEN_PATHS.items():
        dst = BUNDLE / "generations" / bundle_name / lane / src.name
        copy_if_exists(src, dst)
        generation_records.append(
            {
                "bundle": bundle_name,
                "model_lane": lane,
                "source": rel(src),
                "copied_to": rel(dst),
                "rows": count_jsonl(dst),
                "bytes": dst.stat().st_size,
                "sha256": sha256(dst),
            }
        )
    manifest["generation_lanes"] = generation_records


def copy_docs_and_scripts(manifest: dict[str, Any]) -> None:
    scripts = [
        "build_equation_cut_dataset.py",
        "prepare_equation_openai_generation_batch.py",
        "manage_equation_openai_batch.py",
        "run_equation_openai_responses_async.py",
        "join_equation_openai_outputs.py",
        "strip_equation_outer_close_from_joined.py",
        "score_equation_cut_generations.py",
        "summarize_equation_score_dir.py",
        "create_equation_splits_super_bundle.py",
    ]
    for name in scripts:
        copy_if_exists(ROOT / "scripts" / name, BUNDLE / "scripts" / name)
    copy_if_exists(ANTHROPIC / "README_OPUS_CANONICAL_INPUTS.md", BUNDLE / "OPUS47_CANONICAL_INPUTS.md")
    manifest["docs_note"] = "Scripts and canonical Opus input notes are copied for provenance; source-bundle archaeology belongs outside the public artifact."


def copy_score_sources(manifest: dict[str, Any]) -> None:
    records = []
    source_files = [
        (
            "old731",
            "qwen3_8b",
            OLD / "scores" / "small_qwen_current_full731" / "combined_equation_scores.csv",
        ),
        (
            "old731",
            "qwen3_8b",
            OLD / "scores" / "small_qwen_current_full731" / "combined_target_token_logprobs.csv",
        ),
        (
            "old731",
            "qwen3_8b",
            OLD / "scores" / "small_qwen_current_full731" / "softened_model_summary.json",
        ),
        (
            "old731",
            "kimi_k2p6",
            OLD / "scores" / "kimi_k2p6_current_full731" / "combined_equation_scores.csv",
        ),
        (
            "old731",
            "kimi_k2p6",
            OLD / "scores" / "kimi_k2p6_current_full731" / "combined_target_token_logprobs.csv",
        ),
        (
            "old731",
            "kimi_k2p6",
            OLD / "scores" / "kimi_k2p6_current_full731" / "softened_model_summary.json",
        ),
    ]
    for bundle_name, judge_name, src in source_files:
        dst = BUNDLE / "scores" / "source_components" / bundle_name / judge_name / src.name
        copy_if_exists(src, dst)
        records.append({"source": rel(src), "copied_to": rel(dst), "bytes": dst.stat().st_size})

    for lane, score_dir in NEW_QWEN_SCORE_DIRS.items():
        for name in ["equation_scores.csv", "equation_target_token_logprobs.csv", "summary.json", "softened_summary.json"]:
            src = score_dir / name
            dst = BUNDLE / "scores" / "source_components" / "new632" / "qwen3_8b" / lane / name
            copy_if_exists(src, dst)
            records.append({"source": rel(src), "copied_to": rel(dst), "bytes": dst.stat().st_size})

    for lane, score_dir in NEW_KIMI_SCORE_DIRS.items():
        for name in ["equation_scores.csv", "equation_target_token_logprobs.csv", "summary.json", "softened_summary.json"]:
            src = score_dir / name
            dst = BUNDLE / "scores" / "source_components" / "new632" / "kimi_k2p6" / lane / name
            copy_if_exists(src, dst)
            records.append({"source": rel(src), "copied_to": rel(dst), "bytes": dst.stat().st_size})

    for (bundle_name, judge, lane), score_dir in OPUS_SCORE_DIRS.items():
        judge_dir = JUDGE_DIR_NAMES[judge]
        for name in ["equation_scores.csv", "equation_target_token_logprobs.csv", "summary.json", "run_plan.json", "README.md"]:
            src = score_dir / name
            dst = BUNDLE / "scores" / "source_components" / bundle_name / judge_dir / lane / name
            copy_if_exists(src, dst)
            records.append({"source": rel(src), "copied_to": rel(dst), "bytes": dst.stat().st_size})

    manifest["score_source_files"] = records


def write_paper_list(cuts_old: list[dict[str, Any]], cuts_new: list[dict[str, Any]]) -> None:
    rows = []
    for bundle_name, cuts in [("old731", cuts_old), ("new632", cuts_new)]:
        by_paper: dict[str, list[dict[str, Any]]] = {}
        for row in cuts:
            by_paper.setdefault(str(row["paper_id"]), []).append(row)
        for paper_id, paper_rows in sorted(by_paper.items()):
            first = paper_rows[0]
            rows.append(
                {
                    "bundle": bundle_name,
                    "paper_id": paper_id,
                    "n_cuts": len(paper_rows),
                    "paper_title": first.get("paper_title", ""),
                    "paper_source_path": first.get("paper_source_path", ""),
                }
            )
    write_csv_rows(BUNDLE / "data" / "paper_list.csv", rows)


def write_exclusions(cuts_new_source: list[dict[str, Any]], exact_new_rows: list[dict[str, Any]]) -> None:
    rows = []
    old_audit = json.loads((OLD / "AUDIT_REPORT.json").read_text(encoding="utf-8"))
    rows.append(
        {
            "bundle": "old731",
            "excluded_count": 9,
            "reason": "exact Y appeared in predictor prompt/source universe",
            "source_note": "See old bundle AUDIT_REPORT.json; source fresh80_740 had 740 rows and final universe has 731.",
        }
    )
    rows.append(
        {
            "bundle": "new632",
            "excluded_count": len(exact_new_rows),
            "reason": "exact Y appeared in predictor prompt/source universe",
            "source_note": f"Source had {len(cuts_new_source)} rows and final scored universe has {len(cuts_new_source) - len(exact_new_rows)}.",
        }
    )
    write_csv_rows(BUNDLE / "data" / "exclusions_exact_y.csv", rows)
    write_json(BUNDLE / "data" / "old731_exclusion_audit_pointer.json", {"audit_report": rel(OLD / "AUDIT_REPORT.json"), "loaded": bool(old_audit)})


def collect_counts(cuts_old: list[dict[str, Any]], cuts_new: list[dict[str, Any]], lifts: pd.DataFrame) -> dict[str, Any]:
    combined_papers = {str(r["paper_id"]) for r in cuts_old} | {str(r["paper_id"]) for r in cuts_new}
    return {
        "old731": {"cuts": len(cuts_old), "papers": len({str(r["paper_id"]) for r in cuts_old})},
        "new632": {"cuts": len(cuts_new), "papers": len({str(r["paper_id"]) for r in cuts_new})},
        "combined": {"cuts": len(cuts_old) + len(cuts_new), "papers": len(combined_papers)},
        "paper_overlap_old_new": len({str(r["paper_id"]) for r in cuts_old} & {str(r["paper_id"]) for r in cuts_new}),
        "row_lifts": {
            f"{judge}:{lane}": int(len(group))
            for (judge, lane), group in lifts.groupby(["judge", "model_lane"])
        },
    }


def collect_file_manifest() -> list[dict[str, Any]]:
    records = []
    for path in sorted(BUNDLE.rglob("*")):
        if path.is_file():
            records.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
    return records


def write_readme(manifest: dict[str, Any], summaries: pd.DataFrame, comparisons: pd.DataFrame) -> None:
    q = comparisons[
        (comparisons["judge"] == "Qwen")
        & (comparisons["metric"] == "clip2")
        & (comparisons["bundle"] == "combined")
    ]
    k = comparisons[
        (comparisons["judge"] == "Kimi")
        & (comparisons["metric"] == "clip2")
        & (comparisons["bundle"] == "combined")
    ]
    lines = [
        "# Equation Splits Super Bundle",
        "",
        f"Created: {manifest['created_utc']}",
        "",
        "Integrated equation-suffix continuation benchmark bundle combining the old premier 731-cut bundle with the new prev-week 632-cut reproduction.",
        "",
        "## Counts",
        "",
        f"- Old component: {manifest['counts']['old731']['cuts']} cuts from {manifest['counts']['old731']['papers']} papers.",
        f"- New component: {manifest['counts']['new632']['cuts']} cuts from {manifest['counts']['new632']['papers']} papers.",
        f"- Combined: {manifest['counts']['combined']['cuts']} cuts from {manifest['counts']['combined']['papers']} papers.",
        f"- Old/new paper overlap: {manifest['counts']['paper_overlap_old_new']}.",
        "",
        "## Primary Analysis",
        "",
        "Primary metric is Clip2: token logprobs are clipped below -2, then averaged over scored target tokens. Lifts are `scaffold_z_predictor - bare_B`. Model comparisons are paired by cut, with paper-clustered SE as the headline uncertainty.",
        "",
        "### Qwen3-8B Combined Clip2",
        "",
    ]
    lines += comparison_lines(q)
    lines += ["", "### Kimi K2P6 Combined Clip2", ""]
    lines += comparison_lines(k)
    lines += [
        "",
        "## Nano-High Repair",
        "",
        "The old component uses the repaired 731-row nano-high generation lane from `generations/nano_high_repair_2026-05-03/`. The 10 repaired rows were scored for Qwen and Kimi in this super-bundle, so nano-high comparisons now use the same 1363 combined cuts as the other lanes.",
        "",
        "## Anthropic Opus 4.7",
        "",
        "This bundle now includes `opus47_low` and `opus47_medium` predictor lanes staged from `diagnostics/anthropic_claude_smoke/`. Opus appears in the model-comparison summaries as `opus47_medium_minus_opus47_low`; it is not assumed to participate in every downstream experiment built from the original GPT/nano lanes.",
        "",
        "The two pathological medium rows were repaired with true `effort=medium`, `no_thinking=false`, `max_tokens=32768` Anthropic calls. See top-level `OPUS47_CANONICAL_INPUTS.md` for the clean-input map and canonical retry provenance.",
        "",
        "## Key Files",
        "",
        "- `data/cuts_all1363.jsonl`: tagged cut rows from both components.",
        "- `generations/old731/` and `generations/new632/`: finalized stripped generation lanes.",
        "- `scores/source_components/`: copied score CSVs/summaries from the source components.",
        "- `scores/repair_old731_nano_high_missing10/`: new Qwen/Kimi scores for the 10 repaired old-bundle nano-high rows.",
        "- `derived/row_lifts_clip2_raw.csv`: per-cut real-Z lift over `bare_B` for each judge/model lane.",
        "- `derived/thinking_comparisons.csv`: cut-paired, paper-clustered, and paper-level comparison statistics.",
        "- `MANIFEST.json`: checksums and provenance.",
        "",
        "## Stable Keys",
        "",
        "Use `bundle + paper_id + cut_id` as the stable key. `dataset_row_index` is local to each source component.",
    ]
    (BUNDLE / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def comparison_lines(df: pd.DataFrame) -> list[str]:
    out = []
    order = [f"{a}_minus_{b}" for a, b in COMPARISONS]
    by_name = {row["comparison"]: row for _, row in df.iterrows()}
    for name in order:
        if name not in by_name:
            continue
        row = by_name[name]
        out.append(
            f"- `{name}`: {row['mean']:+.5f} +/- {row['se_paper_clustered']:.5f} "
            f"(n={int(row['n_cuts'])}, papers={int(row['n_papers'])})"
        )
    return out


def tag_rows(rows: list[dict[str, Any]], bundle_name: str) -> list[dict[str, Any]]:
    tagged = []
    for row in rows:
        out = dict(row)
        out["component_bundle"] = bundle_name
        out["super_key"] = f"{bundle_name}:{row['paper_id']}:{row['cut_id']}"
        tagged.append(out)
    return tagged


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv_df(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def row_key(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["paper_id"]), int(row["cut_id"])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("/", "\\")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
