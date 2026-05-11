from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

pd = None


KEYS = ["paper_id", "cut_id"]
METRICS = ["raw", "clip2", "clip3", "clip5"]


def main() -> None:
    args = parse_args()
    load_pandas()
    adapter = pd.read_csv(args.adapter_scores)
    token_scores = pd.read_csv(args.fireworks_token_scores)

    realz = summarize_realz_tokens(token_scores)
    joined = realz.merge(
        adapter,
        on=KEYS,
        how="inner",
        suffixes=("_realz", "_adapter"),
    )

    metrics: dict[str, Any] = {}
    split_metrics: dict[str, Any] = {}
    for lane, lane_df in joined.groupby("model_lane"):
        metrics[str(lane)] = summarize_lane(lane_df)
        split_metrics[str(lane)] = {
            str(split): summarize_lane(split_df)
            for split, split_df in lane_df.groupby("split")
        }

    out = {
        "comparison": "Fireworks real-Z scaffold_z_predictor minus HF/LoRA adapter bare_B, joined by (paper_id, cut_id)",
        "adapter_scores": str(args.adapter_scores),
        "fireworks_token_scores": str(args.fireworks_token_scores),
        "n_joined_rows": int(len(joined)),
        "metrics": metrics,
        "split_metrics": split_metrics,
    }
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    for lane in sorted(metrics):
        row = metrics[lane]["clip2"]
        raw = metrics[lane]["raw"]
        print(
            f"{lane:12s} clip2 {row['mean']:+.4f} +/- {row['stderr']:.4f} "
            f"n={row['n']} pos={row['positive_rate']:.3f} | raw {raw['mean']:+.4f}"
        )


def load_pandas() -> None:
    global pd
    try:
        import pandas as pandas_mod
    except ImportError as exc:
        raise SystemExit(
            "Missing pandas, needed for adapter-score comparison. Install "
            "`requirements_sft_gpu.txt` or `python -m pip install pandas`. "
            f"Original import error: {exc}"
        ) from exc
    pd = pandas_mod


def summarize_realz_tokens(token_scores: pd.DataFrame) -> pd.DataFrame:
    z = token_scores[token_scores["condition"].eq("scaffold_z_predictor")].copy()
    z["raw_token"] = z["token_logprob"]
    z["clip2_token"] = z["token_logprob"].clip(lower=-2.0)
    z["clip3_token"] = z["token_logprob"].clip(lower=-3.0)
    z["clip5_token"] = z["token_logprob"].clip(lower=-5.0)
    grouped = (
        z.groupby(KEYS + ["model_lane"], as_index=False)
        .agg(
            raw_realz=("raw_token", "mean"),
            clip2_realz=("clip2_token", "mean"),
            clip3_realz=("clip3_token", "mean"),
            clip5_realz=("clip5_token", "mean"),
            target_tokens_realz=("token_logprob", "size"),
        )
    )
    return grouped


def summarize_lane(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for metric in METRICS:
        realz_col = f"{metric}_realz"
        adapter_col = "raw_mean_logprob" if metric == "raw" else f"{metric}_mean_logprob"
        diff = df[realz_col] - df[adapter_col]
        out[metric] = describe(diff)
    if "target_tokens" in df.columns:
        out["target_token_diff_z_minus_adapter"] = describe(
            df["target_tokens_realz"] - df["target_tokens"]
        )
    return out


def describe(series: pd.Series) -> dict[str, Any]:
    series = series.dropna()
    n = int(series.shape[0])
    stdev = float(series.std(ddof=1)) if n > 1 else 0.0
    return {
        "n": n,
        "mean": float(series.mean()) if n else math.nan,
        "stderr": stdev / math.sqrt(n) if n else math.nan,
        "median": float(series.median()) if n else math.nan,
        "positive_rate": float((series > 0).mean()) if n else math.nan,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Fireworks real-Z scores to local/HF adapter bare-B scores.")
    parser.add_argument("--adapter-scores", type=Path, required=True)
    parser.add_argument("--fireworks-token-scores", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
