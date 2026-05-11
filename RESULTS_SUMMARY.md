# Results Summary

This artifact studies a static forecasting signal, not a completed RLVR
training loop. The common setup is:

```text
X: visible technical-paper context
Y: hidden continuation to be scored
Z: model-written forecast of Y
```

A frozen likelihood scorer receives a prompt containing the visible context and
some auxiliary text, then we measure the likelihood assigned to the true
held-out text `Y`. The central question is whether real forecast information in
`Z` raises the scorer's likelihood more than simple controls, especially
controls that spend the same budget on recent previous context.

The headline result is the equation-suffix benchmark. A secondary prose/TeX
continuation module is included because it probes a harder and less clean
longer-continuation regime.

## Main Equation-Suffix Result

The headline benchmark has 1363 equation-suffix cuts from 138 recent arXiv
manuscripts. It was assembled in two construction waves whose labels are
retained in the data for provenance and optional robustness checks:

```text
first wave (old731): 731 cuts from 74 papers
extension wave (new632): 632 cuts from 64 papers
combined benchmark: 1363 cuts from 138 papers
```

For each cut, a predictor sees surrounding technical context and the visible
prefix of a displayed equation, then writes `Z`, a short forecast of the hidden
equation suffix. The primary comparison is:

```text
forecast Z score - bare_B score
```

where `bare_B` is the same-budget recent-context control. It uses the same
character budget as `Z` to provide recent previous source text, followed by the
same visible equation prefix and the same true target suffix. This is the basic
control for the shortcut "use the forecast slot to provide recent context
instead of making a forecast."

Under Qwen3-8B and `clip2`, all model lanes beat `bare_B` on the combined
benchmark. Reported SEs are clustered by source paper:

| predictor lane | mean lift | paper-clustered SE | positive rate |
|---|---:|---:|---:|
| GPT-5.5 high | +0.2009 | 0.0062 | 87.3% |
| GPT-5.5 medium | +0.1971 | 0.0063 | 87.1% |
| GPT-5.5 low | +0.1908 | 0.0059 | 86.4% |
| Opus 4.7 medium | +0.1841 | 0.0059 | 85.6% |
| Opus 4.7 low | +0.1777 | 0.0059 | 84.3% |
| GPT-5.5 none | +0.1659 | 0.0062 | 84.2% |
| nano high | +0.1076 | 0.0060 | 66.2% |
| nano medium | +0.1005 | 0.0060 | 64.8% |
| nano low | +0.0796 | 0.0056 | 61.6% |

Kimi K2.6 gives the same qualitative pattern:

| predictor lane | mean lift | paper-clustered SE | positive rate |
|---|---:|---:|---:|
| GPT-5.5 high | +0.1698 | 0.0064 | 81.3% |
| GPT-5.5 medium | +0.1649 | 0.0066 | 82.0% |
| GPT-5.5 low | +0.1584 | 0.0062 | 79.2% |
| Opus 4.7 medium | +0.1533 | 0.0062 | 78.5% |
| Opus 4.7 low | +0.1461 | 0.0061 | 77.2% |
| GPT-5.5 none | +0.1320 | 0.0063 | 74.6% |
| nano high | +0.0763 | 0.0061 | 57.2% |
| nano medium | +0.0695 | 0.0060 | 57.0% |
| nano low | +0.0489 | 0.0058 | 52.2% |

The two scorers differ in absolute scale, but both say the same main thing:
real forecasts carry useful information beyond the same-budget recent-context
control.

The corresponding paper-facing benchmark figure is cached at:

```text
diagnostics/equation_benchmark_figures/
  equation_benchmark_lift_and_adjacent_paired_contrasts.png
```

## Thinking-Effort Ordering

The equation-suffix benchmark also distinguishes model family and
provider-defined reasoning effort. The paired comparisons below use `clip2`,
pair by cut, and cluster standard errors by paper.

Qwen3-8B:

| comparison | paired lift | paper-clustered SE |
|---|---:|---:|
| GPT-5.5 low - none | +0.0250 | 0.0032 |
| GPT-5.5 medium - none | +0.0312 | 0.0034 |
| GPT-5.5 high - none | +0.0350 | 0.0038 |
| GPT-5.5 high - low | +0.0100 | 0.0031 |
| nano high - nano low | +0.0280 | 0.0037 |
| Opus 4.7 medium - Opus 4.7 low | +0.0063 | 0.0021 |

Kimi K2.6:

