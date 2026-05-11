# Qwen3-8B Frozen Prefix Windows

This folder packages the compact no-SFT scaffold-scorer summary for the
prose/TeX continuation module. It is the closest prose analogue of the main
equation-split benchmark setup:

```text
scorer: Qwen3-8B
scorer SFT: none
metric: clip2
scaffold: X_base + forecast Z + return-to-paper X_tail
X_base = 2000 chars
X_tail = 2000 chars
Z_budget = 1000 chars
forecast Z = first 1000 chars of model_direct_y_3
scored windows: first 100, 200, 500, 1000 chars of Y
```

The purpose is to show what happens before any scaffold-aware SFT. The headline
is a length curve: forecast strings help strongly in the first 100-200
characters and the measured lift decays as the scored continuation grows.

## Files

- `summary_by_model_window_control.csv`: all saved summary rows.
- `representative_gpt55_high.csv`: the cleaner narrative lane used in the
  module README.

These are summary-level frozen results. The prose module's row-level packaged
CSV files are the later SFT-route scores in `../`. The original exploratory
notes also preserve this table in
`../../docs/PROSE_CONTINUATION_SFT_RESULTS.md` under "Frozen-Scorer Prefix
Windows".

## Representative Result

For GPT-5.5 high:

```text
Forecast Z - scaffold_empty, clip2
100 chars:  +0.0596 +/- .0044
200 chars:  +0.0480 +/- .0031
500 chars:  +0.0349 +/- .0018
1000 chars: +0.0253 +/- .0011

Forecast Z - bare_x_base_plus_z, clip2
100 chars:  +0.0375 +/- .0045
200 chars:  +0.0337 +/- .0032
500 chars:  +0.0217 +/- .0021
1000 chars: +0.0135 +/- .0014
```

The stronger `bare_x_base_plus_z` control is a plain 3000-character
continuation context: the ordinary 2000-character local context plus an extra
1000 immediately preceding characters, matching the forecast side-channel
budget.
