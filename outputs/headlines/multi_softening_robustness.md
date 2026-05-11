# Multi-Softening Robustness

These tables are computed from frozen token-level scorer logprobs. The contrast is
`scaffold_z_predictor - bare_B`, where `bare_B` is the same-budget recent-context
control. Standard errors below are paper-clustered.

Metrics:

- `raw`: mean token logprob.
- `clipK`: token logprob floored at `-K`, then averaged.
- `sqrt_nll`: `-sqrt(max(-logprob, 0))` averaged over target tokens.
- `log1p_nll`: `-log(1 + max(-logprob, 0))` averaged over target tokens.

## Qwen: combined 1363-cut benchmark

| metric | model lane | n | mean lift | paper-clustered SE | positive rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `raw` | `gpt55_none` | 1363 | +0.07341 | 0.01420 | 0.470 |
| `raw` | `gpt55_low` | 1363 | +0.11727 | 0.01373 | 0.544 |
| `raw` | `gpt55_medium` | 1363 | +0.13165 | 0.01455 | 0.566 |
| `raw` | `gpt55_high` | 1363 | +0.13385 | 0.01410 | 0.558 |
| `raw` | `nano_low` | 1363 | -0.08877 | 0.01253 | 0.324 |
| `raw` | `nano_medium` | 1363 | -0.06114 | 0.01301 | 0.347 |
| `raw` | `nano_high` | 1363 | -0.04844 | 0.01299 | 0.362 |
| `raw` | `opus47_low` | 1363 | +0.09133 | 0.01341 | 0.520 |
| `raw` | `opus47_medium` | 1363 | +0.10575 | 0.01334 | 0.534 |
| `clip2` | `gpt55_none` | 1363 | +0.16585 | 0.00621 | 0.842 |
| `clip2` | `gpt55_low` | 1363 | +0.19084 | 0.00591 | 0.864 |
| `clip2` | `gpt55_medium` | 1363 | +0.19707 | 0.00632 | 0.871 |
| `clip2` | `gpt55_high` | 1363 | +0.20088 | 0.00621 | 0.873 |
| `clip2` | `nano_low` | 1363 | +0.07957 | 0.00557 | 0.616 |
| `clip2` | `nano_medium` | 1363 | +0.10047 | 0.00609 | 0.648 |
| `clip2` | `nano_high` | 1363 | +0.10757 | 0.00609 | 0.662 |
| `clip2` | `opus47_low` | 1363 | +0.17772 | 0.00587 | 0.843 |
| `clip2` | `opus47_medium` | 1363 | +0.18405 | 0.00593 | 0.856 |
| `clip3` | `gpt55_none` | 1363 | +0.18320 | 0.00802 | 0.759 |
| `clip3` | `gpt55_low` | 1363 | +0.21493 | 0.00759 | 0.811 |
| `clip3` | `gpt55_medium` | 1363 | +0.22279 | 0.00815 | 0.822 |
| `clip3` | `gpt55_high` | 1363 | +0.22729 | 0.00800 | 0.827 |
| `clip3` | `nano_low` | 1363 | +0.07166 | 0.00714 | 0.544 |
| `clip3` | `nano_medium` | 1363 | +0.09792 | 0.00779 | 0.591 |
| `clip3` | `nano_high` | 1363 | +0.10593 | 0.00784 | 0.604 |
| `clip3` | `opus47_low` | 1363 | +0.19845 | 0.00758 | 0.782 |
| `clip3` | `opus47_medium` | 1363 | +0.20683 | 0.00768 | 0.800 |
| `clip5` | `gpt55_none` | 1363 | +0.18144 | 0.01022 | 0.669 |
| `clip5` | `gpt55_low` | 1363 | +0.22204 | 0.00980 | 0.723 |
| `clip5` | `gpt55_medium` | 1363 | +0.23124 | 0.01043 | 0.742 |
| `clip5` | `gpt55_high` | 1363 | +0.23553 | 0.01024 | 0.740 |
| `clip5` | `nano_low` | 1363 | +0.04036 | 0.00913 | 0.472 |
| `clip5` | `nano_medium` | 1363 | +0.07062 | 0.00976 | 0.494 |
| `clip5` | `nano_high` | 1363 | +0.07867 | 0.00980 | 0.495 |
| `clip5` | `opus47_low` | 1363 | +0.20061 | 0.00975 | 0.701 |
| `clip5` | `opus47_medium` | 1363 | +0.21094 | 0.00984 | 0.721 |
| `sqrt_nll` | `gpt55_none` | 1363 | +0.15811 | 0.00662 | 0.795 |
| `sqrt_nll` | `gpt55_low` | 1363 | +0.18553 | 0.00631 | 0.847 |
| `sqrt_nll` | `gpt55_medium` | 1363 | +0.19278 | 0.00681 | 0.848 |
| `sqrt_nll` | `gpt55_high` | 1363 | +0.19649 | 0.00666 | 0.853 |
| `sqrt_nll` | `nano_low` | 1363 | +0.06487 | 0.00588 | 0.563 |
| `sqrt_nll` | `nano_medium` | 1363 | +0.08595 | 0.00628 | 0.614 |
| `sqrt_nll` | `nano_high` | 1363 | +0.09318 | 0.00633 | 0.620 |
| `sqrt_nll` | `opus47_low` | 1363 | +0.17001 | 0.00624 | 0.803 |
| `sqrt_nll` | `opus47_medium` | 1363 | +0.17749 | 0.00626 | 0.820 |
| `log1p_nll` | `gpt55_none` | 1363 | +0.10178 | 0.00494 | 0.734 |
| `log1p_nll` | `gpt55_low` | 1363 | +0.12127 | 0.00472 | 0.774 |
| `log1p_nll` | `gpt55_medium` | 1363 | +0.12625 | 0.00507 | 0.800 |
| `log1p_nll` | `gpt55_high` | 1363 | +0.12856 | 0.00495 | 0.798 |
| `log1p_nll` | `nano_low` | 1363 | +0.03409 | 0.00439 | 0.502 |
| `log1p_nll` | `nano_medium` | 1363 | +0.04885 | 0.00471 | 0.552 |
| `log1p_nll` | `nano_high` | 1363 | +0.05387 | 0.00473 | 0.550 |
| `log1p_nll` | `opus47_low` | 1363 | +0.11057 | 0.00468 | 0.746 |
| `log1p_nll` | `opus47_medium` | 1363 | +0.11584 | 0.00469 | 0.772 |

