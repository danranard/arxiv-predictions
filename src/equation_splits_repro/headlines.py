from __future__ import annotations

from pathlib import Path
from typing import Any

from .io_utils import read_csv, read_json, read_jsonl, write_csv, write_json, write_text
from .metrics import fmt


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

JUDGES = {
    "qwen3_8b": {
        "label": "Qwen3-8B frozen scorer",
        "score_dir": "scores/small_qwen_current_full731",
        "super_label": "Qwen",
    },
    "kimi_k2p6": {
        "label": "Kimi K2.6 frozen scorer",
        "score_dir": "scores/kimi_k2p6_current_full731",
        "super_label": "Kimi",
    },
}

PAIR_ORDER = [
    "gpt55_low_minus_gpt55_none",
    "gpt55_medium_minus_gpt55_none",
    "gpt55_high_minus_gpt55_none",
    "gpt55_medium_minus_gpt55_low",
    "gpt55_high_minus_gpt55_low",
    "gpt55_high_minus_gpt55_medium",
    "nano_medium_minus_nano_low",
    "nano_high_minus_nano_low",
    "nano_high_minus_nano_medium",
    "opus47_medium_minus_opus47_low",
    "gpt55_high_minus_nano_high",
    "gpt55_medium_minus_nano_high",
]


def reproduce_all(data_root: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "dataset_audit": dataset_audit(data_root, output_dir),
        "realz_lift_by_judge": realz_lift_by_judge(data_root, output_dir),
        "paired_thinking": paired_thinking(data_root, output_dir),
        "noz_sft_control": noz_sft_control(data_root, output_dir),
    }
    write_json(output_dir / "headline_report.json", report)
    write_index(output_dir, report)
    return report


def dataset_audit(data_root: Path, output_dir: Path) -> dict[str, Any]:
    equation_root = equation_super_root(data_root)
    if equation_root is not None:
        all_rows = read_jsonl(equation_root / "data" / "cuts_all1363.jsonl")
        old_rows = read_jsonl(equation_root / "data" / "cuts_old731.jsonl")
        new_rows = read_jsonl(equation_root / "data" / "cuts_new632.jsonl")
        component_counts: dict[str, int] = {}
        for row in all_rows:
            label = row.get("component_bundle", "unknown")
            component_counts[label] = component_counts.get(label, 0) + 1
        paper_ids = {row.get("paper_id") for row in all_rows}
        model_rows = [
            row
            for row in read_csv(equation_root / "derived" / "model_summaries.csv")
            if row["metric"] == "clip2" and row["bundle"] == "combined"
        ]
        generation_rows = [
            {
                "judge": row["judge"],
                "model_lane": row["model_lane"],
                "n_cuts": int(row["n_cuts"]),
                "n_papers": int(row["n_papers"]),
            }
            for row in model_rows
        ]
        write_csv(
            output_dir / "dataset_generation_audit.csv",
            generation_rows,
            ["judge", "model_lane", "n_cuts", "n_papers"],
        )
        md = [
            "# Dataset Audit",
            "",
            "Default headline universe: merged equation-suffix benchmark.",
            "",
            f"Combined rows: {len(all_rows)}",
            f"Combined papers: {len(paper_ids)}",
            f"First construction wave rows (`old731`): {len(old_rows)}",
            f"Extension wave rows (`new632`): {len(new_rows)}",
            f"Construction-wave labels in `cuts_all1363.jsonl`: {component_counts}",
            "",
            "| scorer | model lane | scored cuts | papers |",
            "| --- | --- | ---: | ---: |",
        ]
        for row in generation_rows:
            md.append(f"| {row['judge']} | {row['model_lane']} | {row['n_cuts']} | {row['n_papers']} |")
        write_text(output_dir / "dataset_audit.md", "\n".join(md) + "\n")
        return {
            "final_rows": len(all_rows),
            "papers": len(paper_ids),
            "component_rows": {"old731": len(old_rows), "new632": len(new_rows)},
            "component_labels": component_counts,
            "generation_counts": generation_rows,
        }

    audit = read_json(data_root / "AUDIT_REPORT.json")
    gen_counts = audit["generation_counts"]
    rows = []
    for lane in MODEL_LANES:
        item = gen_counts[lane]
        rows.append(
            {
                "model_lane": lane,
                "rows": item["rows"],
                "unique_paper_cut_keys": item["unique_paper_cut_keys"],
                "missing_731_keys": item["missing_731_keys"],
            }
        )
    write_csv(
        output_dir / "dataset_generation_audit.csv",
        rows,
        ["model_lane", "rows", "unique_paper_cut_keys", "missing_731_keys"],
    )
    md = [
        "# Dataset Audit",
        "",
        f"Source rows: {audit['source_rows']}",
        f"Final benchmark rows: {audit['scored_731_unique_paper_cut_keys']}",
        f"Exact-Y prompt-match rows excluded: {audit['exact_y_prompt_match_rows_in_source']}",
        "",
        "| model lane | rows | unique paper/cut keys | missing final keys |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        md.append(
            f"| {row['model_lane']} | {row['rows']} | {row['unique_paper_cut_keys']} | {row['missing_731_keys']} |"
        )
    write_text(output_dir / "dataset_audit.md", "\n".join(md) + "\n")
    return {
        "source_rows": audit["source_rows"],
        "final_rows": audit["scored_731_unique_paper_cut_keys"],
        "exact_y_excluded": audit["exact_y_prompt_match_rows_in_source"],
        "generation_counts": rows,
    }


