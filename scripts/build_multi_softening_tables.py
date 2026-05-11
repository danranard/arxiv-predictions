from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.headlines import PAIR_ORDER


JUDGES = ["qwen3_8b", "kimi_k2p6"]
MODEL_LANES = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "nano_low",
    "nano_medium",
    "nano_high",
    "opus47_low",
    "opus47_medium",
]
METRICS = ["raw", "clip2", "clip3", "clip5", "sqrt_nll", "log1p_nll"]


@dataclass
class RunningScores:
    n: int = 0
    raw: float = 0.0
    clip2: float = 0.0
    clip3: float = 0.0
    clip5: float = 0.0
    sqrt_nll: float = 0.0
    log1p_nll: float = 0.0

    def add(self, logprob: float) -> None:
        nll = max(0.0, -logprob)
        self.n += 1
        self.raw += logprob
        self.clip2 += -min(nll, 2.0)
        self.clip3 += -min(nll, 3.0)
        self.clip5 += -min(nll, 5.0)
        self.sqrt_nll += -math.sqrt(nll)
        self.log1p_nll += -math.log1p(nll)

    def means(self) -> dict[str, float]:
        if self.n == 0:
            raise ValueError("Cannot average an empty token group")
        return {metric: getattr(self, metric) / self.n for metric in METRICS}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build all-softening equation-suffix result tables from frozen token logprobs."
    )
    parser.add_argument(
        "--equation-root",
        type=Path,
        default=ROOT / "data" / "frozen" / "equation_splits",
    )
    args = parser.parse_args()

    equation_root = args.equation_root
    derived_dir = equation_root / "derived"
    output_dir = ROOT / "outputs" / "headlines"
    derived_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    row_lifts = build_row_lifts(equation_root)
    write_csv(
        derived_dir / "row_lifts_all_softenings.csv",
        row_lifts,
        [
            "bundle",
            "judge",
            "model_lane",
            "dataset_row_index",
            "paper_id",
            "cut_id",
            "metric",
            "z_score",
            "bare_B_score",
            "lift",
            "z_tokens",
            "bare_B_tokens",
            "super_key",
        ],
    )

    summaries = build_model_summaries(row_lifts)
    write_csv(
        derived_dir / "model_summaries_all_softenings.csv",
        summaries,
        [
            "judge",
            "metric",
            "bundle",
            "model_lane",
            "n_cuts",
            "n_papers",
            "mean",
            "se_cut",
            "se_paper_clustered",
            "median",
            "pos_rate",
        ],
    )

    comparisons = build_paired_comparisons(row_lifts)
    write_csv(
        derived_dir / "thinking_comparisons_all_softenings.csv",
        comparisons,
        [
            "judge",
            "metric",
            "bundle",
            "comparison",
            "n_cuts",
            "n_papers",
            "mean",
            "se_cut",
            "se_paper_clustered",
            "median",
            "pos_rate",
        ],
    )

    write_csv(output_dir / "multi_softening_realz_lift.csv", summaries, summaries[0].keys())
    write_csv(output_dir / "multi_softening_paired_comparisons.csv", comparisons, comparisons[0].keys())
    write_markdown(output_dir / "multi_softening_robustness.md", summaries, comparisons)
    print(f"Wrote {len(row_lifts)} row-level lift rows")
    print(f"Wrote {len(summaries)} model summary rows")
    print(f"Wrote {len(comparisons)} paired comparison rows")


def build_row_lifts(equation_root: Path) -> list[dict[str, object]]:
    score_root = equation_root / "scores"
    all_rows: list[dict[str, object]] = []
    for judge in JUDGES:
        old_groups: dict[tuple[str, int, str], tuple[dict[str, str], RunningScores]] = {}
        old_combined = score_root / "source_components" / "old731" / judge / "combined_target_token_logprobs.csv"
        load_token_file(old_combined, old_groups, default_lane=None)

        # The original old731 nano_high lane had ten missing rows. The repair
        # files are frozen in the artifact; merge them here so non-headline
        # softenings use the same full rectangle as clip2.
        repair = score_root / "repair_old731_nano_high_missing10" / judge / "equation_target_token_logprobs.csv"
        if repair.exists():
            load_token_file(repair, old_groups, default_lane="nano_high")

        for lane in ["opus47_low", "opus47_medium"]:
            path = score_root / "source_components" / "old731" / judge / lane / "equation_target_token_logprobs.csv"
            if path.exists():
                load_token_file(path, old_groups, default_lane=lane)
        all_rows.extend(groups_to_lifts(old_groups, "old731", judge))

        new_groups: dict[tuple[str, int, str], tuple[dict[str, str], RunningScores]] = {}
        for lane in MODEL_LANES:
            path = score_root / "source_components" / "new632" / judge / lane / "equation_target_token_logprobs.csv"
            if path.exists():
                load_token_file(path, new_groups, default_lane=lane)
        all_rows.extend(groups_to_lifts(new_groups, "new632", judge))
    overlay_canonical_raw_clip2(equation_root, all_rows)
    return all_rows


