from pathlib import Path

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = (
    ROOT
    / "data/frozen/equation_splits/derived/row_lifts_clip2_raw.csv"
)

MODEL_SUMMARY_CACHE = OUT / "equation_model_lift_summary_paper_clustered.csv"
PAIRWISE_CACHE = OUT / "equation_all_pairwise_lift_comparisons_paper_clustered.csv"
MAIN_PNG = OUT / "equation_benchmark_lift_and_adjacent_paired_contrasts.png"

MODEL_ORDER = [
    "gpt55_high",
    "gpt55_medium",
    "gpt55_low",
    "gpt55_none",
    "opus47_medium",
    "opus47_low",
    "nano_high",
    "nano_medium",
    "nano_low",
]

ADJACENT_PAIR_CONTRASTS = [
    ("gpt55_high", "gpt55_medium", "GPT-5.5: (high - med)"),
    ("gpt55_medium", "gpt55_low", "GPT-5.5: (med - low)"),
    ("gpt55_low", "gpt55_none", "GPT-5.5: (low - none)"),
    ("opus47_medium", "opus47_low", "Opus 4.7: (med - low)"),
    ("nano_high", "nano_medium", "GPT-5.4 nano: (high - med)"),
    ("nano_medium", "nano_low", "GPT-5.4 nano: (med - low)"),
]

LABELS = {
    "gpt55_high": "GPT-5.5 high",
    "gpt55_medium": "GPT-5.5 med",
    "gpt55_low": "GPT-5.5 low",
    "gpt55_none": "GPT-5.5 none",
    "opus47_medium": "Opus 4.7 med",
    "opus47_low": "Opus 4.7 low",
    "nano_high": "GPT-5.4 nano high",
    "nano_medium": "GPT-5.4 nano med",
    "nano_low": "GPT-5.4 nano low",
}

COLORS = {
    "gpt55_high": "#08519c",
    "gpt55_medium": "#4292c6",
    "gpt55_low": "#9ecae1",
    "gpt55_none": "#deebf7",
    "opus47_medium": "#cb181d",
    "opus47_low": "#fb6a4a",
    "nano_high": "#238b45",
    "nano_medium": "#74c476",
    "nano_low": "#c7e9c0",
}

JUDGE_COLORS = {"Qwen": "#252525", "Kimi": "#756bb1"}


def build_caches() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = pd.read_csv(SOURCE)
    data = data[data["bundle"].isin(["old731", "new632"])].copy()

    summary_rows = []
    pair_rows = []

    for judge, judge_data in data.groupby("judge"):
        for model, group in judge_data.groupby("model_lane"):
            if model not in MODEL_ORDER:
                continue
            paper_lifts = group.groupby("paper_id", as_index=False)["lift_clip2"].mean()
            summary_rows.append(
                {
                    "judge": judge,
                    "model_lane": model,
                    "mean_lift_clip2": group["lift_clip2"].mean(),
                    "paper_equal_mean_lift_clip2": paper_lifts["lift_clip2"].mean(),
                    "se_lift_clip2_paper_clustered": paper_lifts["lift_clip2"].std(ddof=1)
                    / np.sqrt(len(paper_lifts)),
                    "n_cuts": group["super_key"].nunique(),
                    "n_papers": paper_lifts["paper_id"].nunique(),
                }
            )

        pivot = judge_data.pivot_table(
            index=["super_key", "paper_id"],
            columns="model_lane",
            values="lift_clip2",
            aggfunc="first",
        )
        for row_model in MODEL_ORDER:
            if row_model not in pivot.columns:
                continue
            for col_model in MODEL_ORDER:
                if col_model == row_model or col_model not in pivot.columns:
                    continue
                diffs = pivot[[row_model, col_model]].dropna().copy()
                diffs["diff"] = diffs[row_model] - diffs[col_model]
                paper_diffs = diffs.reset_index().groupby("paper_id", as_index=False)["diff"].mean()
                se = paper_diffs["diff"].std(ddof=1) / np.sqrt(len(paper_diffs))
                mean = diffs["diff"].mean()
                pair_rows.append(
                    {
                        "judge": judge,
                        "row_model": row_model,
                        "col_model": col_model,
                        "comparison": f"{row_model}_minus_{col_model}",
                        "mean_diff_clip2": mean,
                        "paper_equal_mean_diff_clip2": paper_diffs["diff"].mean(),
                        "se_diff_clip2_paper_clustered": se,
                        "z_score": mean / se if se > 0 else np.nan,
                        "n_cuts": len(diffs),
                        "n_papers": paper_diffs["paper_id"].nunique(),
                        "positive_rate": (diffs["diff"] > 0).mean(),
                    }
                )

    summary = pd.DataFrame(summary_rows)
    summary["model_order"] = summary["model_lane"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    summary = summary.sort_values(["judge", "model_order"])
    summary.to_csv(MODEL_SUMMARY_CACHE, index=False)

    pairwise = pd.DataFrame(pair_rows)
    pairwise.to_csv(PAIRWISE_CACHE, index=False)
    return summary, pairwise


def load_or_build(force: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    if MODEL_SUMMARY_CACHE.exists() and PAIRWISE_CACHE.exists() and not force:
        return pd.read_csv(MODEL_SUMMARY_CACHE), pd.read_csv(PAIRWISE_CACHE)
    return build_caches()


def draw_bars(ax: plt.Axes, summary: pd.DataFrame, judge: str) -> None:
    sub = summary[summary["judge"] == judge].set_index("model_lane").loc[MODEL_ORDER]
    x = np.arange(len(MODEL_ORDER))
    ax.bar(
        x,
        sub["mean_lift_clip2"],
        color=[COLORS[m] for m in MODEL_ORDER],
        width=0.78,
        alpha=0.94,
    )
    ax.errorbar(
        x,
        sub["mean_lift_clip2"],
        yerr=2 * sub["se_lift_clip2_paper_clustered"],
        fmt="none",
        ecolor="black",
        elinewidth=0.85,
        capsize=2.5,
    )
    ax.axhline(0, color="0.55", lw=1)
    judge_title = {
        "Qwen": "Smaller scorer (Qwen3-8B)",
        "Kimi": "Larger scorer (Kimi K2.6)",
    }[judge]
    ax.set_title(judge_title)
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[m] for m in MODEL_ORDER], rotation=38, ha="right")
    ax.grid(axis="y", color="0.9", linewidth=0.8)
    ax.set_axisbelow(True)


