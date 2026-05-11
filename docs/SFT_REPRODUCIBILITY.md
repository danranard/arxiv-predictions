# Context-Only SFT Control Reproducibility

The repo-facing SFT result is the soft-residual context-only control:

```text
data/frozen/scores/heldout33_softresid_no_z_control/
```

The `heldout33` directory label means approximately one-third paper holdout; it
is kept only as a compact path label.

This control fine-tunes `Qwen/Qwen3-8B` as a context-only continuation model:
the forecast string `Z` is absent, so the model learns the strongest
no-forecast baseline we test here. It then asks whether real forecast strings
still improve the frozen score on source manuscripts held out from SFT
training.

The motivation is static RLVR-readiness, not an actual RLVR run. The ordinary
equation benchmark uses unchanged frozen likelihood scorers. This SFT control is
different and intentionally adversarial: it stands in for a learned degeneracy in the
forecasting mechanism, where a predictor spends its bounded side-channel on
extra previous context and prompt-engineering-like interaction with the scorer
rather than on a genuine forecast. Real `Z` beating this control is evidence
that the reward is not merely paying for recent-context paste, scaffold repair,
boundary familiarity, or other easy adaptations.

This should not be confused with a scaffold-aware real-Z SFT scorer. That would
be a candidate reward-model construction step: tune the scorer on disjoint data
so it understands `X + forecast Z + return-to-paper + score Y`, then freeze it
for benchmarking or RLVR-style use. The context-only SFT control here has a
different role: it is a hard negative control meant to emulate an optimized
non-forecast shortcut.

The headline comparison is not over all 731 benchmark rows. It is over the
source-disjoint SFT test rows that also overlap the real-Z scored universe:
`n=220` for the GPT-5.5 lanes, `n=220` for nano low/medium, and `n=218` for
nano high.

This SFT control is intentionally scoped to the first 731-cut construction
wave. The merged 1363-cut equation module is now the default benchmark for
forecast lift and model-comparison tables, but the context-only SFT result
should still be read as a first-wave source-disjoint stress test.

## Reproducibility Tiers

### Tier 1: Frozen-Score Reproduction

This is the default project-artifact promise. It requires no GPU and no paid API.
The artifact includes:

- paper-level train/test split data;
- training configuration;
- training/eval metric trace;
- frozen test adapter scores;
- paired real-Z-vs-adapter comparison JSON.

Running `scripts/reproduce_headlines.py` reproduces the table
`noz_sft_control.md` from these frozen score files.

### Tier 2: Adapter Rescore

This checks the scoring path, but requires `Qwen/Qwen3-8B`, CUDA hardware, and
the LoRA adapter weights. The final adapter is about 349 MB, so it may be
distributed as a Git LFS object or release asset rather than in the small code
checkout.

Install the GPU-side dependencies on a CUDA/PyTorch image:

```bash
python -m pip install -r requirements_sft_gpu.txt
```

The requirements file intentionally does not pin or install `torch`; use the
CUDA build that comes with the GPU image unless you know you need to replace it.

Expected command shape:

```bash
python scripts/score_qwen3_lora_completion.py \
  --model-name Qwen/Qwen3-8B \
  --adapter-path path/to/final_adapter \
  --examples-jsonl data/frozen/scores/heldout33_softresid_no_z_control/data_holdout33_seed20260501_v0/selected_examples.jsonl \
  --keys-json data/frozen/scores/heldout33_softresid_no_z_control/data_holdout33_seed20260501_v0/realz_scored_731_keys.json \
  --split test \
  --boundary-mode full_offset \
  --output-dir outputs/sft_rescore_check
```

Then compare against:

```text
data/frozen/scores/heldout33_softresid_no_z_control/runs_remote/
  qwen3_8b_holdout33_softresid005_r32_e2_lr2e4_v0/
    test_realz_overlap_final_adapter_full_offset/
```

This should match closely. Exact bitwise identity is not the promise across GPU
libraries, CUDA versions, and attention implementations.

To recompute the paired comparison after rescoring:

```bash
python scripts/compare_realz_to_adapter_scores.py \
  --adapter-scores outputs/sft_rescore_check/completion_scores.csv \
  --fireworks-token-scores data/frozen/scores/small_qwen_current_full731/combined_target_token_logprobs.csv \
  --output outputs/sft_rescore_check/realz_vs_adapter_paired_summary.json
```

### Tier 3: Full Retrain

This checks whether the training recipe itself recovers the result. It requires
a GPU large enough for Qwen3-8B LoRA training. The recorded run used H100-class
hardware.

The exact recorded configuration is also saved in:

```text
data/frozen/scores/heldout33_softresid_no_z_control/runs_remote/
  qwen3_8b_holdout33_softresid005_r32_e2_lr2e4_v0/run_config.json
```

Expected command shape:

```bash
python scripts/train_qwen3_8b_clip2_lora.py \
  --model-name Qwen/Qwen3-8B \
  --train-jsonl data/frozen/scores/heldout33_softresid_no_z_control/data_holdout33_seed20260501_v0/train_completion.jsonl \
  --eval-jsonl data/frozen/scores/heldout33_softresid_no_z_control/data_holdout33_seed20260501_v0/eval_completion.jsonl \
  --output-dir outputs/sft_retrain_check \
  --boundary-mode full_offset \
  --loss-mode clip_plus_residual \
  --clip-nll 2.0 \
  --residual-nll-weight 0.05 \
  --epochs 2 \
  --batch-size 4 \
  --eval-batch-size 16 \
  --grad-accum-steps 4 \
  --lora-r 32 \
  --lora-alpha 64 \
  --learning-rate 2e-4 \
  --max-length 1024 \
  --eval-every 50 \
  --save-every 50 \
  --log-every 10 \
  --seed 20260501 \
  --bf16 \
  --gradient-checkpointing
```

The trainer writes:

- `run_config.json`
- `metrics.jsonl`
- periodic `checkpoint-step-*` LoRA adapters if `--save-every` is set;
- `final_adapter/`.

Retraining is not expected to be bitwise reproducible. Reasonable checks are:

- eval clip2 curve in the same ballpark as the frozen trace;
- final adapter beats/ties the same no-adapter baseline on test continuation;
- GPT-5.5 real-Z remains positive against the retrained context-only control on the
  source-disjoint test overlap, while nano remains weak or negative.

## Current Public Claim

For the public artifact, the clean claim should not depend on full retraining.
It is:

```text
real-Z scaffold score - context-only SFT score, source-disjoint test, clip2

GPT-5.5 lanes: positive by about +0.049 to +0.082 logprob/token.
Nano lanes: negative or near zero.
```

The frozen-score path establishes that claim exactly; adapter-rescore and full
retrain are deeper audits.
