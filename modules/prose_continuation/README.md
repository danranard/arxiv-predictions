# Prose/TeX Continuation Module

This module packages the longer-continuation follow-up to the equation-suffix
benchmark. It uses the same notation:

```text
X: visible technical-paper context
Y: true continuation to be scored
Z: predictor forecast string
```

but the cuts are broader prose/TeX continuation cuts rather than within-equation
suffix cuts. Treat this module as a secondary, exploratory result. It is
included for reproducibility and comparison, not as part of the headline
equation-suffix benchmark.

The original bundle README is preserved as `SOURCE_BUNDLE_README.md`.

## Task and Routes

The predictor generations were built from a fresh 40-paper arXiv slate. The
canonical cut rows are:

```text
provenance/selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl
```

The main SFT follow-up compares two routes:

```text
forecast route:
  Qwen3-8B LoRA trained on forecast-scaffold examples
  training examples use nano-low/medium/high forecast Z
  objective = -clipLL_2 + 0.05 raw NLL

context route:
  Qwen3-8B LoRA trained on plain 3000-char pre-target context
  objective = -clipLL_2 + 0.05 raw NLL
```

These SFTs have different interpretations. The forecast-scaffold route is a
candidate frozen reward scorer: it is tuned on disjoint data so it understands
the intended `X + forecast Z + return-to-paper + score Y` interface, then held
fixed for evaluation. The context route is an adversarial control, not an
intended reward model. It asks whether a degenerate strategy that uses the
side-channel budget for extra previous context, plus optimized scorer-interface
interaction, can match or beat real forecasts.

The route comparison is apples-to-apples in the sense that both routes use the
same clipped SFT objective and source-disjoint train/eval split discipline. It
is not the same task as equation-suffix forecasting.

## Headline Within This Module

The cleanest reading is a three-step arc.

First, before any SFT, the unadapted Qwen3-8B scaffold scorer already detects a
short-horizon forecast signal. To avoid mixing reasoning lanes in the narrative,
use GPT-5.5 high as a representative strong predictor:

```text
Frozen Qwen3-8B scaffold scorer, GPT-5.5 high, clip2

Forecast Z - scaffold_empty
100 chars:  +0.0596 +/- .0044
200 chars:  +0.0480 +/- .0031
500 chars:  +0.0349 +/- .0018
1000 chars: +0.0253 +/- .0011

Forecast Z - bare_x_base_plus_z
100 chars:  +0.0375 +/- .0045
200 chars:  +0.0337 +/- .0032
500 chars:  +0.0217 +/- .0021
1000 chars: +0.0135 +/- .0014
```

This says the prose/TeX setting is not simply failed long-body forecasting:
forecast `Z` helps locally and beats a same-budget recent-context control, but
the measured lift decays with the scored prefix length. The summary table is
packaged in:

```text
source_scores/base_qwen_frozen_prefix_windows/
```

A compact diagnostic figure for this frozen-scorer prefix-window effect is
packaged in:

```text
diagnostics/window_lift_figure/
```

It plots `forecast Z - bare_B` under `clip2` for the first 50, 100, 200, and
400 target tokens, with `+/- 2` paper-clustered SE bars. The portable CSV in
that folder is the figure data; the raw token-level logprob files used to make
the cached summary are not bundled in this clean artifact.

Second, this untrained scaffold route loses under `clip2` to the deliberately
strong SFT-trained direct bare-context adversarial control. That comparison is
informative but not exactly fair: the control route has been explicitly trained
for the clipped continuation objective, while the scaffold route is still an
untrained scorer trying to interpret forecast notes.

Third, the scaffold-aware SFT route asks the cleaner reward-design question:
if the intended scorer is tuned on disjoint data to understand forecast notes and
then frozen, do real forecasts still beat the strong context-control route?

Forecast-scaffold clip2 SFT route minus direct bare-context clip2 SFT route:

```text
200-char target:
  GPT-5.5 aggregate: raw -0.1198 +/- .0077, clip2 +0.0270 +/- .0023
  nano aggregate:    raw -0.1584 +/- .0087, clip2 +0.0178 +/- .0025

1000-char target:
  GPT-5.5 aggregate: raw -0.2193 +/- .0035, clip2 +0.0041 +/- .0010
  nano aggregate:    raw -0.2420 +/- .0039, clip2 -0.0019 +/- .0010
```

Interpretation: under the metric these two routes were trained for, GPT-5.5
forecast notes beat the direct bare-context SFT control most clearly in the
first 200 characters. The effect is much smaller at 1000 characters. Raw
logprob is negative in this specific route comparison, which is coherent
because the SFT objective is based on `clipLL_2` with only a small raw
negative-log-likelihood residual.

Model comparison is clearer for GPT-5.5 versus nano than within GPT-5.5
reasoning-effort lanes.

## Audit Status

The local audit is saved in:

```text
analysis/audit_summary.json
```

Checks passed:

```text
train/eval paper overlap: none
train/eval cut overlap: none
join key: (paper_id, cut_id)
joined rows: 4530 = 2265 at y200 + 2265 at y1000
null predictor labels: 0
duplicate joined keys: 0
target mismatches between routes: 0
target windows: exactly 200 and 1000 chars
boundary mode: full_offset for both routes
```

The comparison is an intersection against the 325-cut direct bare-context eval
set; unmatched forecast rows are dropped.

## Contents

```text
analysis/
  forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv
  forecast_clip2_sft_vs_bareB_clip2_sft_summary.csv
  audit_summary.json
  generation_quality_summary.json
  generation_wrapper_audit.json
  generation_prompt_samples.md
  GENERATION_QA.md

scorer_inputs/
  forecast_scaffold/
  bare_context/

source_scores/
  base_qwen_frozen_prefix_windows/
  forecast_scaffold_y200_completion_scores.csv
  forecast_scaffold_y1000_completion_scores.csv
  bare_context_y200_completion_scores.csv
  bare_context_y1000_completion_scores.csv

diagnostics/
  window_lift_figure/
    all_model_window_bar_lifts_clip2_paper_clustered.csv
    all_model_window_bar_lifts_clip2_paper_clustered.png
    plot_window_lift_figure.py

provenance/
  paper_list.csv
  paper_summary.csv
  selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl
  split_manifest_seed20260427_p10000.jsonl
  split_manifest_with_cut_metadata.csv
  scripts/

scripts/
  audit_bundle_local.py
  compare_forecast_clip2_sft_to_bareB_sft.py
  audit_forecast_clip2_sft_bundle.py
  make_generation_sample_audit.py
```

## Weights

The module does not include LoRA adapter weights. They are large and are
described by checksum and source path in `WEIGHTS_AND_TRAINING.md`.

To verify the module after moving or unzipping it:

```bash
python scripts/audit_bundle_local.py
```
