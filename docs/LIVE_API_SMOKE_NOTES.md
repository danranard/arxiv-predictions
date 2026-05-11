# Live API Smoke Notes

Headline reproduction is offline. The live API smoke scripts are only meant to
check that provider interfaces still accept the intended request shapes and
return the expected schema.

## Fireworks Scorer Smoke

On 2026-05-01, row 0, `gpt55_medium`:

```text
Qwen3-8B:
  target token count delta: 0
  raw/token delta:          0.00000
  clip2 delta:              0.00000

Kimi K2.6, repeated same prompt:
  call 1 vs frozen: raw +0.00724, clip2 -0.00188
  call 2 vs frozen: raw +0.00058, clip2 +0.00290
  call 3 vs frozen: raw +0.00071, clip2 -0.00532
```

Follow-up Kimi probes returned the same target token IDs and offsets across
repeats, including with `max_tokens=0`, fixed seed, fixed `prompt_cache_key`,
and explicitly pinned neutral sampling parameters. On row 0, five detailed
repeats had raw logprob SD about `2.03` across target-token positions and
average repeat-to-repeat SD about `0.063` for the same token position, with
row-level `clip2` spanning about `0.018`. Across four two-repeat rows, pairwise
`clip2` deltas were `-0.0073`, `-0.0018`, `-0.0103`, and `+0.0049`. This points
to server-side numerical/routing/backend nondeterminism rather than a
prompt-boundary, tokenization, or token-slicing bug.

For the project artifact, this is acceptable because:

- Qwen3-8B is the main frozen-scorer headline and reproduced exactly in the
  row-0 smoke.
- Kimi K2.6 is a robustness scorer showing the same qualitative trends.
- The exact reproducibility promise is based on saved token-level logprobs,
  not on rerunning mutable serverless endpoints.

If Kimi or Qwen serverless access changes, the offline headline path remains
valid.
