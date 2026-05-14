# Likelihood Scoring for Continuations of Mathematical Text

An automatically generated benchmark for predicting hidden text in technical
papers — code, frozen data, and reproduction scripts.

Companion artifact for the manuscript:

> **Likelihood scoring for continuations of mathematical text: a
> self-supervised benchmark with tests for shortcut vulnerabilities**
>
> [arXiv:2605.10810](https://arxiv.org/abs/2605.10810)

Technical papers offer a natural source of prediction tasks: guessing the
next lines of a derivation, equation, or proof. The manuscript asks whether
such tasks can be assembled into a useful, automatically generated benchmark.

A paper supplies visible context `X` and a hidden continuation `Y`. The model
under evaluation writes an auxiliary string `Z`, intended to help predict `Y`.
A separate language model, used only as a likelihood scorer, then assigns
next-token likelihood to the true `Y` under prompts with and without `Z`. The
benchmark asks whether `Z` improves this likelihood, and compares the forecast
against controls that replace `Z` with nearby context of equal length rather
than a genuine prediction.

This repository contains the frozen data, model generations, token-level
likelihood scores, plotting inputs, and reproduction scripts for the manuscript
results. It is designed to reproduce the numerical claims without making new paid API
calls. Live API scripts are included only as optional smoke tests for provider
interfaces.

## Main Benchmark

The headline benchmark is **equation-suffix prediction**. For each task, we cut
inside a displayed equation in a recent arXiv TeX manuscript. The predictor sees
preceding paper context and the visible equation prefix, then forecasts the
hidden suffix. A frozen scorer assigns likelihood to the true suffix under a
forecast scaffold and under controls.

The merged equation-suffix benchmark contains:

- 1363 automatically selected equation cuts.
- 138 recent physics and mathematics arXiv manuscripts.
- Forecasts from GPT-5.5, Opus 4.7, and GPT-5.4 nano settings.
- Frozen Qwen3-8B and Kimi K2.6 token-level likelihood scores.
- Same-budget context controls and a context-only SFT stress-test control.

The main equation data live here:

```text
data/frozen/equation_splits/
```

The primary headline contrast is:

```text
forecast score - same-budget recent-context control score
```

The primary metric is `clip2` (called `clipLL_2` in the manuscript): a
softened log-likelihood that clips each per-token logprob from below at `-2`
before averaging. This still rewards making target tokens likely, while
preventing a small number of catastrophic local mismatches from erasing an
otherwise useful forecast.

For a narrative summary of the main findings, controls, `clip2`, the toy
equation-ordering diagnostic, and the prose/TeX follow-up, see
`RESULTS_SUMMARY.md`.

## Terminology

- `X`: context before the hidden continuation.
- `Y`: true hidden text being scored.
- `Z`: model forecast string intended to help predict `Y`.
- `bare_B`: same-budget recent-context control.
- `component_bundle`: provenance label in the merged equation rows,
  currently `old731` or `new632`.
- `super_key`: stable merged equation key, `component_bundle:paper_id:cut_id`.
- `clip2`: clipped log-likelihood reward, flooring each target-token logprob
  at `-2` before averaging.

The labels `old731` and `new632` are construction-wave metadata, not separate
benchmark families.

## Repository Map

- `data/frozen/equation_splits/`: main frozen benchmark data, generations, and
  scorer outputs.
- `outputs/headlines/`: reproducible headline tables.
- `diagnostics/equation_benchmark_figures/`: cached paper figures, plotting
  scripts, and figure CSVs.
- `docs/`: scorer identities, manuscript alignment, SFT reproducibility notes,
  and data/release documentation.
- `examples/`: expanded and randomly sampled equation-forecast examples.
- `demo/`: a small single-paper demo path.
- `modules/prose_continuation/`: secondary exploratory prose/TeX continuation
  module.
- `scripts/`: offline reproduction, audit, and live-interface smoke scripts.

The data preserve construction-wave labels such as `component_bundle`,
`old731`, and `new632` for provenance. By default, analyses should target the
combined 1363-cut equation benchmark; the construction-wave labels are for
robustness checks.

## Installation

Requires Python 3.10+ (the pinned development environment uses 3.13).
Dependencies are declared in `pyproject.toml`; an exact lockfile is provided
for both [uv](https://docs.astral.sh/uv/) and pip users.

With uv (recommended):

```bash
uv sync
```

With pip and a venv:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .                       # base deps
pip install -e ".[sft-gpu]"            # optional, for the SFT/GPU path
# or, for an exact match of the development environment:
pip install -r requirements.txt
```

Large frozen data artifacts are tracked with Git LFS:

```bash
git lfs install && git lfs pull
```

## Quick Start

```bash
python scripts/verify_manifest.py
python scripts/reproduce_headlines.py
python scripts/run_fixture_smoke.py
python scripts/recompute_clip2_from_tokens.py --judge qwen3_8b
python scripts/recompute_clip2_from_tokens.py --judge kimi_k2p6
python scripts/build_multi_softening_tables.py
```

The generated headline tables are written to `outputs/headlines/`.

Cached figures from the manuscript, with their plotting scripts and CSV
summaries, are included under:

```text
diagnostics/equation_benchmark_figures/
```

For a concrete walkthrough of equation splits, see `EXAMPLES.md`. For the small
mechanism diagnostic that probes equation ordering and `clip2`, see
`diagnostics/toy_equation_order_probe/`.

For an appendix-style page of randomly sampled equation-forecast examples,
see:

```text
examples/random_equation_forecast_appendix/
```

This folder contains only the final PDF/TeX and a metadata note recording where
each example came from; it omits the scratch rendering scripts.

For a tiny end-to-end single-paper demo, see `demo/`. It bundles one TeX source
file, selects 10 equation suffixes, and by default reads precomputed nano
low/medium generations plus Qwen3-8B `clip2` scores. Optional flags let a user
rerun the paid OpenAI/Fireworks calls.

For exact scorer identity and interface details, including the Fireworks
Qwen3-8B and Kimi K2.6 completion-logprob paths, see
`docs/JUDGE_IDENTITY.md`. For a map from manuscript figures/tables to artifact
files and scripts, see `docs/MANUSCRIPT_ALIGNMENT.md`.

## What This Reproduces

- The merged 1363-cut equation-suffix benchmark.
- Forecast-string lift over the same-budget recent-context control, stored in
  code and data as `bare_B`, under Qwen3-8B and Kimi K2.6 frozen likelihood
  scorers.
- Multi-softening robustness tables for `raw`, `clip2`, `clip3`, `clip5`,
  `sqrt_nll`, and `log1p_nll`, recomputed from frozen token-level logprobs.
- Paired thinking-effort comparisons for GPT-5.5 and GPT-5.4 nano forecasts,
  with paper-clustered standard errors.
- Anthropic Opus 4.7 low/medium predictor lanes in the frozen equation
  headline summaries. These are included for model comparison, but not assumed
  to participate in every downstream SFT/control analysis.
- Opus 4.7 usage diagnostics derived from Anthropic-reported output tokens and
  Anthropic `messages/count_tokens` estimates for the visible forecast text:
  `data/frozen/equation_splits/derived/opus47_usage_anthropic_token_estimates.csv`.
- A context-only SFT control on a source-disjoint subset, showing that GPT-5.5
  forecasts still beat a severe no-forecast continuation baseline under
  `clip2`, while nano forecasts do not.
- A modular prose/TeX continuation SFT follow-up, included as a secondary
  exploratory module.
- A single-paper demo path that exercises the same basic extraction,
  generation, and Qwen scoring shape on 10 cuts from one bundled paper.

## Main Equation Result

On the combined 1363-cut equation benchmark, forecast strings beat the
same-budget recent-context control for every model lane under both frozen
scorers. The benchmark also orders provider-defined reasoning effort in the
expected direction.

For example, under Qwen3-8B and `clip2`, paired model differences are:

```text
gpt55_low    - gpt55_none:   +0.02498 +/- 0.00319
gpt55_medium - gpt55_none:   +0.03122 +/- 0.00343
gpt55_high   - gpt55_none:   +0.03502 +/- 0.00378
gpt55_high   - gpt55_low:    +0.01004 +/- 0.00310
nano_high    - nano_low:     +0.02799 +/- 0.00369
opus47_medium - opus47_low:  +0.00633 +/- 0.00212
```

Kimi K2.6 gives the same qualitative ordering with similar effect sizes. These
standard errors are computed after pairing by cut where applicable and
clustering by paper. Per-lane `forecast Z - bare_B` headline tables also use
paper-clustered standard errors.

The main cached benchmark figure is:

```text
diagnostics/equation_benchmark_figures/
  equation_benchmark_lift_and_adjacent_paired_contrasts.png
```

The corresponding all-softening robustness table is:

```text
outputs/headlines/multi_softening_robustness.md
```

## Context-Only SFT Control

The context-only SFT control is a static stress test, not an RLVR loop. A
Qwen3-8B LoRA is trained on context-only continuation examples where the
forecast string `Z` is absent, then evaluated on source-disjoint held-out
papers. This control was run on the first construction component and should be
read as a held-out shortcut audit, not as the default full-benchmark table.

"Frozen scorer" means frozen during evaluation or hypothetical RLVR use, not
necessarily never adapted during reward-model construction. A scaffold-aware real-Z SFT scorer would be an intended frozen
reward scorer: tune once, on disjoint data, so it understands forecast notes as
forecast notes, then freeze it. By contrast, the context-only SFT control is an
adversarial control: it emulates a degenerate predictor strategy that spends
the side-channel budget on extra previous context and, in effect, has found
prompt-engineering-like ways to make that context unusually useful to the
scorer without providing a genuine forecast.

The headline claim in the manuscript is:

```text
forecast-scaffold score - context-only SFT score, source-disjoint test, clip2

GPT-5.5 lanes: positive by about +0.049 to +0.082 logprob/token.
Nano lanes: negative or near zero.
```

See `docs/SFT_REPRODUCIBILITY.md`.

The cached control-ladder figure is:

```text
diagnostics/equation_benchmark_figures/
  equation_static_control_ladder_with_softresid_sft_test_old731_qwen_gpt55_high.png
```

## Prose Continuation Module

The prose module studies longer technical continuations rather than equation
suffixes. It is exploratory and should not be mixed into the equation headline.
It includes source cut text, paper provenance, forecast and context-route
scorer inputs, SFT score files, generation audits, and local audit scripts.

Main location:

```text
modules/prose_continuation/
```

The prose module now separates the story into three pieces. First, an
unadapted Qwen scaffold scorer, comparable in spirit to the equation-suffix
scorer, shows a clear short-horizon forecast signal whose `clip2` lift decays
from 100 to 1000 scored characters. Second, that untrained scaffold route loses
under `clip2` to a deliberately strong SFT-trained direct bare-context control,
which is informative but not a fair same-scorer comparison. Third, a
scaffold-aware frozen scorer SFT gives the cleaner reward-design test: at a
200-character target window, the forecast-scaffold SFT route beats the direct
bare-context SFT route under `clip2`; at 1000 characters the effect is much
smaller. Raw logprob is negative in that specific comparison, which is coherent
because the SFT objective was based on `clipLL_2` with only a small raw
negative-log-likelihood residual.

## Data Selection

The source-manuscript slate is a documented pre-outcome convenience sample of
recent arXiv-hosted manuscripts from `quant-ph`, `hep-th`, and `math-ph`. The
filters favored long technical manuscripts with TeX source and dense technical
content: equations, definitions, derivations, algorithms, or proofs.

This is not a representative sample of all STEM writing. The point is that,
given a technical TeX-manuscript slate, the tasks are generated automatically.

## Live API Smoke Tests

Headline reproduction does not require live APIs. Optional smoke scripts can
check that provider interfaces still return logprobs/generations in the
expected schema:

```bash
python scripts/live_fireworks_judge_smoke.py --judge qwen3_8b
python scripts/live_fireworks_judge_smoke.py --judge kimi_k2p6
python scripts/live_openai_generation_smoke.py --call
```

These require `FIREWORKS_API_KEY` and/or `OPENAI_API_KEY`. If a hosted
serverless model disappears, the frozen data path remains authoritative.

## Citation

If you use this artifact, please cite:

```bibtex
@misc{ranard2026likelihood,
  title  = {Likelihood scoring for continuations of mathematical text:
            a self-supervised benchmark with tests for shortcut vulnerabilities},
  author = {Ranard, Daniel},
  year   = {2026},
  eprint = {2605.10810},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```

## License

Original code and documentation in this artifact are released under the MIT
License; see `LICENSE`. Third-party paper excerpts, model outputs, and provider
model weights retain their original terms; see `DATA_AVAILABILITY.md` for the
reproducibility scope.
