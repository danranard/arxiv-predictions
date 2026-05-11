# Prose Continuation SFT Results

Last updated: 2026-05-03

This note tracks the non-equation prose-continuation line, especially the
fresh40 scaffold-aware Qwen3-8B SFT experiments. Keep this separate from
`EQUATION_SPLIT_RESULTS.md`: equation suffixes are a short-horizon,
budget-matched symbolic task; this note is about longer prose/TeX continuation
forecasting with `X`, auxiliary `Z`, and held-out continuation `Y`.

## Current Setup

The most recent SFT experiments use the fresh40 prose-continuation scaffold:

```text
X_base = 2000 chars
X_tail = 2000 chars
Z_budget = 1000 chars
target = Y_body
boundary handling = full_offset
base scorer = Qwen/Qwen3-8B
primary SFT loss = raw target-token NLL
```

The canonical experiment folder is:

```text
experiments/2026-05-02_fresh40_scaffold_judge_sft_nanolow_xb2000_xtail2000_z1000_v0/
```

The main local run notes are:

```text
experiments/2026-05-02_fresh40_scaffold_judge_sft_nanolow_xb2000_xtail2000_z1000_v0/RUN_NOTES.md
```

Relevant companion folders:

```text
experiments/2026-05-02_fresh40_scaffold_judge_sft_nano_lmh_xb2000_xtail2000_z1000_v0/
experiments/2026-05-02_fresh40_scaffold_judge_sft_prevctx_xb2000_xtail2000_z1000_v0/
```

All key GPU artifacts from the 2026-05-02 H100 session were copied back
locally, including adapters, metrics, score CSVs, summaries, and run logs.

## Narrative Arc

For write-up purposes, the prose/TeX continuation module is clearest if read in
three steps:

```text
1. Frozen untrained scaffold scorer.
   This is the closest analogue of the equation-split setup: unadapted Qwen3-8B,
   no scorer SFT, forecast scaffold, clip2, and prefix windows of Y. GPT-5.5 high
   beats both scaffold-empty and the stronger same-budget recent-context
   control, but the lift decays from 100 to 1000 scored characters.

2. SFT-trained adversarial context control.
   The untrained scaffold route loses under clip2 to the deliberately strong
   direct bare-context SFT control. This is informative but not exactly a fair
   same-scorer match: the control route is trained for the clipped continuation
   objective, while the scaffold route is still untrained.

3. Scaffold-aware frozen scorer.
   The forecast-scaffold SFT is a candidate reward-scorer construction step:
   tune on disjoint data so the scorer understands forecast notes, freeze it,
   and then compare to the context-control route.
```

The context-control SFT should be read as "extra previous context plus
scorer-interface exploitation," not as an intended reward model.

## Why We Tried SFT

Earlier frozen-scorer prose-continuation experiments showed useful signal under
softened objectives such as `clip2`, but raw full-body logprob was often
dominated by boundary/scaffold brittleness and a few very bad tokens. The
working idea was:

```text
fine-tune the scorer to understand the scaffold -> freeze it -> use raw logprob
```

So for these SFT experiments, raw logprob should be treated as the more
principled primary metric. `clip2` remains diagnostically useful, but it should
not automatically become the headline metric once the scorer has been trained on
the interface.

## Frozen-Scorer Prefix Windows

The non-SFT Qwen3-8B scorer also gives a useful regime-comparison view if the
long prose/TeX continuation task is scored like the equation-split task: use
`clip2`, keep the scorer frozen, and evaluate only the first 100/200/500/1000
characters of the target. This should be read as a short-to-medium-horizon
technical-continuation prefix benchmark, not as an equation-suffix benchmark:
the fresh40 cuts are general mid-block TeX cuts, not deliberate cuts inside
display equations.

On the full available `X_base=2000`, `X_tail=2000`, `Z_budget=1000` scored
batch, forecast `Z` is the first 1000 chars of `model_direct_y_3`. In this
setting, the stronger `bare_x_base_plus_z` control is a plain continuation
control with 3000 contiguous pre-target characters: the ordinary 2000-char
local context plus an extra 1000 chars of immediately preceding context, equal
to the forecast side-channel budget. Forecast `Z` beats scaffold-empty strongly
and the lift decays smoothly with prefix length:

