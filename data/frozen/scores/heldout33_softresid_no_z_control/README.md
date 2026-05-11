# Soft-Residual Context-Only SFT Control

Added: 2026-05-01

This subartifact records the repo-facing clip2 context-only SFT control. In
the underlying file names this is sometimes called the `no_z` control because
the forecast string `Z` is absent. The control is intentionally strong because
Qwen3-8B is fine-tuned for that context-only continuation task before being
compared with real forecast strings.

The purpose is a static RLVR-readiness test. We are not running an RLVR loop
here; instead, we ask whether the frozen reward would plausibly resist simple
or learned degeneracies in the forecasting mechanism. In this control, the
scorer/consumer is frozen at evaluation time, while the context-only pathway has been
trained to improve likelihood of `Y` without supplying a forecast. This is a
proxy for a predictor that spends a bounded side-channel on extra previous
context and scorer-interface exploitation, rather than genuinely predicting the
continuation.

This is conceptually different from a scaffold-aware real-Z SFT scorer. A
scaffold-aware scorer SFT is an intended reward-model construction step: train on
disjoint forecast-scaffold examples so the scorer understands forecast notes as
forecast notes, then freeze it. The context-only SFT is instead a
charitable adversarial control: it asks how well a non-forecast shortcut could
do if its interaction with the scorer had been optimized.

The directory label `heldout33` means approximately one-third paper holdout. It
is a compact path label, not a separate dependency on historical run folders.

## Why This Control Is Severe

The context-only control directly fine-tunes the Qwen3-8B consumer on bare-B raw
equation-suffix continuation. A future RLVR predictor would not get to modify
the scorer/consumer weights; it would only write a bounded `Z` string into a
frozen context. So this is an aggressive static stress test in the control's
favor.

The control is scored outside the forecast scaffold on purpose. For real
forecasts, the scaffold is the intended interface. For a context-only control,
putting previous context inside "forecast notes" can be an artificial handicap:
the model may treat it as guesses rather than ordinary preceding text. The
bare-B route removes that format penalty and is therefore the stronger
context-stuffing control.

That makes the result especially useful: if real `Z` beats this control on
source manuscripts excluded from SFT training, the benefit is hard to dismiss as
scaffold repair, boundary familiarity, or recent-context paste.

## Split

The split is deterministic and source-manuscript-level:

```text
data_holdout33_seed20260501_v0/

seed: 20260501
train: 42 papers, 3188 examples, 363 real-Z-overlap examples
eval:   7 papers,  496 examples,  67 real-Z-overlap examples
test:  25 papers, 1484 examples, 220 real-Z-overlap examples
```

Use the `test` split for the main result.

## Training

Fresh base `Qwen/Qwen3-8B` LoRA:

```text
runs_remote/qwen3_8b_holdout33_softresid005_r32_e2_lr2e4_v0/

objective: hard_clip2 + 0.05 * raw_NLL
boundary_mode: full_offset
epochs: 2
lr: 2e-4
LoRA: r32 alpha64
batch: 4, grad_accum: 4
eval/save every 50 steps
```

Eval `clip2` curve:

```text
step  50: 0.39288
step 100: 0.39201
step 150: 0.39196
epoch 1:  0.38933
step 200: 0.38947
step 250: 0.39059
step 300: 0.38816
step 350: 0.38790
epoch 2:  0.38794
```

The final adapter was essentially tied with the best eval checkpoint and
slightly stronger on the source-disjoint real-Z-overlap scoring, so the final-adapter
comparison is the headline.

## Result

Paired test comparison on source manuscripts excluded from SFT training:

```text
real-Z scaffold score - context-only SFT score, clip2

gpt55_high    +0.0817 +/- 0.0129   n=220   pos=0.605
gpt55_low     +0.0786 +/- 0.0129   n=220   pos=0.618
gpt55_medium  +0.0769 +/- 0.0128   n=220   pos=0.618
gpt55_none    +0.0492 +/- 0.0125   n=220   pos=0.532
nano_high     -0.0107 +/- 0.0131   n=218   pos=0.381
nano_medium   -0.0215 +/- 0.0128   n=220   pos=0.341
nano_low      -0.0344 +/- 0.0119   n=220   pos=0.314
```

Interpretation: GPT-5.5 real forecasts beat even this aggressive context-only
SFT control on source manuscripts excluded from SFT training, while nano
forecasts do not.

## Included Files

- `data_holdout33_seed20260501_v0/`: split data and manifest.
- `runs_remote/.../metrics.jsonl`: training/eval metric trace.
- `runs_remote/.../run_config.json`: training configuration.
- `runs_remote/.../test_realz_overlap_final_adapter_full_offset/`: final-adapter test bare-B scores.
- `runs_remote/.../test_realz_overlap_checkpoint_step350_full_offset/`: best-eval-checkpoint test bare-B scores.
- `runs_remote/.../test_realz_vs_final_adapter_full_offset_comparison`: paired real-Z-vs-final-adapter comparison JSON.
