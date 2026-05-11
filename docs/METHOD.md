# Method Summary

## Task Construction

Each equation-suffix task cuts inside a displayed LaTeX equation from a
technical TeX manuscript. The predictor receives context before the cut and
writes a forecast string `Z`. A frozen likelihood scorer then scores the true
held-out equation suffix `Y` under a prompt that contains the visible equation
prefix and the forecast.

The merged benchmark is built from recent `quant-ph`, `hep-th`, and `math-ph`
arXiv-hosted manuscripts. Source selection used pre-scoring convenience
criteria: recent manuscripts, usually at least 25 pages, technical/equation-rich
style, TeX source availability, and source/cut validation. Selection was not
based on model outputs or downstream scores.

## Main Benchmark Universe

The headline equation universe is the combined 1363-cut benchmark:

```text
data/frozen/equation_splits/data/cuts_all1363.jsonl
```

It was assembled in two construction waves:

```text
first wave (old731): 731 cuts from 74 papers
extension wave (new632): 632 cuts from 64 papers
combined benchmark: 1363 cuts from 138 papers
```

The combined benchmark is the default reporting universe. The construction-wave
labels remain visible in metadata because they preserve provenance and allow
optional checks of hypotheses formed after the first wave and before the
extension. Stable merged joins should use `super_key`, not
`dataset_row_index`; `dataset_row_index` is local to each construction wave.

Within each displayed equation, the cut builder selects relation/operator sites
near the middle of the cleaned equation body, then keeps the nearest site whose
remaining suffix has length 50 to 400 characters. The cut is placed just after
the matched operator, with following whitespace skipped. This makes many tasks
look like completing the right-hand side of an equality or the next line of an
aligned derivation. The predictor prompt includes a coarse target-length hint,
rounded up to the nearest 10 characters.

The selected cuts are not arbitrary adjacent snippets. The builder keeps at
most one cut per displayed equation. When there are more qualifying cuts in a
source manuscript than the per-manuscript quota, it orders cuts by source
position, divides them into buckets, and samples with a fixed seed across those
buckets.

## Scoring

The headline metric is `clip2` (called `clipLL_2` in the manuscript), a
token-level clipped log-likelihood:

```text
score = mean_t max(logprob_t, -2)
```

The artifact also includes robustness tables for several other deterministic
token-level transforms:

```text
raw        = mean_t logprob_t
clipK      = mean_t max(logprob_t, -K), for K in {2,3,5}
sqrt_loss  = mean_t -sqrt(max(-logprob_t, 0))
log1p_loss = mean_t -log(1 + max(-logprob_t, 0))
```

These are not separate scorer calls. They are recomputed from the same frozen
token-level logprobs used for the headline `clip2` result.

For headline lift tables, the main contrast is:

```text
forecast score - same-budget recent-context control score
```

The same-budget recent-context control is `bare_B`: recent raw source context
with the same budget as the forecast slot, followed by the same local equation
prefix and target.

The two frozen scorers in the equation module are Qwen3-8B and Kimi K2.6, both
used through raw completion-logprob interfaces. Qwen3-8B is the primary
smaller-scorer headline; Kimi K2.6 is a larger-model robustness check. See
`JUDGE_IDENTITY.md`.

The merged headline tables report cut-paired model comparisons with
paper-clustered standard errors. This is the default uncertainty estimate for
the combined benchmark.

The all-softening tables in `derived/model_summaries_all_softenings.csv` and
`outputs/headlines/multi_softening_robustness.md` use the same paper-clustered
standard-error convention.

## Controls

The artifact includes static shortcut controls. These are not training loops;
they are offline tests of whether the frozen scoring setup appears to favor
genuine forecast information over simple or learned degeneracies in the
forecasting mechanism.

We use "frozen scorer" in the evaluation-time sense. A scorer may first be
adapted as part of reward-model construction and then frozen before
benchmarking or RLVR-style training. This gives three conceptually different
cases:

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

The core context-only SFT control is scoped to the first 731-cut construction
wave. It trains a Qwen3-8B LoRA continuation model on a bare/context-only
objective, then evaluates it on source manuscripts excluded from SFT training.
Literally, `Z` is absent: the control sees the context and tries to make the
same suffix `Y` likely without receiving a forecast string.

Interpreted as an RLVR stress test, this approximates a predictor that has
learned to use its bounded slot for extra prior context plus scorer-interface
exploitation, improving the scorer's logprobs of `Y` without actually
forecasting the continuation. We score this control outside the forecast
scaffold because the scaffold is part of the intended forecast interface and
empirically tends to handicap context stuffing. The bare-context route is a
harder control: it removes that format penalty and asks whether forecast
information still buys more than an optimized context-only shortcut. The control
is severe and static; it is not a claim that this is the unique fair adversarial
control.

## Prose Continuation Follow-Up

The prose/TeX continuation module extends the same notation to longer
continuations. Those cuts are not equation-suffix tasks, and the control story
is different. The module is included to document what happened in the longer
continuation regime: forecast information helps, full GPT-5.5 clearly beats
nano, but within-GPT thinking-effort ordering is weaker/noisier and more
sensitive to judging choices than in the equation-suffix task.

The prose module should be cited as exploratory unless a write-up explicitly
centers that regime.
