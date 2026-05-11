# Prose continuation window-lift figure

This diagnostic figure summarizes frozen Qwen3-8B scoring for the prose/TeX
continuation setting. It is a secondary diagnostic, not part of the headline
equation-suffix benchmark.

The comparison is:

```text
forecast Z score - bare_B score
```

where `bare_B` is the same-budget recent-context control. Scores use `clip2`
logprob/token, averaged over prefix windows of the hidden continuation `Y`.
Error bars are `+/- 2` paper-clustered standard errors.

## Files

```text
all_model_window_bar_lifts_clip2_paper_clustered.csv
  Portable figure data. This is the source of the plotted bars and error bars.

all_model_window_bar_lifts_clip2_paper_clustered.png
  Rendered figure.

plot_window_lift_figure.py
  Redraws the figure from the cached CSV.
```

## Notes

The raw token-level logprob CSVs used to create the cached summary are not
bundled in this clean artifact. The cached CSV is therefore the portable data
for this diagnostic figure. The bars use scored windows of the first 50, 100,
200, and 400 Qwen-tokenized target tokens. The predictor lanes are ordered by
expected ability inside each window: GPT-5.5 high, medium, low, none, then
nano high, medium, low.

The qualitative reading is that prose/TeX continuation forecasts help most at
short horizons and the measured lift decays with scored length. GPT-5.5 lanes
are clearly above nano lanes, and nano shows a visible thinking-effort gradient.
Within GPT-5.5, the reasoning-effort ordering is not clean in this setting.
