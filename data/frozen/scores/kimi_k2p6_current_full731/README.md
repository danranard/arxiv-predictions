# Kimi K2.6 Current-Scaffold Full731 Aggregate

Created: 2026-05-01T11:26:22.400284+00:00

Scorer: `accounts/fireworks/models/kimi-k2p6`
Scaffold: `current`

This folder scores the finalized OpenAI full731 generation bundle with Kimi K2.6 using the original/current scaffold, so it is directly comparable to the Qwen3-8B current-scaffold aggregate.

`bare_B` rows are reused from the earlier Kimi full731 aggregate because `bare_B` does not use the scaffold text. `scaffold_empty`, `scaffold_oracle_Y`, and all model-Z rows are current-scaffold scores.

## Clip2 Headline: Z - bare_B

| lane | n | mean | stderr | median | positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| gpt55_none | 731 | +0.12969 | +0.00771 | +0.07337 | +0.73871 |
| gpt55_low | 731 | +0.15655 | +0.00784 | +0.11369 | +0.78112 |
| gpt55_medium | 731 | +0.16120 | +0.00789 | +0.10873 | +0.81122 |
| gpt55_high | 731 | +0.16679 | +0.00806 | +0.12153 | +0.79617 |
| nano_low | 731 | +0.04005 | +0.00699 | +0.00076 | +0.50342 |
| nano_medium | 731 | +0.06245 | +0.00749 | +0.01473 | +0.57045 |
| nano_high | 721 | +0.06824 | +0.00772 | +0.01258 | +0.54924 |

## Clip2 Paired Model Comparisons

| comparison | n | mean | stderr | positive rate |
| --- | ---: | ---: | ---: | ---: |
| gpt55_low_minus_gpt55_none | 731 | +0.02686 | +0.00392 | +0.61149 |
| gpt55_medium_minus_gpt55_none | 731 | +0.03151 | +0.00420 | +0.63885 |
| gpt55_high_minus_gpt55_none | 731 | +0.03710 | +0.00466 | +0.64295 |
| gpt55_medium_minus_gpt55_low | 731 | +0.00465 | +0.00353 | +0.53215 |
| gpt55_high_minus_gpt55_low | 731 | +0.01024 | +0.00409 | +0.57045 |
| gpt55_high_minus_gpt55_medium | 731 | +0.00559 | +0.00370 | +0.49658 |
| nano_medium_minus_nano_low | 731 | +0.02240 | +0.00419 | +0.59097 |
| nano_high_minus_nano_low | 721 | +0.02680 | +0.00481 | +0.57975 |
| nano_high_minus_nano_medium | 721 | +0.00428 | +0.00402 | +0.52843 |
| gpt55_high_minus_nano_high | 721 | +0.09998 | +0.00536 | +0.81137 |
| gpt55_medium_minus_nano_high | 721 | +0.09400 | +0.00523 | +0.80166 |

Files:

- `RUN_MANIFEST.json`: exact score runs and reused `bare_B` source.
- `combined_equation_scores.csv`: raw per-row score table with `model_lane`.
- `combined_target_token_logprobs.csv`: token-level logprobs with `model_lane`.
- `softened_model_summary.json`: raw and softened contrasts.