def realz_lift_by_judge(data_root: Path, output_dir: Path) -> dict[str, Any]:
    equation_root = equation_super_root(data_root)
    if equation_root is not None:
        rows = []
        for source in read_csv(equation_root / "derived" / "model_summaries.csv"):
            if source["metric"] != "clip2" or source["bundle"] != "combined":
                continue
            judge_key = judge_key_from_super_label(source["judge"])
            rows.append(
                {
                    "judge": judge_key,
                    "label": source["model_lane"],
                    "n": int(source["n_cuts"]),
                    "mean": float(source["mean"]),
                    "stderr": float(source.get("se_paper_clustered") or source["se_cut"]),
                    "median": float(source["median"]),
                    "positive_rate": float(source["pos_rate"]),
                }
            )
        write_csv(output_dir / "realz_lift_by_judge_clip2.csv", rows, headline_fields())
        write_text(output_dir / "realz_lift_by_judge.md", lift_markdown(rows))
        return {"metric": "clip2", "contrast": "forecast_minus_context_only", "rows": rows}

    rows = []
    for judge_key, judge in JUDGES.items():
        summary = read_summary(data_root, judge_key)
        for lane in MODEL_LANES:
            item = summary["metrics"][lane]["clip2"]["scaffold_z_predictor_minus_bare_B"]
            rows.append(flat_row(judge_key, lane, item))
    write_csv(output_dir / "realz_lift_by_judge_clip2.csv", rows, headline_fields())
    write_text(output_dir / "realz_lift_by_judge.md", lift_markdown(rows))
    return {"metric": "clip2", "contrast": "forecast_minus_context_only", "rows": rows}


def paired_thinking(data_root: Path, output_dir: Path) -> dict[str, Any]:
    equation_root = equation_super_root(data_root)
    if equation_root is not None:
        rows = []
        for source in read_csv(equation_root / "derived" / "thinking_comparisons_clip2_paper_clustered.csv"):
            if source["metric"] != "clip2" or source["bundle"] != "combined":
                continue
            rows.append(
                {
                    "judge": judge_key_from_super_label(source["judge"]),
                    "label": source["comparison"],
                    "n": int(source["n_cuts"]),
                    "mean": float(source["mean"]),
                    "stderr": float(source["se_paper_clustered"]),
                    "median": float(source["median"]),
                    "positive_rate": float(source["pos_rate"]),
                }
            )
        write_csv(output_dir / "paired_thinking_comparisons_clip2.csv", rows, headline_fields())
        write_text(output_dir / "paired_thinking_comparisons.md", paired_markdown(rows))
        return {"metric": "clip2", "rows": rows, "stderr": "paper_clustered"}

    rows = []
    for judge_key, judge in JUDGES.items():
        summary = read_summary(data_root, judge_key)
        comparisons = summary["paired_model_comparisons"]["clip2"]
        for pair in PAIR_ORDER:
            if pair in comparisons:
                rows.append(flat_row(judge_key, pair, comparisons[pair]))
    write_csv(output_dir / "paired_thinking_comparisons_clip2.csv", rows, headline_fields())
    write_text(output_dir / "paired_thinking_comparisons.md", paired_markdown(rows))
    return {"metric": "clip2", "rows": rows}


def noz_sft_control(data_root: Path, output_dir: Path) -> dict[str, Any]:
    comparison_path = (
        data_root
        / "scores"
        / "heldout33_softresid_no_z_control"
        / "runs_remote"
        / "qwen3_8b_holdout33_softresid005_r32_e2_lr2e4_v0"
        / "test_realz_vs_final_adapter_full_offset_comparison"
    )
    comparison = read_json(comparison_path)
    rows = []
    for lane in ["gpt55_high", "gpt55_low", "gpt55_medium", "gpt55_none", "nano_high", "nano_medium", "nano_low"]:
        item = comparison["metrics"][lane]["clip2"]
        rows.append(flat_row("qwen3_8b_noz_sft_control", lane, item))
    write_csv(output_dir / "noz_sft_control_clip2.csv", rows, headline_fields())
    write_text(output_dir / "noz_sft_control.md", heldout_markdown(rows, comparison))
    return {"metric": "clip2", "contrast": comparison["comparison"], "rows": rows}


