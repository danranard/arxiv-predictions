# Artifact Map

## Results Narrative

- `RESULTS_SUMMARY.md`: results-section style overview of the headline
  equation-suffix result, thinking-effort comparisons, `clip2`, the
  equation-ordering diagnostic, SFT controls, and the prose/TeX continuation
  follow-up.
- `docs/MANUSCRIPT_ALIGNMENT.md`: map from manuscript claims, figures, and
  tables to the bundled data and scripts.

## Headline Equation Module

The default equation-suffix benchmark lives at:

```text
data/frozen/equation_splits/
```

Key files:

- `data/cuts_all1363.jsonl`: text-bearing merged benchmark rows.
- `data/cuts_old731.jsonl`: first construction wave.
- `data/cuts_new632.jsonl`: same-recipe extension wave.
- `data/paper_list.csv`: source-paper provenance for both components.
- `derived/model_summaries.csv`: per-model forecast lift summaries.
- `derived/row_lifts_clip2_raw.csv`: per-cut lift rows for raw and `clip2`.
- `derived/thinking_comparisons_clip2_paper_clustered.csv`: paired model
  comparisons with paper-clustered standard errors.
- `generations/old731/` and `generations/new632/`: finalized stripped OpenAI
  generation lanes.
- `scores/source_components/`: frozen Qwen3-8B and Kimi K2.6 token scores from
  the two construction waves.
- `scores/repair_old731_nano_high_missing10/`: repair scores for the first-wave
  nano-high missing rows, so the combined nano-high lane covers all 1363 cuts.
- `MANIFEST.json`: checksums for the source superbundle payload.

Stable merged equation joins should use `super_key`, which has the form:

```text
component_bundle:paper_id:cut_id
```

The `component_bundle` field is currently `old731` or `new632`. Treat these as
construction-wave provenance labels unless an analysis explicitly studies the
expansion from the first wave to the combined benchmark.

## First Construction Wave Files

The original 731-cut component remains in its earlier location for SFT control,
examples, and older smoke scripts:

- `data/frozen/data/cuts_731.jsonl`
- `data/frozen/data/cuts_731_metadata.csv`
- `data/frozen/data/paper_provenance.csv`
- `data/frozen/generations/`
- `data/frozen/scores/small_qwen_current_full731/`
- `data/frozen/scores/kimi_k2p6_current_full731/`

These files are not the default headline universe anymore, but they remain the
source of truth for the context-only SFT control and row-level examples.

## Context-Only SFT Control

- `data/frozen/scores/heldout33_softresid_no_z_control/`: source-disjoint
  context-only Qwen3-8B LoRA control for the first construction wave.

See `docs/SFT_REPRODUCIBILITY.md`.

## Prose Continuation Module

The prose/TeX continuation follow-up is intentionally modular:

```text
modules/prose_continuation/
```

Key files:

- `README.md`: module overview and headline.
- `analysis/forecast_clip2_sft_vs_bareB_clip2_sft_summary.csv`: route
  comparison summaries.
- `analysis/forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv`: joined row-level
  forecast-route minus context-route comparisons.
- `analysis/audit_summary.json`: local audit of joins, splits, boundaries, and
  target windows.
- `analysis/generation_prompt_samples.md` and `analysis/GENERATION_QA.md`:
  human-readable generation quality checks.
- `provenance/paper_list.csv`: 40-paper source slate.
- `provenance/selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl`:
  canonical selected cut text rows.
- `scorer_inputs/`: forecast-scaffold and bare-context completion prompts.
- `source_scores/base_qwen_frozen_prefix_windows/`: compact no-SFT Qwen3-8B
  scaffold-scorer prefix-window summaries.
- `source_scores/`: frozen SFT-route scores.
- `WEIGHTS_AND_TRAINING.md`: LoRA training details and adapter archive
  provenance.

This module shares notation with the equation task but is not part of the
headline equation-suffix benchmark.

## Prompt Snapshots

`docs/prompt_snapshots/` contains one concrete row-0 example for the first
construction wave: predictor prompt, forecast output, scaffolded scoring
prompts, and recent-context control. These are inspection aids, not substitutes
for the frozen CSV/JSON artifacts.

## Outputs

`scripts/reproduce_headlines.py` writes:

- `dataset_audit.md`
- `realz_lift_by_judge.md`
- `paired_thinking_comparisons.md`
- `noz_sft_control.md`
- corresponding CSV/JSON files

The first three outputs use the merged 1363-cut equation module. The
context-only SFT output (`noz_sft_control.md`) uses the first construction wave
because that is where the context-only SFT control was trained and evaluated.

`scripts/recompute_clip2_from_tokens.py` recomputes the first construction
wave's `clip2` summaries from token-level logprob CSVs. The merged module already
includes derived row-lift and comparison tables.

## Diagnostics

- `diagnostics/toy_equation_order_probe/`: a small mechanism probe for the
  equation scaffold and `clip2`, run with both Qwen3-8B and Kimi K2.6. It uses
  toy equations such as `Z = X + A + B` to show that reordered forecasts are
  locally penalized but can still produce strong `clip2` lift after the true
  partial has caught up.

## Demo

- `demo/`: a self-contained single-paper pipeline demo using a bundled TeX
  source for arXiv:2307.05326. The default path reads frozen 10-cut demo
  generations and Qwen3-8B scores. Optional flags rerun cut extraction,
  OpenAI nano low/medium generation, and Fireworks/Qwen scoring.

The demo is pedagogical. It is not part of the headline benchmark and should
not be used as a standalone model-ordering claim.

## Construction Scripts

- `scripts/download_arxiv_source.py`: optional arXiv source downloader and main
  TeX promoter.
- `scripts/pilot_equation_cut_prompts.py`: original cut extraction and prompt
  construction logic.
- `scripts/build_equation_cut_dataset.py`: deterministic multi-paper cut
  selection from promoted TeX files.
- `data/frozen/equation_splits/scripts/`: exact scripts copied from the
  combined superbundle, including the newer merged-bundle builder and scoring
  scripts.

See `docs/DATASET_CONSTRUCTION.md`.