```text
Forecast Z - scaffold_empty, clip2

                 100 chars           200 chars           500 chars           1000 chars
gpt55 none     +0.0586 +/- .0043   +0.0472 +/- .0031   +0.0329 +/- .0018   +0.0237 +/- .0011
gpt55 low      +0.0605 +/- .0045   +0.0476 +/- .0032   +0.0337 +/- .0019   +0.0248 +/- .0011
gpt55 medium   +0.0578 +/- .0044   +0.0458 +/- .0031   +0.0354 +/- .0019   +0.0264 +/- .0012
gpt55 high     +0.0596 +/- .0044   +0.0480 +/- .0031   +0.0349 +/- .0018   +0.0253 +/- .0011

nano low       +0.0235 +/- .0038   +0.0193 +/- .0026   +0.0138 +/- .0014   +0.0103 +/- .0009
nano medium    +0.0265 +/- .0036   +0.0222 +/- .0026   +0.0157 +/- .0014   +0.0114 +/- .0009
nano high      +0.0337 +/- .0040   +0.0255 +/- .0027   +0.0184 +/- .0015   +0.0133 +/- .0009
```

Against the stronger 3000-char `bare_x_base_plus_z` budget control, GPT-5.5
forecast notes still win across all windows, while nano is weak and
near-neutral at longer windows:

```text
Forecast Z - bare_x_base_plus_z, clip2

                 100 chars           200 chars           500 chars           1000 chars
gpt55 none     +0.0360 +/- .0044   +0.0328 +/- .0032   +0.0197 +/- .0020   +0.0119 +/- .0013
gpt55 low      +0.0379 +/- .0046   +0.0332 +/- .0033   +0.0205 +/- .0020   +0.0131 +/- .0013
gpt55 medium   +0.0352 +/- .0046   +0.0314 +/- .0032   +0.0223 +/- .0021   +0.0146 +/- .0014
gpt55 high     +0.0375 +/- .0045   +0.0337 +/- .0032   +0.0217 +/- .0021   +0.0135 +/- .0014

nano low       +0.0011 +/- .0039   +0.0050 +/- .0028   +0.0005 +/- .0018   -0.0014 +/- .0012
nano medium    +0.0041 +/- .0037   +0.0080 +/- .0027   +0.0024 +/- .0018   -0.0002 +/- .0012
nano high      +0.0113 +/- .0040   +0.0113 +/- .0028   +0.0051 +/- .0018   +0.0017 +/- .0012
```

Interpretation: prose/TeX continuations are not simply failed long-body
forecasting. There is a clear local predictive signal under a frozen scorer,
but it dilutes as the target window grows. The stronger budgeted-context
control eats most of the nano signal but not the GPT-5.5 signal, suggesting
that strong forecast `Z` contains information beyond recent-context stuffing.

## Direct Bare-Context SFT Control

On 2026-05-03 we trained a separate direct-continuation `bare_B` control on an
H100. This is different from the scaffold-aware controls above: there is no
`Z` scaffold at all. The control prompt is simply the last 3000 characters
before the target, equal to the 2000-character local context plus an extra
1000 characters matching the forecast side-channel budget.

Conceptually, this is not an alternative intended reward scorer. It is a
charitable stress test for a degenerate predictor strategy: spend the `Z`
budget on extra previous context and exploit the scorer interface so that this
context makes the true continuation higher-likelihood without supplying a
genuine forecast. We use a bare-context route because wrapping previous context
inside the forecast-note scaffold appears to handicap context stuffing; the
plain continuation route is the stronger control.

The split was by paper:

```text
train: 326 cuts from 20 papers
eval:  325 cuts from 20 papers
```

This is useful but small. Both direct-context SFTs overfit quickly enough that
the best held-out checkpoint was the first checkpoint, after one pass through
the training set:

```text
y1000 objective, eval after first pass:
  objective 0.7600, clip 0.6715, raw NLL 1.7717

y200 objective, eval after first pass:
  objective 0.8148, clip 0.7166, raw NLL 1.9638
```

Later epochs worsened held-out objective/raw NLL, so the final comparisons use
the selected best checkpoints rather than the final epoch. A no-adapter GPU
sanity check matched the saved Qwen3-8B/Fireworks scores on 20 exact rows to
about `0.001` mean absolute logprob, with max raw discrepancy about `0.0045`.

We then scored the real forecast scaffold under the validated Qwen3-8B path
on the same held-out cuts and compared it route-wise against the SFT'd
direct-context control. This is a conservative stress test, not a same-scorer
comparison:

```text
real forecast route:
  Qwen3-8B scores X + forecast Z + X_tail scaffold

context-control route:
  SFT'd Qwen scores bare 3000-char pre-target context
```