## Kimi: combined 1363-cut benchmark

| metric | model lane | n | mean lift | paper-clustered SE | positive rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `raw` | `gpt55_none` | 1363 | +0.06916 | 0.01174 | 0.467 |
| `raw` | `gpt55_low` | 1363 | +0.10682 | 0.01178 | 0.530 |
| `raw` | `gpt55_medium` | 1363 | +0.12107 | 0.01230 | 0.549 |
| `raw` | `gpt55_high` | 1363 | +0.12879 | 0.01204 | 0.553 |
| `raw` | `nano_low` | 1363 | -0.05841 | 0.01029 | 0.321 |
| `raw` | `nano_medium` | 1363 | -0.03067 | 0.01105 | 0.344 |
| `raw` | `nano_high` | 1363 | -0.01959 | 0.01123 | 0.354 |
| `raw` | `opus47_low` | 1363 | +0.09010 | 0.01161 | 0.506 |
| `raw` | `opus47_medium` | 1363 | +0.10268 | 0.01147 | 0.525 |
| `clip2` | `gpt55_none` | 1363 | +0.13203 | 0.00632 | 0.746 |
| `clip2` | `gpt55_low` | 1363 | +0.15844 | 0.00627 | 0.792 |
| `clip2` | `gpt55_medium` | 1363 | +0.16495 | 0.00664 | 0.820 |
| `clip2` | `gpt55_high` | 1363 | +0.16985 | 0.00647 | 0.813 |
| `clip2` | `nano_low` | 1363 | +0.04886 | 0.00575 | 0.522 |
| `clip2` | `nano_medium` | 1363 | +0.06948 | 0.00604 | 0.570 |
| `clip2` | `nano_high` | 1363 | +0.07632 | 0.00618 | 0.572 |
| `clip2` | `opus47_low` | 1363 | +0.14610 | 0.00614 | 0.772 |
| `clip2` | `opus47_medium` | 1363 | +0.15334 | 0.00620 | 0.785 |
| `clip3` | `gpt55_none` | 1363 | +0.13341 | 0.00793 | 0.663 |
| `clip3` | `gpt55_low` | 1363 | +0.16596 | 0.00786 | 0.723 |
| `clip3` | `gpt55_medium` | 1363 | +0.17332 | 0.00831 | 0.744 |
| `clip3` | `gpt55_high` | 1363 | +0.17925 | 0.00810 | 0.747 |
| `clip3` | `nano_low` | 1363 | +0.02993 | 0.00713 | 0.444 |
| `clip3` | `nano_medium` | 1363 | +0.05398 | 0.00753 | 0.480 |
| `clip3` | `nano_high` | 1363 | +0.06191 | 0.00772 | 0.494 |
| `clip3` | `opus47_low` | 1363 | +0.15063 | 0.00764 | 0.696 |
| `clip3` | `opus47_medium` | 1363 | +0.16012 | 0.00763 | 0.715 |
| `clip5` | `gpt55_none` | 1363 | +0.10434 | 0.01003 | 0.532 |
| `clip5` | `gpt55_low` | 1363 | +0.14134 | 0.00994 | 0.605 |
| `clip5` | `gpt55_medium` | 1363 | +0.15083 | 0.01042 | 0.629 |
| `clip5` | `gpt55_high` | 1363 | +0.15865 | 0.01016 | 0.637 |
| `clip5` | `nano_low` | 1363 | -0.01694 | 0.00894 | 0.354 |
| `clip5` | `nano_medium` | 1363 | +0.00836 | 0.00943 | 0.382 |
| `clip5` | `nano_high` | 1363 | +0.01762 | 0.00959 | 0.395 |
| `clip5` | `opus47_low` | 1363 | +0.12407 | 0.00976 | 0.567 |
| `clip5` | `opus47_medium` | 1363 | +0.13491 | 0.00960 | 0.585 |
| `sqrt_nll` | `gpt55_none` | 1363 | +0.11996 | 0.00616 | 0.717 |
| `sqrt_nll` | `gpt55_low` | 1363 | +0.14610 | 0.00609 | 0.775 |
| `sqrt_nll` | `gpt55_medium` | 1363 | +0.15351 | 0.00648 | 0.787 |
| `sqrt_nll` | `gpt55_high` | 1363 | +0.15871 | 0.00635 | 0.796 |
| `sqrt_nll` | `nano_low` | 1363 | +0.03752 | 0.00557 | 0.487 |
| `sqrt_nll` | `nano_medium` | 1363 | +0.05751 | 0.00587 | 0.554 |
| `sqrt_nll` | `nano_high` | 1363 | +0.06478 | 0.00603 | 0.547 |
| `sqrt_nll` | `opus47_low` | 1363 | +0.13268 | 0.00604 | 0.729 |
| `sqrt_nll` | `opus47_medium` | 1363 | +0.14051 | 0.00607 | 0.745 |
| `log1p_nll` | `gpt55_none` | 1363 | +0.07897 | 0.00476 | 0.654 |
| `log1p_nll` | `gpt55_low` | 1363 | +0.09799 | 0.00474 | 0.714 |
| `log1p_nll` | `gpt55_medium` | 1363 | +0.10325 | 0.00501 | 0.743 |
| `log1p_nll` | `gpt55_high` | 1363 | +0.10684 | 0.00489 | 0.743 |
| `log1p_nll` | `nano_low` | 1363 | +0.01832 | 0.00429 | 0.439 |
| `log1p_nll` | `nano_medium` | 1363 | +0.03263 | 0.00451 | 0.481 |
| `log1p_nll` | `nano_high` | 1363 | +0.03775 | 0.00463 | 0.494 |
| `log1p_nll` | `opus47_low` | 1363 | +0.08878 | 0.00466 | 0.671 |
| `log1p_nll` | `opus47_medium` | 1363 | +0.09431 | 0.00466 | 0.704 |

## Paired thinking comparisons

The full paired-comparison table for every metric is saved as
`multi_softening_paired_comparisons.csv`. The headline manuscript figure uses
`clip2`, but the other softened metrics preserve the same broad ordering.
