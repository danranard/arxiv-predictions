# Toy Equation-Order Mechanism Probe

This diagnostic probes why `clip2` can preserve useful forecast signal even when a forecast is locally wrong or reordered.

It uses tiny controlled equation continuations such as:

```tex
Z = X + A + B
```

and compares:

- `true_forecast`: the scaffold contains the exact equation suffix.
- `reordered_forecast`: the scaffold contains the same symbols in a different order.
- `wrong_symbol_forecast`: the scaffold contains an incorrect symbol.
- `empty`: the scaffold contains no forecast.
- `bare_B`: the context-only continuation baseline.

The probe is intentionally small and mechanistic. It is not one of the frozen headline benchmark results.

## Files

- `qwen3_8b/`: run against `accounts/fireworks/models/qwen3-8b`.
- `kimi_k2p6/`: run against `accounts/fireworks/models/kimi-k2p6`.
- `scripts/probe_qwen_toy_equation_order.py`: script used for both runs.

Each run folder contains:

- `README.md`: human-readable result table.
- `score_summary.csv`: raw and clip2 scores for each toy condition.
- `target_token_logprobs.csv`: token-level scored-target logprobs.
- `forced_recovery_probe_summary.csv`: recovery probabilities derived from the
  same forced-likelihood token logprobs used by the benchmark.
- `next_token_probe_summary.csv`: older one-token generation diagnostic after
  the true partial has been seen. This is kept for provenance, but the
  forced-likelihood file is the one to use for manuscript-style scoring.
- `next_token_top_logprobs.csv`: top-token details for the older generation diagnostic.
- `run_payload.json`: model id, toy cases, and prompt examples.

## Main Observation

Qwen3-8B and Kimi K2.6 show the same qualitative behavior:

- The exact forecast receives near-perfect likelihood.
- A reordered forecast is punished at the local mismatch, but still gives strong positive `clip2` lift because later tokens become easy once the true prefix has caught up.
- A wrong-symbol forecast is worse, but can still beat empty in some cases because it supplies local equation structure.

This supports the interpretation that `clip2` mostly limits the cost of local mismatch while preserving later usefulness, rather than simply erasing all meaningful forecast errors.