| comparison | paired lift | paper-clustered SE |
|---|---:|---:|
| GPT-5.5 low - none | +0.0264 | 0.0031 |
| GPT-5.5 medium - none | +0.0329 | 0.0034 |
| GPT-5.5 high - none | +0.0378 | 0.0038 |
| GPT-5.5 high - low | +0.0114 | 0.0032 |
| nano high - nano low | +0.0275 | 0.0036 |
| Opus 4.7 medium - Opus 4.7 low | +0.0072 | 0.0020 |

This is the cleanest "benchmark" story in the artifact: without any human
labels, the task orders weaker and stronger forecast generators in the expected
direction. The result is strongest for none/low/high contrasts and weaker for
adjacent nonzero reasoning-effort levels. Opus 4.7 is included as a separate
predictor family; the medium-low contrast is positive under both scorers but should not be
mixed into every downstream SFT/control analysis, which was built primarily
around the GPT and nano lanes.

## Why `clip2` Is the Headline Metric

Raw logprob is included and remains useful, but raw averages can be dominated
by rare severe local mismatches: a bad TeX token boundary, a delimiter surprise,
or a forecast that is directionally useful but briefly wrong. The headline
metric `clip2` (called `clipLL_2` in the manuscript) floors each target-token
logprob at `-2` before averaging:

```text
score = mean_t max(logprob_t, -2)
```

This is a softened likelihood metric. It still rewards making many target
tokens likely, but it does not allow a few extreme losses to dominate the
example.

The toy equation-ordering diagnostic is a useful mechanism check. It uses tiny
equations such as:

```tex
Z = X + A + B
```

and compares an exact forecast, a reordered forecast, an empty scaffold, a
wrong-symbol forecast, and the `bare_B` context baseline. Both Qwen3-8B and
Kimi K2.6 show the same behavior:

- The exact forecast receives near-perfect likelihood.
- A reordered forecast is penalized at the local mismatch.
- Once the true scored prefix has caught up, the reordered forecast can still
  make the next correct token very likely.
- `clip2` preserves that later usefulness instead of letting the local mismatch
  erase the whole example.

For example, in the Kimi diagnostic for `add_ab`, after the true prefix
`Z = X + A +` has already been seen, the true next token is ` B`. Kimi assigns
probability 0.9913 under the exact forecast, 0.9857 under the reordered
forecast, and 0.6898 with an empty scaffold. At the full-target level, the
reordered forecast beats `bare_B` by +0.7837 `clip2`, while still losing to the
exact forecast.

This is why the clipping experiment is not just a cosmetic choice. It reveals a
plausible scoring principle: count broad, recoverable forecast usefulness while
limiting the damage from local disagreements that the true prefix itself
resolves.

## Static Controls And SFT Controls

The artifact distinguishes three conceptually different controls or scorer
routes:

```text
bare_B control:
  What if Z just spends its budget on recent previous context?

context-only SFT control:
  What if Z spends its budget on recent previous context, and the interaction
  with the scorer has been optimized to make that strategy unusually effective?

real-Z scaffold SFT:
  What if we build the intended frozen likelihood scorer so it understands forecast
  notes as forecast notes?
```

The equation-suffix module includes a severe context-only SFT control on the
first 731-cut construction wave. A Qwen3-8B LoRA is trained on context-only
continuation examples where `Z` is absent, then evaluated on source-disjoint
papers. This is not an intended reward scorer. It is a static adversarial
stress test for the claim that forecast information can beat a strong
context-only shortcut.

On held-out papers, real GPT-5.5 forecasts still beat this context-only SFT
control under `clip2`:

| predictor lane | real-Z minus context-only SFT control | SE | n | positive rate |
|---|---:|---:|---:|---:|
| GPT-5.5 high | +0.0817 | 0.0129 | 220 | 60.5% |
| GPT-5.5 low | +0.0786 | 0.0129 | 220 | 61.8% |
| GPT-5.5 medium | +0.0769 | 0.0128 | 220 | 61.8% |
| GPT-5.5 none | +0.0492 | 0.0125 | 220 | 53.2% |
| nano high | -0.0107 | 0.0131 | 218 | 38.1% |
| nano medium | -0.0215 | 0.0128 | 220 | 34.1% |
| nano low | -0.0344 | 0.0119 | 220 | 31.4% |

This control is intentionally strong and somewhat artificial. It does not prove
RLVR safety. It does show that, for sufficiently strong predictors, the
forecast signal survives a much harder context-only comparison than the
ordinary `bare_B` baseline.

A compact control-ladder figure for GPT-5.5 high under the Qwen3-8B scorer is
cached at:

```text
diagnostics/equation_benchmark_figures/
  equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.png
```

The visible figure text calls this simply the SFT no-forecast control. The
underlying frozen scores come from the source-disjoint test split of the
repo-facing context-only SFT run documented in `docs/SFT_REPRODUCIBILITY.md`.

