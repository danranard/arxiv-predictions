from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd


BUNDLE = Path(__file__).resolve().parents[1]
MODELS = [
    "gpt55_none",
    "gpt55_low",
    "gpt55_medium",
    "gpt55_high",
    "gpt54_nano_low",
    "gpt54_nano_medium",
    "gpt54_nano_high",
]
WRAPPER_RE = re.compile(
    r"\b(here(?:'s| is).{0,40}(prediction|continuation|forecast|guess)|"
    r"my (prediction|guess|forecast)|to continue|best guess|as an ai)\b",
    re.IGNORECASE | re.DOTALL,
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def extract_z(prompt: str) -> str:
    start_marker = "% Notes about what's next:\n"
    end_marker = "\n\n% Returning to the paper text:\n"
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


def stderr(series: pd.Series) -> float:
    return float(series.std(ddof=1) / math.sqrt(len(series)))


def audit_window(window: int) -> list[str]:
    problems = []
    forecast_rows = read_jsonl(
        BUNDLE / "scorer_inputs" / "forecast_scaffold" / f"eval_all_realz_y{window}_completion.jsonl"
    )
    bare_rows = read_jsonl(
        BUNDLE / "scorer_inputs" / "bare_context" / f"eval_y{window}_completion.jsonl"
    )
    bare_by_key = {(str(r["paper_id"]), int(r["cut_id"])): r for r in bare_rows}

    for row in forecast_rows:
        prompt = row["prompt"]
        if "% Notes about what's next:" not in prompt or "% Returning to the paper text:" not in prompt:
            problems.append(f"missing scaffold markers in forecast row {row.get('dataset_row_index')}")
            break
        z = extract_z(prompt)
        if len(z.strip()) < 200:
            problems.append(f"short Z in forecast row {row.get('dataset_row_index')}")
            break
        if WRAPPER_RE.search(z[:500]):
            problems.append(f"wrapper-like Z in forecast row {row.get('dataset_row_index')}")
            break

    for row in forecast_rows:
        key = (str(row["paper_id"]), int(row["cut_id"]))
        if key not in bare_by_key:
            continue
        if row["target"] != bare_by_key[key]["target"]:
            problems.append(f"target mismatch at {key}")
            break

    for name in [
        f"forecast_scaffold_y{window}_completion_scores.csv",
        f"bare_context_y{window}_completion_scores.csv",
    ]:
        scores = pd.read_csv(BUNDLE / "source_scores" / name, dtype={"paper_id": str})
        if sorted(scores["target_chars"].unique()) != [window]:
            problems.append(f"{name}: target_chars not exactly {window}")
        if sorted(scores["boundary_mode"].unique()) != ["full_offset"]:
            problems.append(f"{name}: boundary_mode not full_offset")

    return problems


def main() -> None:
    problems = []
    joined = pd.read_csv(
        BUNDLE / "analysis" / "forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv",
        dtype={"paper_id": str},
    )
    if joined["predictor_model"].isna().any():
        problems.append("joined table has null predictor labels")
    if joined.duplicated(["window_chars", "predictor_model", "paper_id", "cut_id"]).any():
        problems.append("joined table has duplicate window/model/paper/cut keys")
    if len(joined) != 4530:
        problems.append(f"joined table row count is {len(joined)}, expected 4530")

    for window in (200, 1000):
        problems.extend(audit_window(window))

    print("Headline from bundle joined CSV:")
    joined["family"] = joined["predictor_model"].map(
        lambda x: "gpt55" if str(x).startswith("gpt55") else "nano"
    )
    for (window, family), group in joined.groupby(["window_chars", "family"]):
        print(
            f"{window}_{family}: "
            f"clip2={group['delta_clip2_mean_logprob'].mean():+.6f} +/- "
            f"{stderr(group['delta_clip2_mean_logprob']):.6f}; "
            f"raw={group['delta_raw_mean_logprob'].mean():+.6f} +/- "
            f"{stderr(group['delta_raw_mean_logprob']):.6f}; n={len(group)}"
        )

    if problems:
        print("\nAUDIT PROBLEMS:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("\nAUDIT OK")


if __name__ == "__main__":
    main()
