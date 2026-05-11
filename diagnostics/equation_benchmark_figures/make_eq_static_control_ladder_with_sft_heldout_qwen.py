from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

PACKAGED_QWEN = (
    ROOT
    / "data/frozen/equation_splits"
    / "scores/source_components/old731/qwen3_8b/combined_target_token_logprobs.csv"
)
NEW_CONTROLS = OUT / "qwen_old731_gpt55_high_controls_bare3B_oracle/equation_target_token_logprobs.csv"
SFT_HELDOUT = (
    ROOT
    / "data/frozen/scores"
    / "heldout33_softresid_no_z_control"
    / "runs_remote/qwen3_8b_holdout33_softresid005_r32_e2_lr2e4_v0"
    / "test_realz_overlap_final_adapter_full_offset/completion_scores.csv"
)

SUMMARY_CSV = OUT / "equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.csv"
PNG = OUT / "equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.png"

MODEL_LANE = "gpt55_high"
STATIC_CONDITIONS = [
    "scaffold_empty",
    "bare_B",
    "bare_3B",
    "scaffold_z_predictor",
    "scaffold_oracle_Y",
]
LADDER_ORDER = [
    "scaffold_empty",
    "bare_B",
    "bare_3B",
    "sft_no_z_heldout",
    "scaffold_z_predictor",
    "scaffold_oracle_Y",
]

LABELS = {
    "scaffold_empty": "Empty\nscaffold",
    "bare_B": "Same-budget\nrecent context",
    "bare_3B": "Triple-budget\nrecent context",
    "sft_no_z_heldout": "SFT\nno-forecast control",
    "scaffold_z_predictor": "GPT-5.5\nforecast",
    "scaffold_oracle_Y": "Oracle\ntrue suffix",
}

COLORS = {
    "scaffold_empty": "#f7fbff",
    "bare_B": "#c6dbef",
    "bare_3B": "#9ecae1",
    "sft_no_z_heldout": "#fdbf6f",
    "scaffold_z_predictor": "#08519c",
    "scaffold_oracle_Y": "#737373",
}


def key_cols() -> list[str]:
    return ["paper_id", "equation_index", "cut_id"]


def paper_clustered(values: pd.DataFrame, col: str) -> dict[str, float]:
    paper_means = values.groupby("paper_id", as_index=False)[col].mean()
    se = paper_means[col].std(ddof=1) / np.sqrt(len(paper_means))
    return {
        "mean": values[col].mean(),
        "paper_equal_mean": paper_means[col].mean(),
        "se_paper_clustered": se,
        "n_cuts": values.drop_duplicates(key_cols()).shape[0],
        "n_papers": paper_means["paper_id"].nunique(),
    }


def load_base_clip2_scores() -> pd.DataFrame:
    base = pd.read_csv(PACKAGED_QWEN)
    base = base[
        (
            (base["model_lane"] == MODEL_LANE)
            & (base["condition"] == "scaffold_z_predictor")
        )
        | (
            (base["model_lane"] == "controls")
            & (base["condition"].isin(["scaffold_empty", "bare_B"]))
        )
    ].copy()

    controls = pd.read_csv(NEW_CONTROLS)
    controls["model_lane"] = "controls"

    keep = [
        "dataset_row_index",
        "paper_id",
        "equation_index",
        "cut_id",
        "condition",
        "model_lane",
        "body_token_index",
        "token_logprob",
    ]
    data = pd.concat([base[keep], controls[keep]], ignore_index=True)
    data["clip2_logprob"] = data["token_logprob"].clip(lower=-2.0)
    return (
        data.groupby(
            ["dataset_row_index", "paper_id", "equation_index", "cut_id", "condition"],
            as_index=False,
        )
        .agg(clip2_mean_logprob=("clip2_logprob", "mean"))
    )


def load_sft_heldout_scores() -> pd.DataFrame:
    sft = pd.read_csv(SFT_HELDOUT)
    sft = sft[sft["split"] == "test"].copy()
    sft = sft.rename(columns={"clip2_mean_logprob": "sft_no_z_heldout"})
    return sft[key_cols() + ["split", "sft_no_z_heldout"]]


