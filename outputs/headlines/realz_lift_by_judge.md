# Forecast Lift Over Context-Only Baseline

Metric: `clip2`; contrast: forecast string `Z` minus same-budget recent-context control `bare_B`.
Reported SE is clustered by paper.

| model lane | Qwen3-8B mean +/- paper-clustered SE | Kimi K2.6 mean +/- paper-clustered SE |
| --- | ---: | ---: |
| gpt55_none | +0.16585 +/- 0.00617 | +0.13203 +/- 0.00629 |
| gpt55_low | +0.19084 +/- 0.00586 | +0.15844 +/- 0.00623 |
| gpt55_medium | +0.19707 +/- 0.00628 | +0.16495 +/- 0.00661 |
| gpt55_high | +0.20088 +/- 0.00617 | +0.16985 +/- 0.00644 |
| nano_low | +0.07957 +/- 0.00557 | +0.04886 +/- 0.00576 |
| nano_medium | +0.10047 +/- 0.00603 | +0.06948 +/- 0.00601 |
| nano_high | +0.10757 +/- 0.00604 | +0.07632 +/- 0.00614 |
| opus47_low | +0.17772 +/- 0.00586 | +0.14610 +/- 0.00612 |
| opus47_medium | +0.18405 +/- 0.00589 | +0.15334 +/- 0.00617 |
