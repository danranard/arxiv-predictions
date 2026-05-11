from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


HERE = Path(__file__).resolve().parent
POINTS_CSV = HERE / "equation_reasoning_token_lift_points_by_judge.csv"

COLORS = {"GPT-5.5": "#2457a6", "GPT-5.4 nano": "#c35a2e"}
MARKERS = {"GPT-5.5": "o", "GPT-5.4 nano": "s"}
JUDGE_LINESTYLES = {"Qwen": "-", "Kimi": "--"}
JUDGE_ALPHA = {"Qwen": 1.0, "Kimi": 0.78}


def legend_label(family: str, judge: str) -> str:
    return f"{family} forecast, {judge} scorer"


def main() -> None:
    points = pd.read_csv(POINTS_CSV)
    fig, ax = plt.subplots(figsize=(8.2, 5.2))

    for judge in ["Qwen", "Kimi"]:
        sub = points[points["judge"] == judge].copy()
        sub["reasoning_tokens_for_log_plot"] = [
            max(1.0, float(x)) for x in sub["avg_reasoning_tokens"]
        ]

        for family in ["GPT-5.5", "GPT-5.4 nano"]:
            fam_all = sub[sub["model_family"] == family].sort_values("effort_order")

            fam_none = fam_all[fam_all["avg_reasoning_tokens"] == 0]
            if not fam_none.empty:
                ax.errorbar(
                    fam_none["reasoning_tokens_for_log_plot"],
                    fam_none["paper_equal_mean_lift_clip2"],
                    yerr=fam_none["se_lift_clip2_paper_clustered"],
                    color=COLORS[family],
                    marker=MARKERS[family],
                    linestyle="none",
                    alpha=JUDGE_ALPHA[judge],
                    markersize=7.0,
                    capsize=3,
                )
                if judge == "Qwen":
                    row = fam_none.iloc[0]
                    ax.annotate(
                        "None",
                        (
                            row["reasoning_tokens_for_log_plot"],
                            row["paper_equal_mean_lift_clip2"],
                        ),
                        xytext=(5, 5),
                        textcoords="offset points",
                        fontsize=8.5,
                        color=COLORS[family],
                    )

            fam_reasoning = fam_all[fam_all["avg_reasoning_tokens"] > 0]
            if not fam_reasoning.empty:
                ax.errorbar(
                    fam_reasoning["reasoning_tokens_for_log_plot"],
                    fam_reasoning["paper_equal_mean_lift_clip2"],
                    yerr=fam_reasoning["se_lift_clip2_paper_clustered"],
                    color=COLORS[family],
                    marker=MARKERS[family],
                    linestyle=JUDGE_LINESTYLES[judge],
                    alpha=JUDGE_ALPHA[judge],
                    linewidth=2.2,
                    markersize=6.5,
                    capsize=3,
                    label=legend_label(family, judge),
                )
                if judge == "Qwen":
                    for _, row in fam_reasoning.iterrows():
                        ax.annotate(
                            row["effort"],
                            (
                                row["reasoning_tokens_for_log_plot"],
                                row["paper_equal_mean_lift_clip2"],
                            ),
                            xytext=(5, 5),
                            textcoords="offset points",
                            fontsize=8.5,
                            color=COLORS[family],
                        )

    ax.set_xscale("log")
    ax.set_xlim(0.8, 6500)
    ax.set_xticks([1, 300, 1000, 3000, 6000])
    ax.set_xticklabels(["1", "300", "1k", "3k", "6k"])
    ax.set_title("Equation-suffix forecasts: likelihood lift vs. reasoning tokens")
    ax.set_xlabel("Average reasoning tokens per forecast")
    ax.set_ylabel("Likelihood lift (clipLL_2/token)")
    ax.grid(True, alpha=0.25, which="both")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.02, 0.05), fontsize=8.7)
    fig.text(
        0.5,
        -0.005,
        "Logarithmic x-axis. Zero-reasoning ('None') points are plotted at x=1.",
        ha="center",
        fontsize=9.5,
        color="#555555",
    )
    fig.tight_layout()
    fig.savefig(HERE / "equation_likelihood_lift_vs_reasoning_tokens.png", dpi=220, bbox_inches="tight")
    fig.savefig(HERE / "equation_likelihood_lift_vs_reasoning_tokens.pdf", bbox_inches="tight")
    print("Wrote equation_likelihood_lift_vs_reasoning_tokens.[png,pdf]")


if __name__ == "__main__":
    main()