def build_summary() -> pd.DataFrame:
    scores = load_base_clip2_scores()
    pivot = scores.pivot_table(
        index=["dataset_row_index", "paper_id", "equation_index", "cut_id"],
        columns="condition",
        values="clip2_mean_logprob",
        aggfunc="first",
    ).reset_index()
    complete = pivot.dropna(subset=STATIC_CONDITIONS).copy()

    rows = []
    for condition in STATIC_CONDITIONS:
        complete["diff"] = complete[condition] - complete["scaffold_empty"]
        rows.append(
            {
                "panel": "ladder",
                "quantity": f"{condition}_minus_scaffold_empty",
                "condition": condition,
                "label": LABELS[condition],
                "subset_note": "731 equation cuts",
                **paper_clustered(complete, "diff"),
            }
        )

    sft = load_sft_heldout_scores()
    heldout = complete.merge(sft, on=key_cols(), how="inner")
    heldout["diff"] = heldout["sft_no_z_heldout"] - heldout["scaffold_empty"]
    rows.append(
        {
            "panel": "ladder",
            "quantity": "sft_no_z_heldout_minus_scaffold_empty",
            "condition": "sft_no_z_heldout",
            "label": LABELS["sft_no_z_heldout"],
            "subset_note": "soft-residual SFT source-disjoint test overlap only",
            **paper_clustered(heldout, "diff"),
        }
    )

    for control in ["scaffold_empty", "bare_B", "bare_3B"]:
        complete["diff"] = complete["scaffold_z_predictor"] - complete[control]
        rows.append(
            {
                "panel": "forecast_minus_control",
                "quantity": f"scaffold_z_predictor_minus_{control}",
                "condition": control,
                "label": {
                    "scaffold_empty": "Forecast minus empty scaffold",
                    "bare_B": "Forecast minus same-budget context",
                    "bare_3B": "Forecast minus triple-budget context",
                }[control],
                "subset_note": "731 equation cuts",
                **paper_clustered(complete, "diff"),
            }
        )

    heldout["diff"] = heldout["scaffold_z_predictor"] - heldout["sft_no_z_heldout"]
    rows.append(
        {
            "panel": "forecast_minus_control",
            "quantity": "scaffold_z_predictor_minus_sft_no_z_heldout",
            "condition": "sft_no_z_heldout",
            "label": "Forecast minus SFT control",
            "subset_note": "soft-residual SFT source-disjoint test overlap only",
            **paper_clustered(heldout, "diff"),
        }
    )

    complete["diff"] = complete["scaffold_oracle_Y"] - complete["scaffold_z_predictor"]
    rows.append(
        {
            "panel": "forecast_minus_control",
            "quantity": "scaffold_oracle_Y_minus_scaffold_z_predictor",
            "condition": "scaffold_oracle_Y",
            "label": "True suffix minus forecast",
            "subset_note": "731 equation cuts",
            **paper_clustered(complete, "diff"),
        }
    )

    summary = pd.DataFrame(rows)
    summary.to_csv(SUMMARY_CSV, index=False)
    return summary


def plot(summary: pd.DataFrame) -> None:
    fig, (ax_ladder, ax_diff) = plt.subplots(
        1, 2, figsize=(14.6, 5.25), gridspec_kw={"width_ratios": [1.08, 1.12]}
    )

    ladder = summary[summary["panel"] == "ladder"].set_index("condition").loc[LADDER_ORDER]
    x = np.arange(len(ladder))
    bars = ax_ladder.bar(
        x,
        ladder["mean"],
        color=[COLORS[c] for c in LADDER_ORDER],
        edgecolor="0.2",
        linewidth=0.75,
    )
    bars[LADDER_ORDER.index("sft_no_z_heldout")].set_hatch("///")
    ax_ladder.errorbar(
        x,
        ladder["mean"],
        yerr=2 * ladder["se_paper_clustered"],
        fmt="none",
        color="black",
        capsize=3,
        lw=0.85,
    )
    ax_ladder.axhline(0, color="0.55", lw=1)
    ax_ladder.set_xticks(x)
    ax_ladder.set_xticklabels(ladder["label"], rotation=30, ha="right")
    ax_ladder.set_ylabel("Lift over empty scaffold\n(clip2 logprob per token)")
    ax_ladder.set_title("Controls and oracle")
    ax_ladder.grid(axis="y", color="0.9")
    ax_ladder.set_axisbelow(True)

    diff_order = [
        "scaffold_z_predictor_minus_scaffold_empty",
        "scaffold_z_predictor_minus_bare_B",
        "scaffold_z_predictor_minus_bare_3B",
        "scaffold_z_predictor_minus_sft_no_z_heldout",
        "scaffold_oracle_Y_minus_scaffold_z_predictor",
    ]
    diffs = summary[summary["panel"] == "forecast_minus_control"].set_index("quantity").loc[diff_order]
    y = np.arange(len(diffs))[::-1]
    diff_colors = ["#08519c", "#3182bd", "#9ecae1", "#fdbf6f", "#737373"]
    diff_bars = ax_diff.barh(
        y,
        diffs["mean"],
        color=diff_colors,
        edgecolor="0.2",
        linewidth=0.75,
    )
    diff_bars[diff_order.index("scaffold_z_predictor_minus_sft_no_z_heldout")].set_hatch("///")
    ax_diff.errorbar(
        diffs["mean"],
        y,
        xerr=2 * diffs["se_paper_clustered"],
        fmt="none",
        color="black",
        capsize=3,
        lw=0.85,
    )
    ax_diff.axvline(0, color="0.55", lw=1)
    ax_diff.set_yticks(y)
    ax_diff.set_yticklabels(diffs["label"])
    ax_diff.set_xlabel("Mean paired difference\n(clip2 logprob per token)")
    ax_diff.set_title("Forecast advantages")
    ax_diff.grid(axis="x", color="0.9")
    ax_diff.set_axisbelow(True)

    fig.suptitle(
        "Equation-suffix prediction with a Qwen3-8B scorer\n"
        "Forecasts generated by GPT-5.5 high",
        y=1.0,
        fontsize=15,
    )
    fig.text(
        0.5,
        -0.02,
        "Unhatched bars use 731 equation cuts from 74 papers. "
        "The hatched SFT no-forecast control uses a source-disjoint test overlap "
        "(220 cuts from 25 papers). "
        "Error bars are ±2 paper-clustered SE.",
        ha="center",
        va="top",
        fontsize=9.5,
    )
    fig.tight_layout()
    fig.savefig(PNG, dpi=200, bbox_inches="tight")


def main() -> None:
    summary = build_summary()
    plot(summary)


if __name__ == "__main__":
    main()