def load_token_file(
    path: Path,
    groups: dict[tuple[str, int, str], tuple[dict[str, str], RunningScores]],
    default_lane: str | None,
) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            condition = row["condition"]
            if condition not in {"scaffold_z_predictor", "bare_B"}:
                continue
            lane = row.get("model_lane") or default_lane
            if lane == "controls" and condition == "bare_B":
                lane = "controls"
            if lane is None:
                raise ValueError(f"Missing model lane in {path}")
            key = (lane, int(row["dataset_row_index"]), condition)
            if key not in groups:
                meta = {
                    "dataset_row_index": row["dataset_row_index"],
                    "paper_id": row["paper_id"],
                    "cut_id": row["cut_id"],
                }
                groups[key] = (meta, RunningScores())
            groups[key][1].add(float(row["token_logprob"]))


def groups_to_lifts(
    groups: dict[tuple[str, int, str], tuple[dict[str, str], RunningScores]],
    bundle: str,
    judge: str,
) -> list[dict[str, object]]:
    control_by_row: dict[int, tuple[dict[str, str], RunningScores]] = {}
    lane_control_by_row: dict[tuple[str, int], tuple[dict[str, str], RunningScores]] = {}
    z_by_lane_row: dict[tuple[str, int], tuple[dict[str, str], RunningScores]] = {}

    for (lane, row_idx, condition), value in groups.items():
        if condition == "bare_B" and lane == "controls":
            control_by_row[row_idx] = value
        elif condition == "bare_B":
            lane_control_by_row[(lane, row_idx)] = value
        elif condition == "scaffold_z_predictor":
            z_by_lane_row[(lane, row_idx)] = value

    any_control_by_row: dict[int, tuple[dict[str, str], RunningScores]] = {}
    control_items = sorted(
        lane_control_by_row.items(),
        key=lambda item: (0 if item[0][0] == "gpt55_none" else 1, item[0][0], item[0][1]),
    )
    for (lane, row_idx), value in control_items:
        any_control_by_row.setdefault(row_idx, value)

    out: list[dict[str, object]] = []
    for (lane, row_idx), (z_meta, z_scores) in sorted(z_by_lane_row.items()):
        control = lane_control_by_row.get((lane, row_idx)) or control_by_row.get(row_idx) or any_control_by_row.get(row_idx)
        if control is None:
            continue
        bare_meta, bare_scores = control
        z_means = z_scores.means()
        bare_means = bare_scores.means()
        for metric in METRICS:
            out.append(
                {
                    "bundle": bundle,
                    "judge": judge_label(judge),
                    "model_lane": lane,
                    "dataset_row_index": row_idx,
                    "paper_id": z_meta["paper_id"],
                    "cut_id": z_meta["cut_id"],
                    "metric": metric,
                    "z_score": z_means[metric],
                    "bare_B_score": bare_means[metric],
                    "lift": z_means[metric] - bare_means[metric],
                    "z_tokens": z_scores.n,
                    "bare_B_tokens": bare_scores.n,
                    "super_key": f"{bundle}:{z_meta['paper_id']}:{z_meta['cut_id']}",
                }
            )
    return out


def overlay_canonical_raw_clip2(equation_root: Path, row_lifts: list[dict[str, object]]) -> None:
    """Pin raw/clip2 rows to the already-published canonical derived file.

    Some later-added lanes, especially Opus, do not repeat the same-budget
    baseline in every source score directory. For raw and clip2 we already have
    a frozen canonical merged row-lift table. Overlaying it keeps the new
    multi-softening table exactly aligned with the existing headline artifact
    where the metrics overlap.
    """

    canonical_path = equation_root / "derived" / "row_lifts_clip2_raw.csv"
    if not canonical_path.exists():
        return
    index = {
        (row["bundle"], row["judge"], row["model_lane"], str(row["dataset_row_index"]), row["metric"]): row
        for row in row_lifts
        if row["metric"] in {"raw", "clip2"}
    }
    with canonical_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            for metric in ["raw", "clip2"]:
                key = (row["bundle"], row["judge"], row["model_lane"], row["dataset_row_index"], metric)
                target = index.get(key)
                if target is None:
                    continue
                target["z_score"] = float(row[f"z_{metric}"])
                target["bare_B_score"] = float(row[f"bare_{metric}"])
                target["lift"] = float(row[f"lift_{metric}"])
                target["z_tokens"] = int(row["z_tokens"])
                target["bare_B_tokens"] = int(row["bare_tokens"])