## Prose/TeX Continuation Follow-Up

The prose/TeX continuation module asks a related but harder question: can
forecast notes help a scorer predict longer technical-paper continuations that
may include prose, notation, definitions, and displayed math?

This setting is not the headline result. The forecast target is much longer,
the possible continuations are less locally constrained, and the measured
effect depends more strongly on how far into `Y` we score.

With an unadapted Qwen scaffold scorer and GPT-5.5 high forecasts, `clip2`
forecast lift is positive but decays with target length:

| comparison | first 100 chars | first 200 chars | first 500 chars | first 1000 chars |
|---|---:|---:|---:|---:|
| forecast Z - scaffold empty | +0.0596 | +0.0480 | +0.0349 | +0.0253 |
| forecast Z - stronger bare context | +0.0375 | +0.0337 | +0.0217 | +0.0135 |

This says the longer-continuation forecasts help locally, but the signal is
less clean than in equation suffixes.

The prose module also includes a compact diagnostic figure built from the
token-level frozen-Qwen scoring. It summarizes `forecast Z - bare_B` over the
first 50, 100, 200, and 400 scored target tokens, with `+/- 2`
paper-clustered SE bars:

```text
modules/prose_continuation/diagnostics/window_lift_figure/
```

The figure shows the same qualitative pattern in a more paper-facing form:
forecast lift is strongest at short scored horizons and decays with length;
GPT-5.5 lanes are clearly above nano lanes; nano shows a visible
thinking-effort gradient; within GPT-5.5, the reasoning-effort ordering is not
clean in this prose/TeX continuation setting.

The prose module also includes SFT route comparisons. When the untrained
forecast scaffold is compared against a direct bare-context SFT control, the
forecast route loses under `clip2`; this is informative but not a fair
same-scorer comparison, because only the context route was trained for the
objective. When both routes are trained with the same clipped objective, the
forecast-scaffold SFT route beats the direct bare-context SFT route at the
short horizon:

```text
Forecast-scaffold clip2 SFT route minus direct bare-context clip2 SFT route

200-char target:
  GPT-5.5 aggregate: raw -0.1198 +/- .0077, clip2 +0.0270 +/- .0023
  nano aggregate:    raw -0.1584 +/- .0087, clip2 +0.0178 +/- .0025

1000-char target:
  GPT-5.5 aggregate: raw -0.2193 +/- .0035, clip2 +0.0041 +/- .0010
  nano aggregate:    raw -0.2420 +/- .0039, clip2 -0.0019 +/- .0010
```

The raw logprob signs in this SFT route comparison should not be overread: the
training objective was based on `clipLL_2` with a small raw
negative-log-likelihood residual. The
headline lesson is that the prose/TeX continuation regime is live but messier:
forecasts help, GPT-5.5 beats nano, and the cleanest signal appears at shorter
scored prefixes.

## Interpretation

The most robust finding is that model forecasts of technical text carry
measurable predictive information for frozen logprob scorers, beyond a
same-budget recent-context baseline. In the equation-suffix regime, this signal
is strong enough to rank model families and thinking-effort settings without
human labels.

The result is especially promising as a pilot benchmark or reward-design
diagnostic:

- It is self-supervised: the true paper text supplies `Y`.
- The predictor can be varied without changing the scorer or the target data.
- The same frozen target scores support many controls.
- The equation-suffix setting gives a clearer signal than broader
  prose-continuation forecasting.

The result should not be presented as a solved RLVR setup. The SFT controls are
static approximations to possible degenerate strategies, not an actual
adversarial training loop. Prompt and scoring choices matter. `clip2` is a
defensible softened likelihood, not a uniquely correct metric.

## Partial Lanes

Partial model-family lanes can be useful as robustness checks, but they should
be reported separately from the combined headline unless they cover the same
cut universe. For example, a lane run only on the first construction wave can show
whether another frontier model family behaves similarly, but it should not be
mixed into the 1363-cut combined model-ordering table without clear labeling.

## Reproducibility Pointers

Useful entry points:

```text
README.md
docs/METHOD.md
docs/ARTIFACTS.md
docs/JUDGE_IDENTITY.md
data/frozen/equation_splits/derived/model_summaries.csv
data/frozen/equation_splits/derived/thinking_comparisons_clip2_paper_clustered.csv
data/frozen/scores/heldout33_softresid_no_z_control/
diagnostics/toy_equation_order_probe/
modules/prose_continuation/
```

The main frozen checks are:

```bash
python scripts/verify_manifest.py
python scripts/reproduce_headlines.py
python scripts/recompute_clip2_from_tokens.py --judge qwen3_8b
python scripts/recompute_clip2_from_tokens.py --judge kimi_k2p6
```