def draw_contrasts(ax: plt.Axes, pairwise: pd.DataFrame, contrasts: list[tuple[str, str, str]]) -> None:
    y_positions = np.arange(len(contrasts))[::-1]
    offsets = {"Qwen": 0.11, "Kimi": -0.11}
    markers = {"Qwen": "o", "Kimi": "s"}

    for y, (row_model, col_model, label) in zip(y_positions, contrasts):
        for judge in ["Qwen", "Kimi"]:
            row = pairwise[
                (pairwise["judge"] == judge)
                & (pairwise["row_model"] == row_model)
                & (pairwise["col_model"] == col_model)
            ].iloc[0]
            mean = row["mean_diff_clip2"]
            se = row["se_diff_clip2_paper_clustered"]
            ax.errorbar(
                mean,
                y + offsets[judge],
                xerr=2 * se,
                fmt=markers[judge],
                color=JUDGE_COLORS[judge],
                ecolor=JUDGE_COLORS[judge],
                capsize=3,
                markersize=5.5,
                label=judge if y == y_positions[0] else None,
            )

    ax.axvline(0, color="0.55", lw=1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([label for _, _, label in contrasts])
    ax.set_xlabel("Mean paired lift difference (clipLL_2/token)")
    ax.set_title("Adjacent thinking-level contrasts within each model family")
    ax.grid(axis="x", color="0.9", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=True, loc="lower right")


def plot(summary: pd.DataFrame, pairwise: pd.DataFrame, contrasts: list[tuple[str, str, str]], out_path: Path) -> None:
    fig = plt.figure(figsize=(13.5, 9.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 0.9], hspace=0.46, wspace=0.12)
    ax_qwen = fig.add_subplot(gs[0, 0])
    ax_kimi = fig.add_subplot(gs[0, 1], sharey=ax_qwen)
    ax_pair = fig.add_subplot(gs[1, :])

    draw_bars(ax_qwen, summary, "Qwen")
    draw_bars(ax_kimi, summary, "Kimi")
    ax_qwen.set_ylabel("Mean forecast lift over same-budget context control\n(clipLL_2/token)")
    plt.setp(ax_kimi.get_yticklabels(), visible=False)

    draw_contrasts(ax_pair, pairwise, contrasts)

    family_handles = [
        plt.Rectangle((0, 0), 1, 1, color=COLORS["gpt55_high"], label="GPT-5.5"),
        plt.Rectangle((0, 0), 1, 1, color=COLORS["opus47_medium"], label="Opus 4.7"),
        plt.Rectangle((0, 0), 1, 1, color=COLORS["nano_high"], label="GPT-5.4 nano"),
    ]
    ax_kimi.legend(handles=family_handles, loc="lower right", frameon=True)

    fig.suptitle(
        "Equation-suffix forecasting as a self-supervised benchmark\n"
        "Forecast lift over a same-budget recent-context control; "
        "paired contrasts compare models on the same cuts",
        y=0.985,
    )
    fig.savefig(out_path, dpi=200, bbox_inches="tight")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    summary, pairwise = load_or_build(args.force)
    plot(summary, pairwise, ADJACENT_PAIR_CONTRASTS, MAIN_PNG)


if __name__ == "__main__":
    main()
