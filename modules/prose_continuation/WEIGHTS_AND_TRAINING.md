# Weights And Training

Created: 2026-05-03.

## Are The LoRA Weights In This Bundle?

No. This compact bundle intentionally excludes the selected LoRA adapter
weights. The bundle zip is about 5.8 MiB. The two selected-adapter archives are
about 621 MiB and 619 MiB, respectively, so including both would make this a
roughly 1.25 GiB bundle.

The selected adapter archives are local in the source experiment folders:

```text
forecast-scaffold selected adapters:
experiments/2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0/h100_forecast_scaffold_clip2_selected_adapters.tgz
bytes: 651219111
sha256: 4b6fede0456d80b694b35ca678ca2e374f82b74b448b30e061eff5c13d6e5eb0

direct bare-context selected adapters:
experiments/2026-05-03_fresh40_bareB_prose_clip2_sft_x3000_v0/h100_bareB_prose_selected_adapters.tgz
bytes: 649421156
sha256: e578e7f47639514ee03c09b32a98fd7173d52ce61596a36c521dd3a71c55efbd
```

The selected adapter directories are also extracted under each source
experiment's `runs_remote/` folder.

## Forecast-Scaffold LoRA

Purpose: train Qwen3-8B to score the forecast scaffold under a loss
corresponding to `clipLL_2`, symmetric with the direct bare-context control.

Interpretation: this is a candidate scaffold-aware frozen scorer. The SFT is a
reward-model construction step performed on disjoint data; after construction,
the scorer is fixed for evaluation or hypothetical RLVR-style use.

Model:

```text
base model: Qwen/Qwen3-8B
interface: raw completion-style prompt/completion scoring
```

Geometry:

```text
X_base = 2000 chars
X_tail = 2000 chars
Z_budget = 1000 chars
forecast Z = first 1000 chars of model_direct_y_3

prompt:
X_base

% Notes about what's next:
% Z

% Returning to the paper text:
X_tail
Y
```

Training data:

```text
978 train examples = 326 train cuts * 3 nano predictors
975 checkpoint-eval examples = 325 held-out cuts * 3 nano predictors
2277 final eval rows = held-out real-Z rows for GPT-5.5 none/low/medium/high
                       plus nano low/medium/high
train/eval papers are disjoint
```

Objective and hyperparameters:

```text
loss = -clipLL_2 + 0.05 * raw NLL
clipLL_2 = mean_t max(logprob_t, -2.0)
boundary_mode = full_offset

LoRA r = 32
LoRA alpha = 64
LoRA dropout = 0.05
learning rate = 2e-4
batch size = 4
grad accumulation = 4
eval batch size = 4
max length = 8192
gradient checkpointing = on
attention implementation = sdpa
```

Selected checkpoints:

```text
y200:
  run: qwen3_8b_forecast_scaffold_y200_clip2resid005_nanolmh_r32_e4_v0
  selected: checkpoint-epoch-1
  reason: eval worsened after first pass

y1000:
  run: qwen3_8b_forecast_scaffold_y1000_clip2resid005_nanolmh_r32_e2_v0
  selected: checkpoint-epoch-1
  reason: eval worsened after first pass
```

Eval trajectory:

```text
y200:
  epoch 0 objective 0.8028, clip 0.7030, raw 1.9958
  epoch 1 objective 0.8251, clip 0.7139, raw 2.2231

y1000:
  epoch 0 objective 0.7672, clip 0.6677, raw 1.9909
  epoch 1 objective 0.7808, clip 0.6783, raw 2.0491
```

## Direct Bare-Context LoRA

Purpose: train a direct continuation control on the strongest simple
recent-context control available in this prose/TeX regime.

Interpretation: this is not an intended reward scorer. It is a charitable
context-control SFT: a proxy for a non-forecast strategy that uses the forecast
budget as extra previous context and optimizes its interaction with the scorer
to improve continuation likelihood.

Model:

```text
base model: Qwen/Qwen3-8B
interface: raw completion-style prompt/completion scoring
```

Geometry:

```text
prompt = 3000 contiguous chars before target
       = 2000-char local context + 1000 extra chars matching Z budget
no scaffold
```

Training data:

```text
326 train cuts from 20 papers
325 eval cuts from 20 held-out papers
train/eval papers are disjoint
```

Objective and hyperparameters:

```text
loss = -clipLL_2 + 0.05 * raw NLL
clipLL_2 = mean_t max(logprob_t, -2.0)
boundary_mode = full_offset

LoRA r = 32
LoRA alpha = 64
LoRA dropout = 0.05
learning rate = 2e-4
batch size = 4
grad accumulation = 4
eval batch size = 4
max length = 8192
attention implementation = sdpa
```

Selected checkpoints:

```text
y200:
  run: qwen3_8b_bareB_y200_softresid005_r32_e8_v0
  selected: checkpoint-epoch-1
  reason: eval worsened after first pass

y1000:
  run: qwen3_8b_bareB_y1000_softresid005_r32_e8_v0
  selected: checkpoint-epoch-1
  reason: eval worsened after first pass
```

## Source Training Docs

Training and scoring scripts are in:

```text
scripts/
```

The full source experiment folders contain the pulled H100 logs, score
artifacts, tokenizer files, selected checkpoints, and adapter archives. The
construction-time H100 handoff notes are archived outside the public artifact
under the wrapper-level `meta_notes/` folder.
