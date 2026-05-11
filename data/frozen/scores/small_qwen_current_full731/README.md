# Qwen3-8B Current-Scaffold Full731 Aggregate

Created: 2026-05-01T10:47:36.320260+00:00

Scorer: `accounts/fireworks/models/qwen3-8b`
Scaffold: `current`

This folder aggregates existing Qwen3-8B scoring with new missing-row scoring for the finalized OpenAI full731 generation bundle.

## Clip2 Headline: Z - bare_B

| lane | n | mean | stderr | median | positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| gpt55_none | 731 | +0.16670 | +0.00769 | +0.11179 | +0.82763 |
| gpt55_low | 731 | +0.19151 | +0.00771 | +0.14681 | +0.85773 |
| gpt55_medium | 731 | +0.19592 | +0.00774 | +0.14673 | +0.86867 |
| gpt55_high | 731 | +0.20212 | +0.00792 | +0.15993 | +0.86183 |
| nano_low | 731 | +0.07373 | +0.00690 | +0.03561 | +0.59508 |
| nano_medium | 731 | +0.09578 | +0.00734 | +0.04615 | +0.63064 |
| nano_high | 721 | +0.10338 | +0.00757 | +0.04789 | +0.63245 |

## Clip2 Paired Model Comparisons

| comparison | n | mean | stderr | positive rate |
| --- | ---: | ---: | ---: | ---: |
| gpt55_low_minus_gpt55_none | 731 | +0.02481 | +0.00404 | +0.52120 |
| gpt55_medium_minus_gpt55_none | 731 | +0.02922 | +0.00425 | +0.55951 |
| gpt55_high_minus_gpt55_none | 731 | +0.03542 | +0.00463 | +0.57319 |
| gpt55_medium_minus_gpt55_low | 731 | +0.00440 | +0.00336 | +0.41176 |
| gpt55_high_minus_gpt55_low | 731 | +0.01061 | +0.00397 | +0.44460 |
| gpt55_high_minus_gpt55_medium | 731 | +0.00620 | +0.00372 | +0.39535 |
| nano_medium_minus_nano_low | 731 | +0.02205 | +0.00412 | +0.56908 |
| nano_high_minus_nano_low | 721 | +0.02884 | +0.00479 | +0.58114 |
| nano_high_minus_nano_medium | 721 | +0.00659 | +0.00403 | +0.48821 |
| gpt55_high_minus_nano_high | 721 | +0.09961 | +0.00531 | +0.80028 |
| gpt55_medium_minus_nano_high | 721 | +0.09316 | +0.00516 | +0.78641 |

Files:

- `RUN_MANIFEST.json`: reused score folders and missing-row score runs.
- `combined_equation_scores.csv`: raw per-row score table with `model_lane`.
- `combined_target_token_logprobs.csv`: token-level logprobs with `model_lane`.
- `softened_model_summary.json`: raw and softened contrasts.
