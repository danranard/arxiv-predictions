# Equation Benchmark Figures

This directory contains paper-facing figures for the equation-suffix benchmark.
The figures are cached as PNGs, and the plotting scripts plus intermediate CSV
summaries are included so they can be regenerated without API calls.

## Figures

- `equation_benchmark_lift_and_adjacent_paired_contrasts.png`
  Main benchmark figure. The top row shows forecast lift over the same-budget
  recent-context control for Qwen3-8B and Kimi K2.6 scorers. The bottom row shows
  paired adjacent thinking-level contrasts within each model family.
- `equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.png`
  Control ladder for GPT-5.5 high forecasts under the Qwen3-8B scorer. It
  compares empty scaffold, same-budget context, triple-budget context, the
  source-disjoint SFT no-forecast control, GPT-5.5 forecast, and the oracle true
  suffix.
- `equation_lift_distribution_gpt55_high_low_none_nano_high_ecdf.png`
  Per-cut forecast-lift distributions for GPT-5.5 high, GPT-5.5 low,
  GPT-5.5 none, and GPT-5.4 nano high under both scorers. This checks whether
  the model-ordering effect is broad-based rather than driven by a few extreme
  examples.
- `equation_likelihood_lift_vs_reasoning_tokens.png`
  Forecast likelihood lift versus average OpenAI reasoning-token use for the
  GPT-5.5 and GPT-5.4 nano lanes under both Qwen3-8B and Kimi K2.6 scorers.
  This is a descriptive test-time-compute diagnostic: the x-axis uses an
  ordinary log scale, with zero-reasoning `None` points plotted at x=1 and not
  connected to the positive-reasoning lines.

## Reproduction

Run from the artifact root:

```bash
python diagnostics/equation_benchmark_figures/make_eq_benchmark_main_figure.py --force
python diagnostics/equation_benchmark_figures/make_eq_static_control_ladder_with_sft_heldout_qwen.py
python diagnostics/equation_benchmark_figures/make_eq_lift_distribution_figure.py
python diagnostics/equation_benchmark_figures/make_reasoning_token_lift_figure.py
```

The control-ladder script uses the included extra Qwen score files in
`qwen_old731_gpt55_high_controls_bare3B_oracle/` for the triple-budget and
oracle controls. Those scores were generated once from Fireworks/Qwen3-8B and
are frozen here to keep figure reproduction local.

The SFT bar uses the repo-facing context-only SFT control:

```text
data/frozen/scores/heldout33_softresid_no_z_control/
```

In the visible figure text it is labeled simply as the SFT no-forecast control.
The training objective and source-disjoint split are documented in
`docs/SFT_REPRODUCIBILITY.md`.
