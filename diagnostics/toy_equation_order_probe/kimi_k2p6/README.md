# Toy equation-order Qwen probe

Model: `accounts/fireworks/models/kimi-k2p6`

All scored targets omit the closing display delimiter. The left-hand side is always `Z =`.

## Score Summary

| case | condition | raw | clip2 | clip2 vs empty | clip2 vs bare |
|---|---:|---:|---:|---:|---:|
| add_ab | bare_B | -2.0047 | -1.2141 | +0.2355 | +0.0000 |
| add_ab | true_forecast | -0.0244 | -0.0244 | +1.4252 | +1.1896 |
| add_ab | reordered_forecast | -0.6210 | -0.4304 | +1.0193 | +0.7837 |
| add_ab | wrong_symbol_forecast | -2.4577 | -0.9546 | +0.4950 | +0.2595 |
| add_ab | empty | -2.9809 | -1.4496 | +0.0000 | -0.2355 |
| add_ba | bare_B | -2.8305 | -1.6898 | +0.2633 | +0.0000 |
| add_ba | true_forecast | -0.0477 | -0.0477 | +1.9054 | +1.6421 |
| add_ba | reordered_forecast | -0.9284 | -0.4221 | +1.5310 | +1.2677 |
| add_ba | wrong_symbol_forecast | -3.2296 | -1.2140 | +0.7392 | +0.4759 |
| add_ba | empty | -3.6156 | -1.9531 | +0.0000 | -0.2633 |
| mul_ab | bare_B | -4.1182 | -1.6768 | +0.2666 | +0.0000 |
| mul_ab | true_forecast | -0.0384 | -0.0384 | +1.9050 | +1.6384 |
| mul_ab | reordered_forecast | -1.0871 | -0.5246 | +1.4187 | +1.1521 |
| mul_ab | wrong_symbol_forecast | -4.1075 | -1.0216 | +0.9218 | +0.6552 |
| mul_ab | empty | -4.6855 | -1.9434 | +0.0000 | -0.2666 |
| mul_ba | bare_B | -4.2695 | -1.6836 | +0.2559 | +0.0000 |
| mul_ba | true_forecast | -0.0471 | -0.0471 | +1.8924 | +1.6365 |
| mul_ba | reordered_forecast | -1.2603 | -0.5260 | +1.4135 | +1.1576 |
| mul_ba | wrong_symbol_forecast | -4.8897 | -1.0147 | +0.9247 | +0.6689 |
| mul_ba | empty | -5.1426 | -1.9395 | +0.0000 | -0.2559 |

## Forced-Likelihood Recovery Probe

The recovery probe asks for the probability of the true next token after the
true prefix has already passed through the local mismatch induced by the
reordered forecast. These values are derived from `target_token_logprobs.csv`,
using the same forced-likelihood scoring path as the benchmark.

| case | condition | partial | true next | forced token | p(true next) |
|---|---|---|---:|---:|---:|
| add_ab | true_forecast | `Z = X + A +` | ` B` | ` B` | 0.9871 |
| add_ab | reordered_forecast | `Z = X + A +` | ` B` | ` B` | 0.9871 |
| add_ab | wrong_symbol_forecast | `Z = X + A +` | ` B` | ` B` | 0.5068 |
| add_ab | empty | `Z = X + A +` | ` B` | ` B` | 0.7050 |
| add_ba | true_forecast | `Z = X + B +` | ` A` | ` A` | 0.9885 |
| add_ba | reordered_forecast | `Z = X + B +` | ` A` | ` A` | 0.9696 |
| add_ba | wrong_symbol_forecast | `Z = X + B +` | ` A` | ` A` | 0.0453 |
| add_ba | empty | `Z = X + B +` | ` A` | ` A` | 0.0888 |
| mul_ab | true_forecast | `Z = X + A` | ` B` | ` B` | 0.9884 |
| mul_ab | reordered_forecast | `Z = X + A` | ` B` | ` B` | 0.9727 |
| mul_ab | wrong_symbol_forecast | `Z = X + A` | ` B` | ` B` | 0.0007 |
| mul_ab | empty | `Z = X + A` | ` B` | ` B` | 0.0051 |
| mul_ba | true_forecast | `Z = X + B` | ` A` | ` A` | 0.9888 |
| mul_ba | reordered_forecast | `Z = X + B` | ` A` | ` A` | 0.9885 |
| mul_ba | wrong_symbol_forecast | `Z = X + B` | ` A` | ` A` | 0.0001 |
| mul_ba | empty | `Z = X + B` | ` A` | ` A` | 0.0007 |
