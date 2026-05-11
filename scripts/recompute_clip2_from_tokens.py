from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.headlines import JUDGES, MODEL_LANES, PAIR_ORDER
from equation_splits_repro.io_utils import read_json, write_json
from equation_splits_repro.metrics import metric_score, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute clip2 summaries from token-level logprob CSVs.")
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "frozen")
    parser.add_argument("--judge", choices=sorted(JUDGES), default="qwen3_8b")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    args = parser.parse_args()

    data_root = args.data_root if args.data_root.is_absolute() else ROOT / args.data_root
    default_out = ROOT / "outputs" / "audit" / f"clip2_recompute_{args.judge}.json"
    out_arg = args.out or default_out
    out = out_arg if out_arg.is_absolute() else ROOT / out_arg
    result = recompute_judge(data_root, args.judge, args.tolerance)
    write_json(out, result)
    if result["failures"]:
        raise SystemExit("Clip2 recompute mismatches:\n" + "\n".join(result["failures"]))
    print(f"Clip2 token recompute passed for {args.judge}.")
    print(f"Wrote audit to {out}")


def recompute_judge(data_root: Path, judge_key: str, tolerance: float) -> dict[str, Any]:
    score_dir = data_root / JUDGES[judge_key]["score_dir"]
    token_path = score_dir / "combined_target_token_logprobs.csv"
    expected = read_json(score_dir / "softened_model_summary.json")
    token_scores = load_token_scores(token_path)

    actual = {
        "metrics": {},
        "paired_model_comparisons": {"clip2": {}},
    }
    lanes = sorted({model for model, _idx, cond in token_scores if cond == "scaffold_z_predictor" and model != "controls"})
    for lane in lanes:
        ids = sorted(idx for model, idx, cond in token_scores if model == lane and cond == "scaffold_z_predictor")
        diffs = []
        for idx in ids:
            left = token_scores[(lane, idx, "scaffold_z_predictor")]
            right = token_scores.get(("controls", idx, "bare_B"))
            if right is not None:
                diffs.append(left - right)
        actual["metrics"][lane] = {"clip2": {"scaffold_z_predictor_minus_bare_B": summarize(diffs)}}

    for pair in PAIR_ORDER:
        left, right = pair.split("_minus_")
        diffs = []
        left_ids = {idx for model, idx, cond in token_scores if model == left and cond == "scaffold_z_predictor"}
        right_ids = {idx for model, idx, cond in token_scores if model == right and cond == "scaffold_z_predictor"}
        for idx in sorted(left_ids & right_ids):
            diffs.append(token_scores[(left, idx, "scaffold_z_predictor")] - token_scores[(right, idx, "scaffold_z_predictor")])
        if diffs:
            actual["paired_model_comparisons"]["clip2"][pair] = summarize(diffs)

    failures = compare_expected(actual, expected, tolerance)
    return {
        "judge": judge_key,
        "token_logprob_csv": str(token_path.relative_to(data_root)),
        "tolerance": tolerance,
        "failures": failures,
        "actual": actual,
    }


def load_token_scores(path: Path) -> dict[tuple[str, int, str], float]:
    grouped: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["model_lane"], int(row["dataset_row_index"]), row["condition"])
            grouped[key].append(float(row["token_logprob"]))
    return {key: metric_score(values, "clip2") for key, values in grouped.items()}


def compare_expected(actual: dict[str, Any], expected: dict[str, Any], tolerance: float) -> list[str]:
    failures: list[str] = []
    for lane in sorted(expected["metrics"]):
        if lane not in actual["metrics"]:
            failures.append(f"metrics.{lane}: missing from recomputed token scores")
            continue
        actual_row = actual["metrics"][lane]["clip2"]["scaffold_z_predictor_minus_bare_B"]
        expected_row = expected["metrics"][lane]["clip2"]["scaffold_z_predictor_minus_bare_B"]
        compare_row(f"metrics.{lane}.clip2.scaffold_z_predictor_minus_bare_B", actual_row, expected_row, tolerance, failures)
    for pair, actual_row in actual["paired_model_comparisons"]["clip2"].items():
        if pair not in expected["paired_model_comparisons"]["clip2"]:
            continue
        expected_row = expected["paired_model_comparisons"]["clip2"][pair]
        compare_row(f"paired.{pair}.clip2", actual_row, expected_row, tolerance, failures)
    return failures


def compare_row(path: str, actual: dict[str, Any], expected: dict[str, Any], tolerance: float, failures: list[str]) -> None:
    for key in ("n", "mean", "stderr", "median", "positive_rate"):
        if key not in actual or key not in expected:
            continue
        a = actual[key]
        e = expected[key]
        if isinstance(a, int) or isinstance(e, int):
            if a != e:
                failures.append(f"{path}.{key}: {a} != {e}")
        elif a is None or e is None:
            if a is not e:
                failures.append(f"{path}.{key}: {a} != {e}")
        elif not math.isclose(float(a), float(e), rel_tol=0.0, abs_tol=tolerance):
            failures.append(f"{path}.{key}: {a} != {e}")


if __name__ == "__main__":
    main()