The forecast-scaffold SFT results below should be read differently: a
scaffold-aware SFT scorer is a candidate frozen reward scorer, tuned on disjoint
data to understand forecast notes as forecast notes and then frozen. The
bare-context SFT is a pushed non-forecast control.

Using raw logprob, real forecasts survive this SFT'd bare-context control:

```text
Forecast route - SFT bare_B context route, raw logprob

200-char target, y200-trained control:
gpt55 none     +0.0893 +/- .0164
gpt55 low      +0.0984 +/- .0167
gpt55 medium   +0.0879 +/- .0161
gpt55 high     +0.1038 +/- .0160

1000-char target, y1000-trained control:
gpt55 none     +0.2199 +/- .0074
gpt55 low      +0.2208 +/- .0078
gpt55 medium   +0.2224 +/- .0077
gpt55 high     +0.2251 +/- .0076
```

Nano forecasts also beat this direct-context SFT control in raw, but with
smaller margins:

```text
200-char target:  +0.0683 to +0.0782
1000-char target: +0.2010 to +0.2061
```

Under `clip2`, however, the SFT'd bare-context control wins:

```text
GPT-5.5, 200-char target:  -0.0473 to -0.0428
GPT-5.5, 1000-char target: -0.0619 to -0.0600
```

Interpretation: this control behaves as expected for a clip2-trained
direct-continuation model. If the post-SFT evaluation metric is raw logprob,
real-Z survives strongly. If the metric remains `clip2`, then the direct
context-control route wins, which is not shocking because the control was
explicitly optimized for a clip2-heavy objective. This reinforces that the
choice between raw and softened scoring is part of the experimental design,
not an innocuous reporting detail.

## Fixed Forecast-Scaffold Judge

Under the canonical nano-low forecast-scaffold SFT, GPT-5.5 forecast `Z` beats
the strong bare context control in raw and `clip2`. Against
`bare_x_base_plus_z::control`:

```text
gpt55_medium: clip2 +0.0097 +/- 0.0013, raw +0.0055
gpt55_high:   clip2 +0.0094 +/- 0.0013, raw +0.0058
gpt55_low:    clip2 +0.0094 +/- 0.0013, raw +0.0042
gpt55_none:   clip2 +0.0083 +/- 0.0013, raw +0.0044
nano_high:    clip2 +0.0035 +/- 0.0012, raw -0.0076
nano_low:     clip2 +0.0018 +/- 0.0011, raw -0.0105
```

Against the budgeted previous-context scaffold control:

```text
gpt55_medium: clip2 +0.0059 +/- 0.0013, raw +0.0062
gpt55_high:   clip2 +0.0056 +/- 0.0012, raw +0.0065
gpt55_low:    clip2 +0.0055 +/- 0.0012, raw +0.0048
gpt55_none:   clip2 +0.0044 +/- 0.0012, raw +0.0051
nano_high:    clip2 -0.0004 +/- 0.0011, raw -0.0069
nano_low:     clip2 -0.0021 +/- 0.0011, raw -0.0098
```

Interpretation: with one fixed forecast-aware scorer, GPT-5.5 forecasts carry
real predictive information, and weak nano forecasts remain weak. This is the
cleanest "is there signal?" result for this prose-continuation SFT line.

## Higher-Volume Forecast SFT

The nano-low/medium/high forecast-Z SFT trained on more weak-model forecast
notes. It preserved the main separation:

```text
vs bare_x_base_plus_z::control
gpt55_medium: clip2 +0.0098 +/- 0.0013, raw +0.0047
gpt55_high:   clip2 +0.0095 +/- 0.0013, raw +0.0047
gpt55_low:    clip2 +0.0089 +/- 0.0013, raw +0.0027
gpt55_none:   clip2 +0.0081 +/- 0.0013, raw +0.0030
nano_high:    clip2 +0.0046 +/- 0.0012, raw -0.0078
nano_medium:  clip2 +0.0028 +/- 0.0011, raw -0.0099
nano_low:     clip2 +0.0030 +/- 0.0011, raw -0.0103
```

This suggests the scorer did not simply learn to reward any predictor-style
note. GPT-5.5 forecast notes remain better than nano notes; nano raw lift stays
negative.

## Context-Tuned Scorers And Controls

We also trained context-only variants to probe adversarial controls.

### Same Context-Tuned Judge

If the scorer is trained on budgeted previous-context `Z` and then that same
scorer compares forecast `Z` against previous-context `Z`, GPT-5.5 forecasts
lose in raw logprob:

```text
raw forecast minus once-tuned context control
gpt55_high:   -0.0031 +/- 0.0028
gpt55_medium: -0.0034 +/- 0.0029
gpt55_low:    -0.0045 +/- 0.0028
gpt55_none:   -0.0044 +/- 0.0029
```

This is not very surprising: the scorer has been trained to treat the `Z` slot
as previous context, so true previous-context `Z` is native to that scorer and
forecast `Z` is relatively out-of-distribution. Under `clip2`, forecasts do
beat the same context-tuned control, but this is a stranger result if the SFT
plan is to use raw logprob as the primary post-SFT metric.

### Route-Wise Charitable Stress Test

The more adversarial-control-flavored comparison was:

```text
forecast route:
  forecast Z scored by the ordinary once-tuned forecast-scaffold scorer

context route:
  budgeted previous-context Z scored by a further context-tuned scorer
```

The further context-tuned scorer starts from the canonical forecast-scaffold
adapter and then trains for 3 more epochs on the previous-context scaffold. It
is deliberately a pushed/charitable context-control route, using the extra
`Z_budget` chars immediately before `X_tail` rather than repeating `X_base` or
`X_tail`.

Training/eval trajectory:

```text
epoch 0 eval: raw 1.3226, clip2 0.7611
epoch 1 eval: raw 1.3306, clip2 0.7522
epoch 2 eval: raw 1.3343, clip2 0.7521
```

So the pushed context-control tune was approximately done for the clipped
context-control objective: `clip2` improved and then plateaued, while raw NLL
worsened after the first epoch.

In the route-wise comparison, GPT-5.5 forecasts beat the twice-tuned context
route in raw logprob:

```text
raw forecast/control minus twice-tuned context
gpt55_high:   +0.0086 +/- 0.0029, about 3.0 SE
gpt55_medium: +0.0084 +/- 0.0030, about 2.8 SE
gpt55_none:   +0.0073 +/- 0.0030, about 2.4 SE
gpt55_low:    +0.0070 +/- 0.0029, about 2.4 SE
nano_high:    -0.0045 +/- 0.0028
```

Under `clip2`, however, the twice-tuned context route roughly ties GPT-5.5:

```text
clip2 forecast/control minus twice-tuned context
gpt55_medium: +0.0006 +/- 0.0013
gpt55_high:   +0.0003 +/- 0.0013
gpt55_low:    +0.0003 +/- 0.0013
gpt55_none:   -0.0008 +/- 0.0013
nano_high:    -0.0055 +/- 0.0012
```

Interpretation: the route-wise raw result is encouraging because even a
charitably tuned context-stuffing route does not dominate strong forecasting.
But it is a stress test, not the cleanest main benchmark, because it compares
scores from two different tuned scorers.

## High Versus Medium

Across these prose-continuation experiments, GPT-5.5 variants reliably beat
nano variants, but intra-GPT-5.5 ordering is not settled. Medium often edges
out high/low/none by a tiny amount, while high sometimes looks flat or slightly
worse. The high-medium gap is usually similar in size to the standard error.

Working hypothesis: high-effort continuations may be semantically polished but
commit to a locally plausible alternate continuation, which exact logprob
scorers penalize. Treat this as unresolved/noisy until the scorer, metric,
scaffold, and data split are locked.

## Current Takeaway

Do not collapse these experiments into one scoreboard. They answer different
questions:

1. **Fixed forecast-scaffold scorer:** forecast `Z` clearly carries real signal.
2. **Same context-tuned scorer:** previous-context controls can win raw when the
   scorer is trained to treat `Z` as context.
3. **Route-wise charitable stress test:** even a pushed context-control route
   does not obviously dominate strong GPT-5.5 forecasting; under raw logprob,
   GPT-5.5 forecasts still win by roughly `+0.007` to `+0.009` mean logprob.
4. **Symmetric clip2-route test:** when both the forecast route and direct
   context route receive analogous `clip2 + 0.05 raw` SFT, GPT-5.5 forecast
   notes beat direct bare context under `clip2`, especially for 200-character
   targets.

For a paper/benchmark story, the fixed-scorer result is the clean primary
evidence. For RLVR hackability, the route-wise charitable comparison is a useful
stress test, but it remains sensitive to SFT volume, SFT duration, the chosen
metric, and the exact definition of the adversarial context control.

## Forecast-Scaffold Clip2 SFT

On 2026-05-03 we ran the symmetric `clipLL_2`-route experiment:

