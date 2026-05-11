# Scorer Identity

This artifact uses two frozen hosted likelihood scorers. The primary scorer is
Qwen3-8B:

```text
provider/model: accounts/fireworks/models/qwen3-8b
serving path:   Fireworks OpenAI-compatible /completions
upstream HF:    Qwen/Qwen3-8B
interface:      raw prompt-completion logprob scoring, not chat messages
```

The model should be described as **Qwen3-8B post-trained/chat-capable weights
used in raw completion-logprob mode**. It should not be described as
pretraining-only `Qwen/Qwen3-8B-Base`. Fireworks labels this catalog entry as a
"base model", but in this context that means the provider's base deployable
model, not the upstream pretraining-only base checkpoint. The Hugging Face
model tree for `Qwen/Qwen3-8B` lists `Qwen/Qwen3-8B-Base` as its base model and
describes `Qwen/Qwen3-8B` as "Pretraining & Post-training".

Mechanically, scoring sends `prompt + target` to the completions endpoint with
`echo=true`, `logprobs=1`, and `temperature=0`, then extracts only target-token
logprobs by text offset. There is no system prompt, messages array, assistant
role, or automatic chat template in the normal Qwen scoring path.

For LoRA/SFT controls run on rented GPU hardware, the local model was loaded as
`Qwen/Qwen3-8B` through Hugging Face/Transformers. A no-adapter audit compared
local Hugging Face `Qwen/Qwen3-8B` against Fireworks
`accounts/fireworks/models/qwen3-8b` on 650 overlapping equation examples,
using identical prompts and full-offset prompt+target tokenization. The target
token counts matched exactly on all rows. Mean per-token logprob differences
were tiny relative to experimental effects:

```text
raw   corr 0.99964   HF - Fireworks mean -0.00108 +/- 0.00053
clip2 corr 0.99958   HF - Fireworks mean +0.00138 +/- 0.00027
clip3 corr 0.99955   HF - Fireworks mean +0.00138 +/- 0.00037
clip5 corr 0.99962   HF - Fireworks mean +0.00032 +/- 0.00045
```

Interpretation: for this artifact's scoring purposes, the Fireworks Qwen3-8B
scorer and the H100 Hugging Face model should be treated as the same upstream
Qwen3-8B model, with small serving/precision differences. We do not claim
bit-identical hosted and local weights or kernels.

The second frozen scorer is:

```text
provider/model: accounts/fireworks/models/kimi-k2p6
serving path:   Fireworks OpenAI-compatible /completions
interface:      raw prompt-completion logprob scoring
```

Kimi K2.6 is included as a larger-model robustness check. It should be
described as **Fireworks-hosted Kimi K2.6 by Moonshot AI, used in raw
completion-logprob mode**. Moonshot/Kimi documentation identifies Kimi K2.6 as
an open-source/open-weight multimodal agentic model with a 256k context window;
the public Hugging Face model is `moonshotai/Kimi-K2.6`, and the Kimi API model
name is `kimi-k2.6`. Our experiments did not load Kimi locally or train Kimi
adapters, so we do not make a local-vs-hosted equivalence claim analogous to
the Qwen/H100 audit.

For our purposes, the exact model identifier is the Fireworks identifier saved
in every Kimi run plan:

```text
accounts/fireworks/models/kimi-k2p6
```

The scoring interface is the same completion-logprob path as Qwen: send
`prompt + target` to `/completions` with `echo=true`, `logprobs=1`, and
`temperature=0`, then extract target-token logprobs by offset. Fireworks returns
a leading `<bos>` token for Kimi as well; the scoring wrapper normalizes this
offset shift before slicing target tokens.

In live smoke tests, the Kimi serverless endpoint showed small
repeat-to-repeat logprob variation on the same prompt despite matching target
token IDs and offsets, and despite neutral sampling settings. Exact Kimi
reproducibility in this artifact therefore comes from the frozen saved
token-level logprob files, not from rerunning the hosted endpoint. Kimi should
be cited as a large hosted robustness scorer, not as a bit-stable local
reproduction target.
