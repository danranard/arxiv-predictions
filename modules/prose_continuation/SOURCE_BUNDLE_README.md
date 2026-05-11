# Prose/TeX Continuation SFT Route Bundle

Created: 2026-05-03.

This bundle records the prose/TeX continuation route-wise SFT comparison:

```text
forecast route:
  Qwen3-8B LoRA trained on forecast-scaffold examples
  training examples use nano-low/medium/high forecast Z
  objective = -clipLL_2 + 0.05 raw NLL

context route:
  Qwen3-8B LoRA trained on plain 3000-char pre-target context
  objective = -clipLL_2 + 0.05 raw NLL
```

It is the symmetric clipped-objective follow-up to the earlier direct
`bare_B` prose stress test. The earlier test gave clip2-style SFT only to the
direct bare-context route; this one gives the forecast-scaffold route the same
kind of SFT and then compares the two routes.

## Headline

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
forecast notes beat the direct bare-context SFT control, especially for the
200-character window. Raw logprob is negative in this specific comparison,
which is coherent because the SFT objective is based on `clipLL_2` with only a
small raw negative-log-likelihood residual.

Model comparison is weaker than the route/control result. GPT-5.5 beats nano
clearly; ordering within GPT-5.5 is tiny/noisy.

## Audit Status

The saved audit is:

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

This is an intersection comparison against the 325-cut direct bare-context eval
set. Unmatched forecast rows are dropped.

## Generation Audit

The actual forecast scaffold inputs are included under:

```text
scorer_inputs/forecast_scaffold/
```

The human-readable sample audit is:

```text
analysis/generation_prompt_samples.md
analysis/GENERATION_QA.md
```

The automated wrapper scan found no obvious preambles/wrappers like "here is
my prediction", "to continue", or "best guess". All extracted `Z` strings were
nonempty and about 1000 chars as intended.

There were a few target-prefix hits where the first 40 or 120 chars of `Y`
appeared inside `Z`; the four 120-char hits were hand-read and look like
ordinary local near-forecasts or repeated TeX structure, not prompt leakage.

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
    train_y200_completion.jsonl
    train_y1000_completion.jsonl
    eval_all_realz_y200_completion.jsonl
    eval_all_realz_y1000_completion.jsonl
  bare_context/
    train_y200_completion.jsonl
    train_y1000_completion.jsonl
    eval_y200_completion.jsonl
    eval_y1000_completion.jsonl

source_scores/
  forecast_scaffold_y200_completion_scores.csv
  forecast_scaffold_y1000_completion_scores.csv
  bare_context_y200_completion_scores.csv
  bare_context_y1000_completion_scores.csv

dataset_v1/
  forecast_manifest.json
  bare_context_control_manifest.json
  SOURCE_README.md

provenance/
  paper_list.csv
  paper_summary.csv
  split_manifest_seed20260427_p10000.jsonl
  split_manifest_with_cut_metadata.csv
  selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl
  scripts/
  README.md
  SHA256SUMS.txt

scripts/
  audit_bundle_local.py
  compare_forecast_clip2_sft_to_bareB_sft.py
  audit_forecast_clip2_sft_bundle.py
  make_generation_sample_audit.py

MANIFEST.json
WEIGHTS_AND_TRAINING.md

docs/
  PROSE_CONTINUATION_SFT_RESULTS.md
```

The bundle does not include the selected LoRA adapter weights. They are large;
the internal staging labels for the adapter archives were:

```text
experiments/2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0/
  h100_forecast_scaffold_clip2_selected_adapters.tgz

experiments/2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0/
  h100_bareB_prose_selected_adapters.tgz
```

Exact adapter archive sizes, checksums, and training details are recorded in:

```text
WEIGHTS_AND_TRAINING.md
```

Construction-time H100 handoff notes were moved out of the public artifact and
archived in the wrapper-level `meta_notes/` folder.

## Internal Staging Labels

```text
forecast SFT:
experiments/2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0/

direct bare-context SFT:
experiments/2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0/
```

The focused writeup is:

```text
PROSE_CONTINUATION_SFT_RESULTS.md
```

To verify the bundle after moving/unzipping it:

```text
python scripts/audit_bundle_local.py
```

The provenance directory makes the bundle self-contained for the paper slate
and selected cut text used by this analysis. It includes the 40-paper arXiv
list, the fixed 661-cut shuffled split manifest, the canonical 10k predictor-X
/ 4k judge-X / 1.8k target cut text rows, and local copies of the cut-building
and prompt-building scripts.