```text
forecast route:
  Qwen3-8B LoRA trained on nano-low/medium/high forecast scaffolds
  objective = -clipLL_2 + 0.05 * raw NLL
  eval = real forecast Z from GPT-5.5 and nano variants

context route:
  direct bare-context Qwen3-8B LoRA trained with the same clip2-style objective
  eval = 3000-char contiguous pre-target context
```

This fixes the asymmetry in the earlier direct `bare_B` stress test, where the
context route had clip2-style SFT and the forecast route did not. The forecast
run used the same `X_base=2000`, `X_tail=2000`, `Z_budget=1000` geometry as the
main prose-continuation batch, with forecast `Z` truncated to 1000 characters.

Both forecast-scaffold target-window adapters selected the first checkpoint by
held-out nano-LMH objective; the second pass was already worse:

```text
y200:
  epoch 0 objective 0.8028, clip 0.7030, raw 1.9958
  epoch 1 objective 0.8251, clip 0.7139, raw 2.2231

y1000:
  epoch 0 objective 0.7672, clip 0.6677, raw 1.9909
  epoch 1 objective 0.7808, clip 0.6783, raw 2.0491
```

Clean route-wise comparison against the direct bare-context clip2 SFT control:

```text
Forecast-scaffold clip2 SFT route minus direct bare-context clip2 SFT route

200-char target:
  GPT-5.5 aggregate: raw -0.1198 +/- .0077, clip2 +0.0270 +/- .0023
  nano aggregate:    raw -0.1584 +/- .0087, clip2 +0.0178 +/- .0025

1000-char target:
  GPT-5.5 aggregate: raw -0.2193 +/- .0035, clip2 +0.0041 +/- .0010
  nano aggregate:    raw -0.2420 +/- .0039, clip2 -0.0019 +/- .0010
```

Per-model GPT-5.5 `clip2` deltas:

```text
200 chars:
gpt55 none     +0.0261 +/- .0049
gpt55 low      +0.0256 +/- .0049
gpt55 medium   +0.0278 +/- .0045
gpt55 high     +0.0285 +/- .0044

1000 chars:
gpt55 none     +0.0036 +/- .0019
gpt55 low      +0.0039 +/- .0020
gpt55 medium   +0.0044 +/- .0019
gpt55 high     +0.0046 +/- .0019
```

Audit status for this comparison:

```text
source artifacts:
  forecast SFT:
    experiments/2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0/
  direct bare-context SFT:
    experiments/2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0/

train/eval split:
  forecast SFT train = 978 rows = 326 cuts * 3 nano predictors, 20 papers
  forecast eval-all = 2277 rows, 20 held-out papers
  direct bare-context train = 326 cuts, 20 papers
  direct bare-context eval = 325 cuts, 20 held-out papers
  no train/eval paper overlap in either route
  no train/eval cut overlap in either route

joined comparison:
  join key = (paper_id, cut_id), not cut_id alone
  joined rows = 4530 = 2265 rows at y200 + 2265 rows at y1000
  no null predictor labels
  no duplicate (window, predictor_model, paper_id, cut_id) keys
  target strings match exactly between routes on every joined row
  target windows are exactly 200 and 1000 chars
  both forecast and bare-context scores use boundary_mode = full_offset
```

The joined comparison is intentionally an intersection comparison. The
forecast eval file has slightly broader model-row coverage than the direct
`bare_B` eval file: GPT-5.5 none/low/medium each have 323 matched cuts,
GPT-5.5 high has 321, and nano low/medium/high each have 325. Unmatched
forecast rows are dropped rather than imputed.

Interpretation: once the forecast route gets the same style of clipped SFT,
GPT-5.5 forecast notes beat the direct bare-context SFT control under `clip2`,
especially on the 200-character window. Raw logprob goes negative in this
particular comparison, which is coherent rather than mysterious: both routes
were optimized for a clipped objective with only a small raw residual.

Bookkeeping note: the local comparison script was corrected to join forecast
and control rows on `(paper_id, cut_id)`, not `cut_id` alone. `cut_id` is only
unique within a paper.

Bundled artifact:

```text
bundles/2026-05-03_prose_continuation_sft_clip2_v1/
bundles/2026-05-03_prose_continuation_sft_clip2_v1.zip
```

The bundle includes scorer-input JSONL, source score CSVs, joined comparisons,
the audit summary, and generation/prompt sample audits. It excludes the large
LoRA adapter weights, which remain in the source experiment folders.
