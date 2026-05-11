from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


FIREWORKS_COMPLETIONS_URL = "https://api.fireworks.ai/inference/v1/completions"
DEFAULT_MODEL = "accounts/fireworks/models/qwen3-8b"


@dataclass(frozen=True)
class ToyCase:
    case_id: str
    description: str
    lhs: str
    true_rhs: str
    reordered_rhs: str
    wrong_rhs: str
    recovery_partial: str
    recovery_true_next: str


TOY_CASES = [
    ToyCase(
        case_id="add_ab",
        description="Addition order: true X + A + B, reordered X + B + A",
        lhs="Z =",
        true_rhs=" X + A + B",
        reordered_rhs=" X + B + A",
        wrong_rhs=" X + Y",
        recovery_partial=" X + A +",
        recovery_true_next=" B",
    ),
    ToyCase(
        case_id="add_ba",
        description="Addition order, A/B swapped: true X + B + A, reordered X + A + B",
        lhs="Z =",
        true_rhs=" X + B + A",
        reordered_rhs=" X + A + B",
        wrong_rhs=" X + Y",
        recovery_partial=" X + B +",
        recovery_true_next=" A",
    ),
    ToyCase(
        case_id="mul_ab",
        description="Juxtaposed product: true X + A B, reordered X + B A",
        lhs="Z =",
        true_rhs=" X + A B",
        reordered_rhs=" X + B A",
        wrong_rhs=" X + Y",
        recovery_partial=" X + A",
        recovery_true_next=" B",
    ),
    ToyCase(
        case_id="mul_ba",
        description="Juxtaposed product, A/B swapped: true X + B A, reordered X + A B",
        lhs="Z =",
        true_rhs=" X + B A",
        reordered_rhs=" X + A B",
        wrong_rhs=" X + Y",
        recovery_partial=" X + B",
        recovery_true_next=" A",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Probe Qwen logprobs on tiny equation-order examples using the "
            "equation-splits-style scaffold. Targets omit the closing delimiter."
        )
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("RLVR text-prediction")
        / "experiments"
        / "2026-05-03_toy_equation_order_qwen_probe",
    )
    parser.add_argument("--context", default="Here are some equations involving some sums.")
    args = parser.parse_args()

    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        raise SystemExit("FIREWORKS_API_KEY is not set")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    client = FireworksClient(api_key=api_key, model=args.model)

    score_rows: list[dict[str, Any]] = []
    token_rows: list[dict[str, Any]] = []
    forced_probe_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    top_token_rows: list[dict[str, Any]] = []
    prompt_examples: dict[str, str] = {}

    for toy in TOY_CASES:
        scores = run_scored_case(client, toy, args.context)
        bare_clip2 = scores["bare_B"]["clip2"]
        empty_clip2 = scores["empty"]["clip2"]

        for condition, result in scores.items():
            score_rows.append(
                {
                    "case_id": toy.case_id,
                    "description": toy.description,
                    "condition": condition,
                    "raw_mean": result["raw"],
                    "clip2_mean": result["clip2"],
                    "clip2_vs_empty": result["clip2"] - empty_clip2,
                    "clip2_vs_bare": result["clip2"] - bare_clip2,
                    "target_token_count": len(result["tokens"]),
                    "target": toy.true_rhs,
                }
            )
            for idx, token in enumerate(result["tokens"]):
                token_rows.append(
                    {
                        "case_id": toy.case_id,
                        "condition": condition,
                        "target_token_index": idx,
                        "target_char_offset": token["offset"],
                        "token": token["token"],
                        "token_logprob": token["logprob"],
                        "clip2_token_logprob": max(token["logprob"], -2.0),
                    }
                )

        probes = run_recovery_probe(client, toy)
        forced_probes = run_forced_recovery_probe(client, toy)
        for condition, result in forced_probes.items():
            token = result["tokens"][0]
            forced_probe_rows.append(
                {
                    "case_id": toy.case_id,
                    "description": toy.description,
                    "condition": condition,
                    "partial": toy.lhs + toy.recovery_partial,
                    "true_next": toy.recovery_true_next,
                    "forced_token": token["token"],
                    "forced_logprob": token["logprob"],
                    "forced_probability": math.exp(token["logprob"]),
                }
            )
        for condition, result in probes.items():
            probe_rows.append(
                {
                    "case_id": toy.case_id,
                    "description": toy.description,
                    "condition": condition,
                    "partial": toy.lhs + toy.recovery_partial,
                    "true_next": toy.recovery_true_next,
                    "generated_token": result["generated_token"],
                    "generated_logprob": result["generated_logprob"],
                    "generated_probability": math.exp(result["generated_logprob"]),
                    "true_next_logprob": result.get("true_next_logprob"),
                    "true_next_probability": (
                        math.exp(result["true_next_logprob"])
                        if result.get("true_next_logprob") is not None
                        else None
                    ),
                }
            )
            for rank, item in enumerate(result["top_tokens"], start=1):
                top_token_rows.append(
                    {
                        "case_id": toy.case_id,
                        "condition": condition,
                        "rank": rank,
                        "token": item["token"],
                        "logprob": item["logprob"],
                        "probability": math.exp(item["logprob"]),
                        "is_true_next": item["token"] == toy.recovery_true_next,
                    }
                )

        prompt_examples[toy.case_id] = make_scaffold_prompt(toy, toy.true_rhs) + "[SCORED_TARGET]"

    write_csv(args.out_dir / "score_summary.csv", score_rows)
    write_csv(args.out_dir / "target_token_logprobs.csv", token_rows)
    write_csv(args.out_dir / "forced_recovery_probe_summary.csv", forced_probe_rows)
    write_csv(args.out_dir / "next_token_probe_summary.csv", probe_rows)
    write_csv(args.out_dir / "next_token_top_logprobs.csv", top_token_rows)
    write_json(
        args.out_dir / "run_payload.json",
        {
            "model": args.model,
            "target_includes_closing_delimiter": False,
            "cases": [toy.__dict__ for toy in TOY_CASES],
            "prompt_examples": prompt_examples,
        },
    )
    write_markdown(args.out_dir / "README.md", args.model, score_rows, forced_probe_rows, probe_rows)

    print(f"Wrote toy equation-order probe results to {args.out_dir}")
    print_summary(score_rows, forced_probe_rows)


class FireworksClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenAI/Python 1.0",
        }

    def completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"model": self.model, **payload}
        response = requests.post(
            FIREWORKS_COMPLETIONS_URL,
            headers=self.headers,
            json=body,
            timeout=90,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Fireworks HTTP {response.status_code}: {response.text[:1000]}")
        return response.json()


def run_scored_case(client: FireworksClient, toy: ToyCase, context: str) -> dict[str, dict[str, Any]]:
    bare_prefix = f"{context}\n\\begin{{equation}}\n{toy.lhs}"
    prefixes = {
        "bare_B": bare_prefix,
        "true_forecast": make_scaffold_prompt(toy, toy.true_rhs),
        "reordered_forecast": make_scaffold_prompt(toy, toy.reordered_rhs),
        "wrong_symbol_forecast": make_scaffold_prompt(toy, toy.wrong_rhs),
        "empty_forecast": make_scaffold_prompt(toy, ""),
        "empty": make_scaffold_prompt(toy, ""),
    }
    # Keep the historical condition name "empty" as the comparison baseline and
    # omit the duplicate alias before scoring.
    prefixes.pop("empty_forecast")
    return {condition: score_target(client, prefix, toy.true_rhs) for condition, prefix in prefixes.items()}


def make_scaffold_prompt(toy: ToyCase, rhs: str) -> str:
    return (
        "% First equation:\n"
        "\\begin{equation}\n"
        f"{toy.lhs}{rhs}\n"
        "\\end{equation}\n\n"
        "% Same equation:\n"
        "\\begin{equation}\n"
        f"{toy.lhs}"
    )


def score_target(client: FireworksClient, prefix: str, target: str) -> dict[str, Any]:
    full = prefix + target
    response = client.completions(
        {
            "prompt": full,
            "max_tokens": 1,
            "echo": True,
            "logprobs": 1,
            "temperature": 0,
            "return_token_ids": True,
        }
    )
    logprobs = response["choices"][0]["logprobs"]
    boundary = len(prefix)
    target_end = len(full)
    tokens = []
    for token, offset, logprob in zip(
        logprobs["tokens"],
        logprobs["text_offset"],
        logprobs["token_logprobs"],
    ):
        if logprob is None:
            continue
        offset = int(offset)
        if boundary <= offset < target_end:
            tokens.append(
                {
                    "token": token,
                    "offset": offset - boundary,
                    "logprob": float(logprob),
                }
            )
    if not tokens:
        raise RuntimeError("No target tokens found in Fireworks response")
    raw = sum(item["logprob"] for item in tokens) / len(tokens)
    clip2 = sum(max(item["logprob"], -2.0) for item in tokens) / len(tokens)
    return {"raw": raw, "clip2": clip2, "tokens": tokens}


def run_recovery_probe(client: FireworksClient, toy: ToyCase) -> dict[str, dict[str, Any]]:
    prompts = {
        "true_forecast": make_partial_probe_prompt(toy, toy.true_rhs),
        "reordered_forecast": make_partial_probe_prompt(toy, toy.reordered_rhs),
        "wrong_symbol_forecast": make_partial_probe_prompt(toy, toy.wrong_rhs),
        "empty": make_partial_probe_prompt(toy, ""),
    }
    return {
        condition: next_token_distribution(client, prompt, toy.recovery_true_next)
        for condition, prompt in prompts.items()
    }


def run_forced_recovery_probe(client: FireworksClient, toy: ToyCase) -> dict[str, dict[str, Any]]:
    prompts = {
        "true_forecast": make_partial_probe_prompt(toy, toy.true_rhs),
        "reordered_forecast": make_partial_probe_prompt(toy, toy.reordered_rhs),
        "wrong_symbol_forecast": make_partial_probe_prompt(toy, toy.wrong_rhs),
        "empty": make_partial_probe_prompt(toy, ""),
    }
    return {
        condition: score_target(client, prompt, toy.recovery_true_next)
        for condition, prompt in prompts.items()
    }


def make_partial_probe_prompt(toy: ToyCase, rhs: str) -> str:
    return make_scaffold_prompt(toy, rhs) + toy.recovery_partial


def next_token_distribution(client: FireworksClient, prompt: str, true_next: str) -> dict[str, Any]:
    response = client.completions(
        {
            "prompt": prompt,
            "max_tokens": 1,
            "echo": False,
            "logprobs": 5,
            "temperature": 0,
            "return_token_ids": True,
        }
    )
    logprobs = response["choices"][0]["logprobs"]
    generated_token = logprobs["tokens"][0]
    generated_logprob = float(logprobs["token_logprobs"][0])
    top = logprobs.get("top_logprobs", [{}])[0] or {}
    top_tokens = [
        {"token": token, "logprob": float(logprob)}
        for token, logprob in sorted(top.items(), key=lambda item: item[1], reverse=True)
    ]
    true_next_logprob = next(
        (item["logprob"] for item in top_tokens if item["token"] == true_next),
        None,
    )
    if true_next_logprob is None:
        direct = score_target(client, prompt, true_next)["tokens"]
        true_next_logprob = direct[0]["logprob"] if direct else None
    return {
        "generated_token": generated_token,
        "generated_logprob": generated_logprob,
        "top_tokens": top_tokens,
        "true_next_logprob": true_next_logprob,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(
    path: Path,
    model: str,
    score_rows: list[dict[str, Any]],
    forced_probe_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Toy equation-order Qwen probe",
        "",
        f"Model: `{model}`",
        "",
        "All scored targets omit the closing display delimiter. The left-hand side is always `Z =`.",
        "",
        "## Score Summary",
        "",
        "| case | condition | raw | clip2 | clip2 vs empty | clip2 vs bare |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in score_rows:
        lines.append(
            "| {case_id} | {condition} | {raw_mean:+.4f} | {clip2_mean:+.4f} | "
            "{clip2_vs_empty:+.4f} | {clip2_vs_bare:+.4f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Forced-Likelihood Recovery Probe",
            "",
            "The recovery probe asks for the probability of the true next token after",
            "the true prefix has already passed through the local mismatch induced by",
            "the reordered forecast. These values use the same forced-likelihood",
            "scoring path as the benchmark.",
            "",
            "| case | condition | partial | true next | forced token | p(true next) |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in forced_probe_rows:
        prob = row["forced_probability"]
        lines.append(
            f"| {row['case_id']} | {row['condition']} | `{row['partial']}` | "
            f"`{row['true_next']}` | `{row['forced_token']}` | {prob:.4f} |"
        )
    lines.extend(
        [
            "",
            "## One-Token Generation Diagnostic",
            "",
            "This older diagnostic asks the endpoint to generate one token and records",
            "top logprobs. It is kept for provenance; use the forced-likelihood table",
            "above for manuscript-style scoring.",
            "",
            "| case | condition | partial | true next | generated | p(true next) |",
            "|---|---|---|---:|---:|---:|",
        ]
    )
    for row in probe_rows:
        prob = row["true_next_probability"]
        prob_text = "NA" if prob is None else f"{prob:.4f}"
        lines.append(
            f"| {row['case_id']} | {row['condition']} | `{row['partial']}` | "
            f"`{row['true_next']}` | `{row['generated_token']}` | {prob_text} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(score_rows: list[dict[str, Any]], forced_probe_rows: list[dict[str, Any]]) -> None:
    print("\nScore summary:")
    for row in score_rows:
        if row["condition"] in {"true_forecast", "reordered_forecast", "wrong_symbol_forecast", "bare_B", "empty"}:
            print(
                f"{row['case_id']:7s} {row['condition']:22s} "
                f"raw={row['raw_mean']:+.4f} clip2={row['clip2_mean']:+.4f} "
                f"vs_empty={row['clip2_vs_empty']:+.4f} vs_bare={row['clip2_vs_bare']:+.4f}"
            )
    print("\nForced recovery p(true next):")
    for row in forced_probe_rows:
        print(
            f"{row['case_id']:7s} {row['condition']:22s} "
            f"p={row['forced_probability']:.4f} token={row['forced_token']!r}"
        )


if __name__ == "__main__":
    main()
