from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/frozen/equation_splits/derived/row_lifts_clip2_raw.csv"

SUMMARY_CSV = OUT / "equation_lift_distribution_gpt55_high_low_none_nano_high_summary.csv"
PNG = OUT / "equation_lift_distribution_gpt55_high_low_none_nano_high_ecdf.png"

MODEL_ORDER = ["gpt55_high", "gpt55_low", "gpt55_none", "nano_high"]
LABELS = {
    "gpt55_high": "GPT-5.5 high",
    "gpt55_low": "GPT-5.5 low",
    "gpt55_none": "GPT-5.5 none",
    "nano_high": "GPT-5.4 nano high",
}
COLORS = {
    "gpt55_high": "#08519c",
    "gpt55_low": "#6baed6",
    "gpt55_none": "#9ecae1",
    "nano_high": "#238b45",
}
JUDGE_TITLES = {
    "Qwen": "Qwen3-8B scorer",
    "Kimi": "Kimi K2.6 scorer",
}


def load_data() -> pd.DataFrame:
    data = pd.read_csv(SOURCE)
    return data[
        data["bundle"].isin(["old731", "new632"])
        & data["model_lane"].isin(MODEL_ORDER)
        & data["judge"].isin(["Qwen", "Kimi"])
    ].copy()


def write_summary(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (judge, model), group in data.groupby(["judge", "model_lane"]):
        rows.append(
            {
                "judge": judge,
                "model_lane": model,
                "label": LABELS[model],
                "n": len(group),
                "mean": group["lift_clip2"].mean(),
                "median": group["lift_clip2"].median(),
                "p10": group["lift_clip2"].quantile(0.10),
                "p25": group["lift_clip2"].quantile(0.25),
                "p75": group["lift_clip2"].quantile(0.75),
                "p90": group["lift_clip2"].quantile(0.90),
                "positive_rate": (group["lift_clip2"] > 0).mean(),
            }
        )
    summary = pd.DataFrame(rows)
    summary["model_order"] = summary["model_lane"].map({m: i for i, m in enumerate(MODEL_ORDER)})
    summary = summary.sort_values(["judge", "model_order"]).drop(columns=["model_order"])
    summary.to_csv(SUMMARY_CSV, index=False)
    return summary


def ecdf(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.sort(values)
    y = np.arange(1, len(x) + 1) / len(x)
    return x, y


def plot(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.7, 4.55), sharey=True)

    for ax, judge in zip(axes, ["Qwen", "Kimi"]):
        sub = data[data["judge"] == judge]
        for model in MODEL_ORDER:
            vals = sub[sub["model_lane"] == model]["lift_clip2"].to_numpy()
            x, y = ecdf(vals)
            ax.plot(x, y, lw=2.5, color=COLORS[model], label=LABELS[model])
            ax.axvline(np.median(vals), color=COLORS[model], lw=1.05, ls="--", alpha=0.68)

        ax.axvline(0, color="0.45", lw=1)
        ax.set_xlim(-0.30, 0.65)
        ax.set_ylim(0, 1)
        ax.grid(color="0.9", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_title(JUDGE_TITLES[judge])
        ax.set_xlabel("Forecast lift over same-budget context\n(clip2 logprob per token)")

    axes[0].set_ylabel("Empirical cumulative fraction")
    axes[1].legend(loc="lower right", frameon=True)

    fig.suptitle("Per-cut forecast-lift distributions", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(PNG, dpi=200, bbox_inches="tight")


def main() -> None:
    data = load_data()
    write_summary(data)
    plot(data)


if __name__ == "__main__":
    main()
