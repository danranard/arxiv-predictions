# Context-Only SFT Control

Metric: `clip2`; contrast: real forecast `Z` under the frozen Qwen3-8B score minus the context-only SFT continuation-control score. The SFT control is trained without forecast strings and evaluated on source manuscripts excluded from SFT training. The filename keeps the older `noz` label because `Z` is absent in this control.

Join: Fireworks real-Z scaffold_z_predictor minus HF/LoRA adapter bare_B, joined by (paper_id, cut_id)

| model lane | n | mean +/- SE | positive rate |
| --- | ---: | ---: | ---: |
| gpt55_high | 220 | +0.08166 +/- 0.01291 | 0.60455 |
| gpt55_low | 220 | +0.07864 +/- 0.01294 | 0.61818 |
| gpt55_medium | 220 | +0.07685 +/- 0.01278 | 0.61818 |
| gpt55_none | 220 | +0.04917 +/- 0.01246 | 0.53182 |
| nano_high | 218 | -0.01070 +/- 0.01311 | 0.38073 |
| nano_medium | 220 | -0.02147 +/- 0.01283 | 0.34091 |
| nano_low | 220 | -0.03436 +/- 0.01192 | 0.31364 |