def read_summary(data_root: Path, judge_key: str) -> dict[str, Any]:
    return read_json(data_root / JUDGES[judge_key]["score_dir"] / "softened_model_summary.json")


def equation_super_root(data_root: Path) -> Path | None:
    path = data_root / "equation_splits"
    if (path / "data" / "cuts_all1363.jsonl").exists():
        return path
    return None


def judge_key_from_super_label(label: str) -> str:
    for key, meta in JUDGES.items():
        if meta["super_label"] == label:
            return key
    raise KeyError(f"Unknown judge label in combined equation summary: {label}")


def flat_row(judge: str, label: str, item: dict[str, Any]) -> dict[str, Any]:
    return {
        "judge": judge,
        "label": label,
        "n": item["n"],
        "mean": item["mean"],
        "stderr": item["stderr"],
        "median": item.get("median"),
        "positive_rate": item["positive_rate"],
    }


def headline_fields() -> list[str]:
    return ["judge", "label", "n", "mean", "stderr", "median", "positive_rate"]


def lift_markdown(rows: list[dict[str, Any]]) -> str:
    by_lane = {lane: {row["judge"]: row for row in rows if row["label"] == lane} for lane in MODEL_LANES}
    lines = [
        "# Forecast Lift Over Context-Only Baseline",
        "",
        "Metric: `clip2`; contrast: forecast string `Z` minus same-budget recent-context control `bare_B`.",
        "Reported SE is clustered by paper.",
        "",
        "| model lane | Qwen3-8B mean +/- paper-clustered SE | Kimi K2.6 mean +/- paper-clustered SE |",
        "| --- | ---: | ---: |",
    ]
    for lane in MODEL_LANES:
        if lane not in by_lane or "qwen3_8b" not in by_lane[lane] or "kimi_k2p6" not in by_lane[lane]:
            continue
        qwen = by_lane[lane]["qwen3_8b"]
        kimi = by_lane[lane]["kimi_k2p6"]
        lines.append(
            f"| {lane} | {fmt(qwen['mean'])} +/- {fmt(qwen['stderr'], signed=False)} | "
            f"{fmt(kimi['mean'])} +/- {fmt(kimi['stderr'], signed=False)} |"
        )
    return "\n".join(lines) + "\n"


def paired_markdown(rows: list[dict[str, Any]]) -> str:
    by_pair = {pair: {row["judge"]: row for row in rows if row["label"] == pair} for pair in PAIR_ORDER}
    lines = [
        "# Paired Thinking Comparisons",
        "",
        "Metric: `clip2`; paired by benchmark row where both model lanes are available. Reported SE is clustered by paper.",
        "",
        "| comparison | Qwen3-8B mean +/- paper-clustered SE | Kimi K2.6 mean +/- paper-clustered SE |",
        "| --- | ---: | ---: |",
    ]
    for pair in PAIR_ORDER:
        if pair not in by_pair or "qwen3_8b" not in by_pair[pair] or "kimi_k2p6" not in by_pair[pair]:
            continue
        qwen = by_pair[pair]["qwen3_8b"]
        kimi = by_pair[pair]["kimi_k2p6"]
        lines.append(
            f"| {pair} | {fmt(qwen['mean'])} +/- {fmt(qwen['stderr'], signed=False)} | "
            f"{fmt(kimi['mean'])} +/- {fmt(kimi['stderr'], signed=False)} |"
        )
    return "\n".join(lines) + "\n"


def heldout_markdown(rows: list[dict[str, Any]], comparison: dict[str, Any]) -> str:
    lines = [
        "# Context-Only SFT Control",
        "",
        "Metric: `clip2`; contrast: real forecast `Z` under the frozen Qwen3-8B score "
        "minus the context-only SFT continuation-control score. The SFT control is trained "
        "without forecast strings and evaluated on source manuscripts excluded from SFT training. "
        "The filename keeps the older `noz` label because `Z` is absent in this control.",
        "",
        f"Join: {comparison['comparison']}",
        "",
        "| model lane | n | mean +/- SE | positive rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['n']} | {fmt(row['mean'])} +/- {fmt(row['stderr'], signed=False)} | "
            f"{fmt(row['positive_rate'], signed=False)} |"
        )
    return "\n".join(lines) + "\n"


def write_index(output_dir: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Headline Reproduction Outputs",
        "",
        "Generated files:",
        "",
        "- `dataset_audit.md`",
        "- `realz_lift_by_judge.md`",
        "- `paired_thinking_comparisons.md`",
        "- `noz_sft_control.md`",
        "- `headline_report.json`",
        "",
        "These outputs are computed from frozen artifacts, without live API calls.",
    ]
    write_text(output_dir / "README.md", "\n".join(lines) + "\n")
