# Single-Paper Equation Demo Report

Paper: arXiv:2307.05326. This is a pipeline demo, not part of the headline benchmark.

Metric: `clip2`; contrast: predictor forecast condition minus `bare_B`.

| row | nano low lift | nano medium lift | bare_B clip2 | low clip2 | medium clip2 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | -0.0454 | +0.0198 | -0.4706 | -0.5160 | -0.4507 |
| 1 | +0.4438 | +0.4360 | -0.7098 | -0.2659 | -0.2738 |
| 2 | +0.1300 | -0.0005 | -0.6016 | -0.4716 | -0.6021 |
| 3 | +0.3344 | +0.5644 | -0.8174 | -0.4830 | -0.2529 |
| 4 | +0.0040 | -0.1186 | -0.7613 | -0.7573 | -0.8799 |
| 5 | +0.0682 | +0.0467 | -0.7063 | -0.6382 | -0.6596 |
| 6 | -0.0065 | -0.0072 | -0.2530 | -0.2595 | -0.2602 |
| 7 | +0.7112 | +0.8424 | -1.2119 | -0.5008 | -0.3695 |
| 8 | +0.0270 | +0.0863 | -0.4513 | -0.4243 | -0.3651 |
| 9 | -0.0304 | -0.0921 | -0.3053 | -0.3357 | -0.3974 |

Nano low mean lift: +0.1636 +/- 0.0797; positive 7/10.
Nano medium mean lift: +0.1777 +/- 0.1019; positive 6/10.

Interpretation note: this is a 10-cut single-paper pipeline demo. It is not meant to establish a benchmark/model-ordering result by itself; the main reported equation-suffix results use many more cuts across many papers.

Frozen generations: `demo\frozen\generations_demo10.jsonl` (20 rows).
Frozen scores: `demo\frozen\qwen3_8b_scores_demo10.csv`.
