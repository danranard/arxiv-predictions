from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
CSV = HERE / "all_model_window_bar_lifts_clip2_paper_clustered.csv"
OUT = HERE / "all_model_window_bar_lifts_clip2_paper_clustered.png"

WINDOWS = [50, 100, 200, 400]
MODEL_ORDER = [
    "gpt55_high",
    "gpt55_medium",
    "gpt55_low",
    "gpt55_none",
    "nano_high",
    "nano_medium",
    "nano_low",
]
LABELS = {
    "gpt55_high": "5.5 high",
    "gpt55_medium": "5.5 med",
    "gpt55_low": "5.5 low",
    "gpt55_none": "5.5 none",
    "nano_high": "nano high",
    "nano_medium": "nano med",
    "nano_low": "nano low",
}
COLORS = {
    "gpt55_high": "#08519c",
    "gpt55_medium": "#4292c6",
    "gpt55_low": "#9ecae1",
    "gpt55_none": "#deebf7",
    "nano_high": "#238b45",
    "nano_medium": "#74c476",
    "nano_low": "#c7e9c0",
}


def main() -> None:
    summary = pd.read_csv(CSV)

    fig, ax = plt.subplots(figsize=(12.6, 5.8))
    x = np.arange(len(WINDOWS))
    width = 0.105
    offsets = (np.arange(len(MODEL_ORDER)) - (len(MODEL_ORDER) - 1) / 2) * width

    for offset, model in zip(offsets, MODEL_ORDER):
        sub = summary[summary["model"] == model].set_index("window_tokens").loc[WINDOWS]
        ax.bar(
            x + offset,
            sub["mean_lift_clip2"],
            width=width * 0.92,
            label=LABELS[model],
            color=COLORS[model],
            alpha=0.93,
        )
        ax.errorbar(
            x + offset,
            sub["mean_lift_clip2"],
            yerr=2 * sub["se_paper_clustered"],
            fmt="none",
            ecolor="black",
            elinewidth=0.85,
            capsize=2.3,
        )

    ax.axhline(0, color="0.55", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"first {w} tokens" for w in WINDOWS])
    ax.set_ylabel("forecast Z - bare_B lift (clipLL_2/token)")
    ax.set_title(
        "Prose continuation forecast lift by scored window\n"
        "models ordered by expected ability inside each window; "
        "error bars: +/-2 paper-clustered SE"
    )
    ax.legend(ncols=4, frameon=True, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)


if __name__ == "__main__":
    main()
