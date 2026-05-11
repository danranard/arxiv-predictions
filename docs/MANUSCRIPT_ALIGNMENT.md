# Manuscript Alignment

This note maps the main manuscript-facing claims to the companion artifact
files. It is intentionally higher-level than `docs/ARTIFACTS.md`: start here
when checking which bundled object supports which paper result.

## Main Equation-Suffix Benchmark

Headline claim: on 1363 equation-suffix cuts from 138 recent arXiv manuscripts,
forecast strings from GPT-5.5, Opus 4.7, and GPT-5.4 nano improve clipped
likelihood over the same-budget recent-context control under both Qwen3-8B and
Kimi K2.6 scorers.

Primary files:

```text
data/frozen/equation_splits/data/cuts_all1363.jsonl
data/frozen/equation_splits/derived/model_summaries.csv
data/frozen/equation_splits/derived/row_lifts_clip2_raw.csv
outputs/headlines/realz_lift_by_judge.md
```

Paper-facing figure and cached data:

```text
diagnostics/equation_benchmark_figures/
  equation_benchmark_lift_and_adjacent_paired_contrasts.png
  equation_model_lift_summary_paper_clustered.csv
  equation_all_pairwise_lift_comparisons_paper_clustered.csv
```

## Reasoning-Effort Comparisons

Headline claim: provider-defined reasoning-effort settings are distinguishable
in the equation-suffix benchmark, most clearly for none/low/high contrasts and
for GPT-5.4 nano high versus low.

Primary files:

```text
data/frozen/equation_splits/derived/thinking_comparisons_clip2_paper_clustered.csv
outputs/headlines/paired_thinking_comparisons.md
```

Reasoning-token usage diagnostics:

```text
diagnostics/equation_benchmark_figures/
  equation_likelihood_lift_vs_reasoning_tokens.png
  equation_reasoning_token_summary_by_lane.csv
  equation_reasoning_token_lift_points_by_judge.csv
data/frozen/equation_splits/derived/
  opus47_usage_anthropic_token_estimates.csv
  opus47_usage_anthropic_token_estimates_summary.json
```

OpenAI and Anthropic token counts use different tokenizers and should be read
as within-provider diagnostics, not directly calibrated compute units.

## Scoring Softness

Headline claim: the main ordering is robust across several deterministic
softenings of the same frozen token-level logprobs; `clip2` is the headline
metric because it limits catastrophic local mismatches while retaining useful
token-level signal.

Primary files:

```text
data/frozen/equation_splits/derived/model_summaries_all_softenings.csv
data/frozen/equation_splits/derived/row_lifts_all_softenings.csv
data/frozen/equation_splits/derived/thinking_comparisons_all_softenings.csv
outputs/headlines/multi_softening_robustness.md
```

Mechanism probe:

```text
diagnostics/toy_equation_order_probe/
```

## Shortcut Controls

Headline claim: GPT-5.5 forecasts survive a deliberately strong context-only
SFT control on source-disjoint held-out papers, while GPT-5.4 nano forecasts do
not.

Primary files:

```text
docs/SFT_REPRODUCIBILITY.md
data/frozen/scores/heldout33_softresid_no_z_control/
outputs/headlines/noz_sft_control.md
```

Paper-facing control figure:

```text
diagnostics/equation_benchmark_figures/
  equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.png
  equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.csv
```

The path label `no_z` is retained for reproducibility, but the manuscript
terminology is "context-only SFT control."

## Examples

Expanded prompt examples and random equation-forecast examples:

```text
docs/prompt_snapshots/
examples/random_equation_forecast_appendix/
```

The random-example appendix is intended for qualitative inspection; it is not
part of the scoring calculation.

## Prose/TeX Continuation Follow-Up

Headline claim: longer mixed prose/TeX continuations show positive but noisier
forecast lift, concentrated near the beginning of the target.

Primary module:

```text
modules/prose_continuation/
```

Key files:

```text
modules/prose_continuation/README.md
modules/prose_continuation/source_scores/base_qwen_frozen_prefix_windows/
modules/prose_continuation/diagnostics/window_lift_figure/
  all_model_window_bar_lifts_clip2_paper_clustered.png
  all_model_window_bar_lifts_clip2_paper_clustered.csv
```

The prose/TeX module is a secondary exploratory result, not the main
equation-suffix benchmark.
