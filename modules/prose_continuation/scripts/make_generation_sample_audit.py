from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments" / "2026-05-03_fresh40_forecast_scaffold_clip2_sft_nano_lmh_v0"
OUT = EXP / "analysis"
MODEL_ORDER = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "gpt54_nano_low",
    "gpt54_nano_medium",
    "gpt54_nano_high",
]

WRAPPER_PATTERNS = [
    r"\bhere(?:'s| is)\b.{0,40}\b(?:prediction|continuation|forecast|guess)\b",
    r"\bmy (?:prediction|guess|forecast)\b",
    r"\bi (?:would|will) (?:predict|continue|guess)\b",
    r"\bthe next (?:paragraph|passage|text) (?:might|will|could)\b",
    r"\bto continue\b",
    r"\bbest guess\b",
    r"\bas an ai\b",
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def extract_z(prompt: str) -> str:
    start_marker = "% Notes about what's next:\n"
    end_marker = "\n\n% Returning to the paper text:\n"
    if start_marker not in prompt or end_marker not in prompt:
        return ""
    start = prompt.index(start_marker) + len(start_marker)
    end = prompt.index(end_marker, start)
    z_block = prompt[start:end]
    lines = []
    for line in z_block.splitlines():
        if line.startswith("% "):
            lines.append(line[2:])
        elif line == "%":
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def tail(text: str, n: int = 1400) -> str:
    text = text.strip()
    return text[-n:]


def head(text: str, n: int = 1000) -> str:
    return text.strip()[:n]


def count_wrappers(rows: list[dict]) -> dict:
    counts: dict[str, Counter] = defaultdict(Counter)
    examples: dict[str, list[dict]] = defaultdict(list)
    compiled = [(pat, re.compile(pat, re.IGNORECASE | re.DOTALL)) for pat in WRAPPER_PATTERNS]
    for row in rows:
        model = row["predictor_model"]
        z = extract_z(row["prompt"])
        for name, pattern in compiled:
            if pattern.search(z[:500]):
                counts[model][name] += 1
                if len(examples[model]) < 5:
                    examples[model].append(
                        {
                            "paper_id": row["paper_id"],
                            "cut_id": row["cut_id"],
                            "pattern": name,
                            "z_head": head(z, 350),
                        }
                    )
    return {
        "counts": {model: dict(counts.get(model, Counter())) for model in MODEL_ORDER},
        "examples": examples,
    }


def generation_quality_summary(rows: list[dict]) -> dict:
    by_model = {}
    for model in MODEL_ORDER:
        model_rows = [row for row in rows if row.get("predictor_model") == model]
        z_values = [extract_z(row["prompt"]) for row in model_rows]
        z_lens = sorted(len(z) for z in z_values)
        exact_target_prefix_hits = 0
        target_head_hits = 0
        for row, z in zip(model_rows, z_values):
            target = row["target"].strip()
            if target and target[:120] in z:
                exact_target_prefix_hits += 1
            if target and target[:40] in z:
                target_head_hits += 1
        if z_lens:
            by_model[model] = {
                "rows": len(model_rows),
                "z_chars_min": z_lens[0],
                "z_chars_p10": z_lens[len(z_lens) // 10],
                "z_chars_median": z_lens[len(z_lens) // 2],
                "z_chars_p90": z_lens[(len(z_lens) * 9) // 10],
                "z_chars_max": z_lens[-1],
                "z_empty": sum(1 for z in z_values if not z.strip()),
                "z_under_200_chars": sum(1 for z in z_values if len(z.strip()) < 200),
                "z_exactly_budgetish_1000_chars": sum(1 for z in z_values if len(z) >= 995),
                "target_first_120_chars_in_z": exact_target_prefix_hits,
                "target_first_40_chars_in_z": target_head_hits,
            }
    return by_model


def choose_samples(rows: list[dict]) -> list[dict]:
    # Deterministic spread: first, middle, last matched-ish row per model where possible.
    samples = []
    for model in MODEL_ORDER:
        model_rows = [r for r in rows if r.get("predictor_model") == model]
        if not model_rows:
            continue
        indexes = sorted({0, len(model_rows) // 2, len(model_rows) - 1})
        for idx in indexes[:3]:
            samples.append(model_rows[idx])
    return samples


def make_markdown(rows: list[dict], wrapper_audit: dict, quality_summary: dict) -> str:
    lines = [
        "# Generation And Scoring Sample Audit",
        "",
        "Created: 2026-05-03.",
        "",
        "Purpose: quick human-readable audit of the actual forecast `Z` strings and scaffolded prompts sent to the SFT forecast-scaffold scorer. This is not a statistical sample; it is a deterministic spread across predictor models to catch obvious prompt/generation pathologies.",
        "",
        "The scorer sees:",
        "",
        "```text",
        "X_base",
        "",
        "% Notes about what's next:",
        "% Z",
        "",
        "% Returning to the paper text:",
        "X_tail",
        "Y",
        "```",
        "",
        "The score is on `Y`; `X_base + notes + X_tail` is the prompt.",
        "",
        "## Automated Wrapper Scan",
        "",
        "Searched the first 500 chars of extracted `Z` for obvious wrapper/preamble language such as `here is my prediction`, `to continue`, `best guess`, and similar.",
        "",
        "```text",
    ]
    for model in MODEL_ORDER:
        counts = wrapper_audit["counts"].get(model, {})
        total = sum(counts.values())
        lines.append(f"{model:18s} flagged_matches={total} details={counts}")
    lines.extend(["```", ""])
    if any(wrapper_audit["examples"].values()):
        lines.append("Flagged examples for manual review:")
        lines.append("")
        for model, examples in wrapper_audit["examples"].items():
            for ex in examples:
                lines.append(f"- `{model}` `{ex['paper_id']}` cut `{ex['cut_id']}` pattern `{ex['pattern']}`: {ex['z_head']!r}")
        lines.append("")
    else:
        lines.append("No obvious wrapper/preamble patterns were flagged by this crude scan.")
        lines.append("")

    lines.append("## Generation Quality Summary")
    lines.append("")
    lines.append("```text")
    for model in MODEL_ORDER:
        q = quality_summary.get(model, {})
        if not q:
            continue
        lines.append(
            f"{model:18s} rows={q['rows']:3d} "
            f"z_chars min/p10/med/p90/max="
            f"{q['z_chars_min']}/{q['z_chars_p10']}/{q['z_chars_median']}/"
            f"{q['z_chars_p90']}/{q['z_chars_max']} "
            f"empty={q['z_empty']} under200={q['z_under_200_chars']} "
            f"target40_in_z={q['target_first_40_chars_in_z']} "
            f"target120_in_z={q['target_first_120_chars_in_z']}"
        )
    lines.append("```")
    lines.append("")
    lines.append(
        "`target40_in_z` and `target120_in_z` are crude leakage/near-copy scans for the first "
        "40 or 120 chars of the scored target appearing inside extracted `Z`. Hits are not "
        "automatically invalid, because technical text can repeat local phrases, but nonzero "
        "counts should be hand-read."
    )
    lines.append("")

    lines.append("## Samples")
    lines.append("")
    for row in rows:
        prompt = row["prompt"]
        z = extract_z(prompt)
        target = row["target"]
        before_return = prompt.split("\n\n% Returning to the paper text:\n", 1)[0]
        x_tail = prompt.split("\n\n% Returning to the paper text:\n", 1)[1]
        lines.extend(
            [
                f"### {row['predictor_model']} | paper {row['paper_id']} | cut {row['cut_id']}",
                "",
                f"- prompt chars: `{len(prompt)}`",
                f"- Z chars: `{len(z)}`",
                f"- target chars: `{len(target)}`",
                "",
                "**Z Head**",
                "",
                "```text",
                head(z, 1200),
                "```",
                "",
                "**Prompt Tail Before Returning Marker**",
                "",
                "```text",
                tail(before_return, 1200),
                "```",
                "",
                "**X Tail Given To Judge**",
                "",
                "```text",
                tail(x_tail, 1400),
                "```",
                "",
                "**Target Y Head**",
                "",
                "```text",
                head(target, 1200),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rows = read_jsonl(EXP / "dataset_v1" / "eval_all_realz_y1000_completion.jsonl")
    wrapper_audit = count_wrappers(rows)
    quality_summary = generation_quality_summary(rows)
    samples = choose_samples(rows)
    (OUT / "generation_quality_summary.json").write_text(
        json.dumps(quality_summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUT / "generation_wrapper_audit.json").write_text(
        json.dumps(wrapper_audit, indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUT / "generation_prompt_samples.md").write_text(
        make_markdown(samples, wrapper_audit, quality_summary), encoding="utf-8"
    )
    print("wrote analysis/generation_quality_summary.json")
    print("wrote analysis/generation_wrapper_audit.json")
    print("wrote analysis/generation_prompt_samples.md")


if __name__ == "__main__":
    main()
