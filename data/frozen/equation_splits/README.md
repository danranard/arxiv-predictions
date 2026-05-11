# Equation-Suffix Benchmark Bundle

Created: 2026-05-04T23:20:27.158210+00:00

Frozen combined equation-suffix benchmark bundle for the manuscript companion
artifact. The 1363-cut benchmark combines a first construction wave with a
same-recipe extension wave; those labels are retained for provenance and
optional robustness checks, not as separate benchmark families.

## Counts

- First construction wave (`old731`): 731 cuts from 74 papers.
- Extension wave (`new632`): 632 cuts from 64 papers.
- Combined benchmark: 1363 cuts from 138 papers.
- Wave paper overlap: 0.

## Primary Analysis

Primary metric is Clip2: token logprobs are clipped below -2, then averaged
over scored target tokens. Lifts are `scaffold_z_predictor - bare_B`, where
`bare_B` is the same-budget recent-context control. Model comparisons are
paired by cut, with paper-clustered SE as the headline uncertainty.

### Qwen3-8B Combined Clip2

- `gpt55_low_minus_gpt55_none`: +0.02498 +/- 0.00319 (n=1363, papers=138)
- `gpt55_medium_minus_gpt55_none`: +0.03122 +/- 0.00343 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_none`: +0.03502 +/- 0.00378 (n=1363, papers=138)
- `gpt55_medium_minus_gpt55_low`: +0.00624 +/- 0.00248 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_low`: +0.01004 +/- 0.00310 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_medium`: +0.00380 +/- 0.00248 (n=1363, papers=138)
- `nano_medium_minus_nano_low`: +0.02090 +/- 0.00329 (n=1363, papers=138)
- `nano_high_minus_nano_low`: +0.02799 +/- 0.00369 (n=1363, papers=138)
- `nano_high_minus_nano_medium`: +0.00710 +/- 0.00261 (n=1363, papers=138)
- `opus47_medium_minus_opus47_low`: +0.00633 +/- 0.00212 (n=1363, papers=138)

### Kimi K2.6 Combined Clip2

- `gpt55_low_minus_gpt55_none`: +0.02641 +/- 0.00306 (n=1363, papers=138)
- `gpt55_medium_minus_gpt55_none`: +0.03292 +/- 0.00344 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_none`: +0.03782 +/- 0.00381 (n=1363, papers=138)
- `gpt55_medium_minus_gpt55_low`: +0.00651 +/- 0.00258 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_low`: +0.01141 +/- 0.00323 (n=1363, papers=138)
- `gpt55_high_minus_gpt55_medium`: +0.00490 +/- 0.00244 (n=1363, papers=138)
- `nano_medium_minus_nano_low`: +0.02062 +/- 0.00341 (n=1363, papers=138)
- `nano_high_minus_nano_low`: +0.02746 +/- 0.00362 (n=1363, papers=138)
- `nano_high_minus_nano_medium`: +0.00684 +/- 0.00265 (n=1363, papers=138)
- `opus47_medium_minus_opus47_low`: +0.00724 +/- 0.00198 (n=1363, papers=138)

## Nano-High Repair

The first construction wave uses the repaired 731-row nano-high generation lane
from `generations/nano_high_repair_2026-05-03/`. The 10 repaired rows were
scored for Qwen and Kimi in this bundle, so nano-high comparisons now use the
same 1363 combined cuts as the other lanes.

## Anthropic Opus 4.7

This bundle now includes `opus47_low` and `opus47_medium` predictor lanes staged from `diagnostics/anthropic_claude_smoke/`. Opus appears in the model-comparison summaries as `opus47_medium_minus_opus47_low`; it is not assumed to participate in every downstream experiment built from the original GPT/nano lanes.

Usage diagnostics for Opus 4.7 are saved in `derived/opus47_usage_anthropic_token_estimates.csv` and summarized in `derived/opus47_usage_anthropic_token_estimates_summary.json`. These estimate non-visible Opus output tokens as saved Anthropic `output_tokens` minus an Anthropic `messages/count_tokens` estimate of the visible forecast text, with a small single-message overhead correction. Treat these as within-provider scale diagnostics rather than calibrated compute units comparable to OpenAI reasoning-token counts.

The two pathological medium rows were repaired with true `effort=medium`,
`no_thinking=false`, `max_tokens=32768` Anthropic calls. See
`OPUS47_CANONICAL_INPUTS.md` for the clean-input map and canonical retry
provenance. A longer retry-audit note is archived outside the public artifact
under the wrapper-level `meta_notes/` folder.

## Key Files

- `data/cuts_all1363.jsonl`: tagged cut rows from both construction waves.
- `generations/old731/` and `generations/new632/`: finalized stripped generation lanes.
- `scores/source_components/`: copied score CSVs/summaries from the source components.
- `scores/repair_old731_nano_high_missing10/`: Qwen/Kimi scores for the 10 repaired first-wave nano-high rows.
- `derived/row_lifts_clip2_raw.csv`: per-cut real-Z lift over `bare_B` for each scorer/model lane.
- `derived/thinking_comparisons.csv`: cut-paired, paper-clustered, and paper-level comparison statistics.
- `derived/row_lifts_all_softenings.csv`: per-cut real-Z lift over `bare_B`
  for `raw`, `clip2`, `clip3`, `clip5`, `sqrt_nll`, and `log1p_nll`.
- `derived/model_summaries_all_softenings.csv`: per-lane lift summaries for
  every saved softening, with paper-clustered SE.
- `derived/thinking_comparisons_all_softenings.csv`: cut-paired model
  comparisons for every saved softening, with paper-clustered SE.
- `MANIFEST.json`: checksums and provenance.

## Stable Keys

Use `bundle + paper_id + cut_id` as the stable key. `dataset_row_index` is local to each source component.
