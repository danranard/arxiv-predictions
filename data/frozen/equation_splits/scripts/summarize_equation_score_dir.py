"""Summarize raw and softened equation-cut logprob score differences."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any


METRICS = ["raw", "sqrt_nll", "log1p_nll", "clip2", "clip3", "clip5"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-dir", type=Path, required=True)
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=[
            "scaffold_z_predictor:bare_B",
            "scaffold_z_predictor:bare_3B",
            "bare_3B:bare_B",
            "scaffold_oracle_Y:bare_3B",
            "scaffold_empty:bare_3B",
        ],
        help="Pairs as LEFT:RIGHT, summarized as LEFT minus RIGHT.",
    )
    args = parser.parse_args()

    score_dir = args.score_dir
    token_path = score_dir / "equation_target_token_logprobs.csv"
    rows = list(csv.DictReader(token_path.open(encoding="utf-8")))
    by_key: dict[tuple[int, str], list[float]] = {}
    for row in rows:
        key = (int(row["dataset_row_index"]), row["condition"])
        by_key.setdefault(key, []).append(float(row["token_logprob"]))

    pairs = [parse_pair(pair) for pair in args.pairs]
    out: dict[str, Any] = {}
    for metric in METRICS:
        out[metric] = {}
        for left, right in pairs:
            diffs = pair_diffs(by_key, left, right, metric)
            if diffs:
                out[metric][f"{left}_minus_{right}"] = summarize(diffs)

    out_path = score_dir / "softened_summary.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


def parse_pair(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"Pair must be LEFT:RIGHT, got {text!r}")
    left, right = text.split(":", 1)
    return left, right


def pair_diffs(
    by_key: dict[tuple[int, str], list[float]],
    left: str,
    right: str,
    metric: str,
) -> list[float]:
    diffs: list[float] = []
    row_ids = sorted({idx for idx, _ in by_key})
    for idx in row_ids:
        left_lps = by_key.get((idx, left))
        right_lps = by_key.get((idx, right))
        if left_lps and right_lps:
            diffs.append(metric_score(left_lps, metric) - metric_score(right_lps, metric))
    return diffs


def metric_score(logprobs: list[float], metric: str) -> float:
    nll = [-value for value in logprobs]
    if metric == "raw":
        values = logprobs
    elif metric == "sqrt_nll":
        values = [-math.sqrt(max(0.0, value)) for value in nll]
    elif metric == "log1p_nll":
        values = [-math.log1p(max(0.0, value)) for value in nll]
    elif metric.startswith("clip"):
        cap = float(metric[4:])
        values = [-min(max(0.0, value), cap) for value in nll]
    else:
        raise ValueError(f"Unknown metric {metric!r}")
    return sum(values) / len(values)


def summarize(values: list[float]) -> dict[str, float | int | None]:
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "stderr": statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None,
        "median": statistics.median(values),
        "positive_rate": sum(value > 0 for value in values) / len(values),
    }


if __name__ == "__main__":
    main()