def build_model_summaries(row_lifts: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = ["judge", "metric", "bundle", "model_lane"]
    rows = summarize_groups(row_lifts, keys, value_col="lift")
    combined = summarize_groups(
        row_lifts,
        ["judge", "metric", "model_lane"],
        value_col="lift",
        bundle_override="combined",
    )
    return sorted(rows + combined, key=lambda r: (r["judge"], r["metric"], r["bundle"], r["model_lane"]))


def build_paired_comparisons(row_lifts: list[dict[str, object]]) -> list[dict[str, object]]:
    score_by_key: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for row in row_lifts:
        key = (
            str(row["judge"]),
            str(row["metric"]),
            str(row["bundle"]),
            str(row["model_lane"]),
            str(row["super_key"]),
        )
        score_by_key[key] = row

    by_judge_metric_bundle: set[tuple[str, str, str]] = {
        (str(row["judge"]), str(row["metric"]), str(row["bundle"])) for row in row_lifts
    }
    component_keys = list(by_judge_metric_bundle)
    by_judge_metric_bundle.update((judge, metric, "combined") for judge, metric, _ in component_keys)

    out: list[dict[str, object]] = []
    for judge, metric, bundle in sorted(by_judge_metric_bundle):
        for pair in PAIR_ORDER:
            left, right = pair.split("_minus_")
            diffs: list[dict[str, object]] = []
            left_rows = [
                row
                for row in row_lifts
                if row["judge"] == judge
                and row["metric"] == metric
                and row["model_lane"] == left
                and (bundle == "combined" or row["bundle"] == bundle)
            ]
            for left_row in left_rows:
                right_key = (
                    judge,
                    metric,
                    str(left_row["bundle"]),
                    right,
                    str(left_row["super_key"]),
                )
                right_row = score_by_key.get(right_key)
                if right_row is None:
                    continue
                diffs.append(
                    {
                        "paper_id": left_row["paper_id"],
                        "value": float(left_row["z_score"]) - float(right_row["z_score"]),
                    }
                )
            if diffs:
                out.append(summarize_values(diffs, {"judge": judge, "metric": metric, "bundle": bundle, "comparison": pair}))
    return sorted(out, key=lambda r: (r["judge"], r["metric"], r["bundle"], r["comparison"]))


def summarize_groups(
    rows: list[dict[str, object]],
    group_keys: list[str],
    value_col: str,
    bundle_override: str | None = None,
) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        key = tuple(row[k] for k in group_keys)
        grouped[key].append({"paper_id": row["paper_id"], "value": float(row[value_col])})

    out: list[dict[str, object]] = []
    for key, values in grouped.items():
        prefix = dict(zip(group_keys, key))
        if bundle_override is not None:
            prefix["bundle"] = bundle_override
        out.append(summarize_values(values, prefix))
    return out


def summarize_values(values: list[dict[str, object]], prefix: dict[str, object]) -> dict[str, object]:
    xs = [float(v["value"]) for v in values]
    paper_means: dict[str, list[float]] = defaultdict(list)
    for value in values:
        paper_means[str(value["paper_id"])].append(float(value["value"]))
    per_paper = [statistics.mean(vs) for vs in paper_means.values()]
    return {
        **prefix,
        "n_cuts": len(xs),
        "n_papers": len(per_paper),
        "mean": statistics.mean(xs),
        "se_cut": stderr(xs),
        "se_paper_clustered": stderr(per_paper),
        "median": statistics.median(xs),
        "pos_rate": sum(x > 0 for x in xs) / len(xs),
    }


def stderr(xs: Iterable[float]) -> float:
    values = list(xs)
    if len(values) < 2:
        return float("nan")
    return statistics.stdev(values) / math.sqrt(len(values))


def judge_label(judge: str) -> str:
    return {"qwen3_8b": "Qwen", "kimi_k2p6": "Kimi"}[judge]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: Iterable[str]) -> None:
    field_list = list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summaries: list[dict[str, object]], comparisons: list[dict[str, object]]) -> None:
    combined = [row for row in summaries if row["bundle"] == "combined"]
    lines = [
        "# Multi-Softening Robustness",
        "",
        "These tables are computed from frozen token-level scorer logprobs. The contrast is",
        "`scaffold_z_predictor - bare_B`, where `bare_B` is the same-budget recent-context",
        "control. Standard errors below are paper-clustered.",
        "",
        "Metrics:",
        "",
        "- `raw`: mean token logprob.",
        "- `clipK`: token logprob floored at `-K`, then averaged.",
        "- `sqrt_nll`: `-sqrt(max(-logprob, 0))` averaged over target tokens.",
        "- `log1p_nll`: `-log(1 + max(-logprob, 0))` averaged over target tokens.",
        "",
    ]
    for judge in ["Qwen", "Kimi"]:
        lines.extend([f"## {judge}: combined 1363-cut benchmark", ""])
        lines.append("| metric | model lane | n | mean lift | paper-clustered SE | positive rate |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
        for metric in METRICS:
            for lane in MODEL_LANES:
                row = next(
                    (
                        item
                        for item in combined
                        if item["judge"] == judge and item["metric"] == metric and item["model_lane"] == lane
                    ),
                    None,
                )
                if row is None:
                    continue
                lines.append(
                    f"| `{metric}` | `{lane}` | {row['n_cuts']} | {float(row['mean']):+.5f} | "
                    f"{float(row['se_paper_clustered']):.5f} | {float(row['pos_rate']):.3f} |"
                )
        lines.append("")
    lines.extend(
        [
            "## Paired thinking comparisons",
            "",
            "The full paired-comparison table for every metric is saved as",
            "`multi_softening_paired_comparisons.csv`. The headline manuscript figure uses",
            "`clip2`, but the other softened metrics preserve the same broad ordering.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
