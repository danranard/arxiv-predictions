# Toy equation-order Qwen probe

Model: `accounts/fireworks/models/qwen3-8b`

All scored targets omit the closing display delimiter. The left-hand side is always `Z =`.

## Score Summary

| case | condition | raw | clip2 | clip2 vs empty | clip2 vs bare |
|---|---:|---:|---:|---:|---:|
| add_ab | bare_B | -1.9494 | -1.1025 | +0.4400 | +0.0000 |
| add_ab | true_forecast | -0.0083 | -0.0083 | +1.5342 | +1.0942 |
| add_ab | reordered_forecast | -0.7134 | -0.4072 | +1.1354 | +0.6954 |
| add_ab | wrong_symbol_forecast | -3.2380 | -0.9005 | +0.6421 | +0.2021 |
| add_ab | empty | -3.3051 | -1.5426 | +0.0000 | -0.4400 |
| add_ba | bare_B | -3.1543 | -1.5293 | +0.3926 | +0.0000 |
| add_ba | true_forecast | -0.0112 | -0.0112 | +1.9107 | +1.5181 |
| add_ba | reordered_forecast | -0.8688 | -0.4375 | +1.4843 | +1.0918 |
| add_ba | wrong_symbol_forecast | -4.1286 | -1.2005 | +0.7214 | +0.3288 |
| add_ba | empty | -4.2406 | -1.9219 | +0.0000 | -0.3926 |
| mul_ab | bare_B | -4.3218 | -1.5288 | +0.4224 | +0.0000 |
| mul_ab | true_forecast | -0.0034 | -0.0034 | +1.9478 | +1.5254 |
| mul_ab | reordered_forecast | -1.2882 | -0.5070 | +1.4442 | +1.0218 |
| mul_ab | wrong_symbol_forecast | -5.4850 | -1.0006 | +0.9506 | +0.5282 |
| mul_ab | empty | -5.3027 | -1.9512 | +0.0000 | -0.4224 |
| mul_ba | bare_B | -4.8530 | -1.5288 | +0.4224 | +0.0000 |
| mul_ba | true_forecast | -0.0040 | -0.0040 | +1.9472 | +1.5248 |
| mul_ba | reordered_forecast | -1.5667 | -0.5042 | +1.4470 | +1.0246 |
| mul_ba | wrong_symbol_forecast | -6.2818 | -1.0006 | +0.9506 | +0.5282 |
| mul_ba | empty | -5.6074 | -1.9512 | +0.0000 | -0.4224 |

## Forced-Likelihood Recovery Probe

The recovery probe asks for the probability of the true next token after the
true prefix has already passed through the local mismatch induced by the
reordered forecast. These values are derived from `target_token_logprobs.csv`,
using the same forced-likelihood scoring path as the benchmark.

| case | condition | partial | true next | forced token | p(true next) |
|---|---|---|---:|---:|---:|
| add_ab | true_forecast | `Z = X + A +` | ` B` | ` B` | 0.9979 |
| add_ab | reordered_forecast | `Z = X + A +` | ` B` | ` B` | 0.9934 |
| add_ab | wrong_symbol_forecast | `Z = X + A +` | ` B` | ` B` | 0.6065 |
| add_ab | empty | `Z = X + A +` | ` B` | ` B` | 0.6444 |
| add_ba | true_forecast | `Z = X + B +` | ` A` | ` A` | 0.9956 |
| add_ba | reordered_forecast | `Z = X + B +` | ` A` | ` A` | 0.8570 |
| add_ba | wrong_symbol_forecast | `Z = X + B +` | ` A` | ` A` | 0.0736 |
| add_ba | empty | `Z = X + B +` | ` A` | ` A` | 0.0332 |
| mul_ab | true_forecast | `Z = X + A` | ` B` | ` B` | 0.9990 |
| mul_ab | reordered_forecast | `Z = X + A` | ` B` | ` B` | 0.9787 |
| mul_ab | wrong_symbol_forecast | `Z = X + A` | ` B` | ` B` | 0.0001 |
| mul_ab | empty | `Z = X + A` | ` B` | ` B` | 0.0014 |
| mul_ba | true_forecast | `Z = X + B` | ` A` | ` A` | 0.9990 |
| mul_ba | reordered_forecast | `Z = X + B` | ` A` | ` A` | 0.9897 |
| mul_ba | wrong_symbol_forecast | `Z = X + B` | ` A` | ` A` | 0.0000 |
| mul_ba | empty | `Z = X + B` | ` A` | ` A` | 0.0016 |
