# Opus 4.7 Canonical Inputs

Created: 2026-05-04.

This directory contains both canonical Anthropic Claude Opus 4.7 equation-split data and scratch/provenance attempts. The migration into the equation-splits reproducible bundle should read only the canonical inputs listed here.

## Canonical Generation Inputs

Use these four clean joined generation files:

| bundle | lane | joined file |
|---|---|---|
| old731 | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_medium_eq_superbundle_partial_current/claude_opus47_medium_partial_joined.jsonl` |
| old731 | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_low_eq_full731_partial_current/claude_opus47_low_partial_joined.jsonl` |
| new632 | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/claude_opus47_medium_new632_current_joined.jsonl` |
| new632 | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/claude_opus47_low_new632_current_joined.jsonl` |

These joined files are the canonical row rectangles:

- old731 medium: 731 rows
- old731 low: 731 rows
- new632 medium: 632 rows
- new632 low: 632 rows

The joined files select successful attempts and should supersede older append-only raw attempts in the same output logs.

## Canonical Score Inputs

Use these eight z-only score directories:

| bundle | judge | lane | score dir |
|---|---|---|---|
| old731 | Qwen3-8B | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_medium_eq_superbundle_partial_current/small_qwen_current_body_plus_close_zonly` |
| old731 | Qwen3-8B | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_low_eq_full731_partial_current/small_qwen_current_body_plus_close_zonly` |
| old731 | Kimi K2P6 | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_medium_eq_superbundle_partial_current/kimi_k2p6_current_body_plus_close_zonly` |
| old731 | Kimi K2P6 | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-03_opus47_low_eq_full731_partial_current/kimi_k2p6_current_body_plus_close_zonly` |
| new632 | Qwen3-8B | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/medium_new632_qwen_body_plus_close_zonly` |
| new632 | Qwen3-8B | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/low_new632_qwen_body_plus_close_zonly` |
| new632 | Kimi K2P6 | `opus47_medium` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/medium_new632_kimi_body_plus_close_zonly` |
| new632 | Kimi K2P6 | `opus47_low` | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_second_subbundle_plan_v0/low_new632_kimi_body_plus_close_zonly` |

Each canonical score dir should contain exactly one `scaffold_z_predictor` score row per joined generation row:

- old731 score dirs: 731 rows
- new632 score dirs: 632 rows

## Canonical Repair Provenance

The canonical medium lanes include two high-budget true-medium repairs:

| bundle | row | repair dir | notes |
|---|---:|---|---|
| old731 | 452 | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_medium_canonical_repair_v1/old_medium_row0452_32768` | `effort=medium`, `no_thinking=false`, `max_tokens=32768`, visible length 68, output tokens 29331 |
| new632 | 590 | `diagnostics/anthropic_claude_smoke/2026-05-04_opus47_medium_canonical_repair_v1/new_medium_row0590_32768` | `effort=medium`, `no_thinking=false`, `max_tokens=32768`, visible length 118, output tokens 21132 |

These repairs replace earlier no-thinking fallbacks and should be treated as canonical medium-thinking samples.

The low lanes include high-token retries for the analogous rows. These are conceptually fine because they preserve the intended low-thinking setting and only increase the output/thinking token budget.

## Canonical Audit Note

This file is the public artifact's compact provenance summary for the Opus 4.7
lane integration. A longer retry/rectangle cleanup note from the construction
workspace is archived outside the public artifact under the wrapper-level
`meta_notes/` folder.

## Scratch / Do Not Use As Canonical Inputs

Do not migrate these as canonical bundle inputs:

- `2026-05-04_opus47_medium_canonical_repair_v0`: failed immediately because `ANTHROPIC_API_KEY` was not set.
- `2026-05-04_opus47_no_thinking_straggler_retries_v0`: diagnostic no-thinking fallback, superseded by true-medium repairs.
- `2026-05-04_opus47_straggler_retries_v0`, `2026-05-04_opus47_final_straggler_retries_v1`, `2026-05-04_opus47_high_budget_straggler_retries_v0`: raw/provenance retry orchestration; useful historically, but not canonical joined inputs.
- `2026-05-03_opus47_medium_eq_superbundle_partial_228`, `_440`, `_483`: partial snapshots, superseded by `partial_current`.
- `2026-05-03_opus47_low_eq_first100_partial_53`, `_90`, `_current`: partial snapshots, superseded by the full current low lane.
- one-row smoke/probe files such as `2026-05-03_opus47_xhigh_eq_row0000*.json`, `2026-05-03_opus47_high_eq_row0000_4096.json`, and `2026-05-03_opus47_medium_eq_row0000_8192.json`.
- non-zonly partial scoring folders such as `small_qwen_current_body_plus_close` under partial medium snapshots; these are exploratory and should not enter the Opus lane integration.

## Current Headline Check

After true-medium repairs and score refresh, paired `opus47_medium - opus47_low` on `scaffold_z_predictor`, `body_plus_close`:

```text
Qwen3-8B, combined old731+new632, n=1363, P=138 paper clusters:
raw   +0.014642 +/- 0.004823
clip1 +0.003959 +/- 0.001254
clip2 +0.006324 +/- 0.002125
clip3 +0.008379 +/- 0.002786

Kimi K2P6, combined old731+new632, n=1363, P=138 paper clusters:
raw   +0.012750 +/- 0.003544
clip1 +0.004567 +/- 0.001252
clip2 +0.007305 +/- 0.001977
clip3 +0.009565 +/- 0.002512
```

These are paper-clustered SEs over old/new paper clusters.
