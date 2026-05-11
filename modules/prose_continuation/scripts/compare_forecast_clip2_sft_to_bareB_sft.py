from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments" / "2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0"
BAREB = ROOT / "experiments" / "2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0"
OUT = EXP / "analysis"
OUT.mkdir(exist_ok=True)

METRICS = ["raw_mean_logprob", "clip2_mean_logprob", "clip3_mean_logprob", "clip5_mean_logprob"]
MODEL_ORDER = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "gpt54_nano_low",
    "gpt54_nano_medium",
    "gpt54_nano_high",
]


def stderr(values: pd.Series) -> float:
    values = values.dropna()
    if len(values) <= 1:
        return float("nan")
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def metadata(window: int) -> pd.DataFrame:
    rows = []
    path = EXP / "dataset_v1" / f"eval_all_realz_y{window}_completion.jsonl"
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            rows.append(
                {
                    "dataset_row_index": int(row["dataset_row_index"]),
                    "cut_id": int(row["cut_id"]),
                    "paper_id": str(row["paper_id"]),
                    "predictor_model": row["predictor_model"],
                }
            )
    return pd.DataFrame(rows)


def read_forecast_scores(window: int) -> pd.DataFrame:
    if window == 200:
        run = "qwen3_8b_forecast_scaffold_y200_clip2resid005_nanolmh_r32_e4_v0"
    elif window == 1000:
        run = "qwen3_8b_forecast_scaffold_y1000_clip2resid005_nanolmh_r32_e2_v0"
    else:
        raise ValueError(window)
    path = EXP / "runs_remote" / run / f"best_checkpoint_eval_all_realz_y{window}_scores_full_offset" / "completion_scores.csv"
    scores = pd.read_csv(path, dtype={"paper_id": str})
    return scores.merge(metadata(window), on=["dataset_row_index", "cut_id", "paper_id"], how="left")


def read_bare_control(window: int) -> pd.DataFrame:
    if window == 200:
        path = (
            BAREB
            / "runs_remote"
            / "qwen3_8b_bareB_y200_softresid005_r32_e8_v0"
            / "best_checkpoint_eval_y200_scores_full_offset"
            / "completion_scores.csv"
        )
    elif window == 1000:
        path = (
            BAREB
            / "runs_remote"
            / "qwen3_8b_bareB_y1000_softresid005_r32_e8_v0"
            / "best_checkpoint_eval_y1000_scores_full_offset"
            / "completion_scores.csv"
        )
    else:
        raise ValueError(window)
    scores = pd.read_csv(path, dtype={"paper_id": str})
    return scores


def compare_window(window: int) -> pd.DataFrame:
    forecast = read_forecast_scores(window)
    control = read_bare_control(window)
    merged = forecast.merge(control, on=["paper_id", "cut_id"], suffixes=("_forecast", "_bareB_control"), how="inner")
    merged["window_chars"] = window
    for metric in METRICS:
        merged[f"delta_{metric}"] = merged[f"{metric}_forecast"] - merged[f"{metric}_bareB_control"]
    return merged


def main() -> None:
    joined = pd.concat([compare_window(200), compare_window(1000)], ignore_index=True)
    joined.to_csv(OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv", index=False)

    rows = []
    for (window, model), group in joined.groupby(["window_chars", "predictor_model"], dropna=False):
        row = {
            "window_chars": int(window),
            "predictor_model": model,
            "n": int(len(group)),
            "n_cuts": int(group["cut_id"].nunique()),
        }
        for metric in METRICS:
            delta = group[f"delta_{metric}"]
            row[f"delta_{metric}_mean"] = float(delta.mean())
            row[f"delta_{metric}_stderr"] = stderr(delta)
            row[f"delta_{metric}_pct_positive"] = float((delta > 0).mean())
            row[f"forecast_{metric}_mean"] = float(group[f"{metric}_forecast"].mean())
            row[f"bareB_control_{metric}_mean"] = float(group[f"{metric}_bareB_control"].mean())
        rows.append(row)

    summary = pd.DataFrame(rows)
    summary["predictor_model"] = pd.Categorical(summary["predictor_model"], MODEL_ORDER, ordered=True)
    summary = summary.sort_values(["window_chars", "predictor_model"])
    summary.to_csv(OUT / "forecast_clip2_sft_vs_bareB_clip2_sft_summary.csv", index=False)

    cols = [
        "window_chars",
        "predictor_model",
        "n",
        "delta_raw_mean_logprob_mean",
        "delta_raw_mean_logprob_stderr",
        "delta_clip2_mean_logprob_mean",
        "delta_clip2_mean_logprob_stderr",
        "delta_clip2_mean_logprob_pct_positive",
    ]
    print(summary[cols].to_string(index=False))


if __name__ == "__main__":
    main()
