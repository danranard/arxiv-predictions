# Equation-Cut Scoring: Copy Scaffold Controls

Created: 2026-05-04T21:59:35.659689+00:00

Judge: `accounts/fireworks/models/qwen3-8b` via `https://api.fireworks.ai/inference/v1`.
Elapsed seconds: 1.6.
Target mode: `body_plus_close`.
Scaffold variant: `current`.
Bare multipliers: `[1.0]`.
Headline comparison baseline: `bare_B`.

Target-mode definitions:

- `body`: score only the held-out equation suffix `Y`.
- `body_plus_close`: score `Y` plus newline and the display close delimiter, e.g. `\end{equation*}` or `\]`.

Conditions:

- `bare_B`: last `B=len(Y)+40` chars before the equation plus equation prefix.
- `bare_3B`: last `3*B` chars before the equation plus equation prefix, when requested.
- `scaffold_empty`: original copy scaffold with an empty first-equation suffix.
- `scaffold_oracle_Y`: original copy scaffold with true `Y` in the first equation.
- `scaffold_z_predictor`: original copy scaffold with GPT-5.5 generated `Z_B`, then same equation prefix.
- `scaffold_raw_precontext_B`: same scaffold with the previous `B` raw pre-cut characters inserted in the Z slot, when requested.

Headline:

- n pairs: 0
- mean diff per token (`scaffold_z_predictor - bare_B`): None
- stderr: None
- positive rate: None

Files:

- `equation_scores.csv`
- `equation_target_token_logprobs.csv`
- `summary.json`
- `prompt_previews/`
