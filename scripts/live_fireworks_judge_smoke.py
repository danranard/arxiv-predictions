from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.io_utils import read_jsonl, write_json
from equation_splits_repro.metrics import metric_score


FIREWORKS_COMPLETIONS_URL = "https://api.fireworks.ai/inference/v1/completions"
JUDGE_MODELS = {
    "qwen3_8b": "accounts/fireworks/models/qwen3-8b",
    "kimi_k2p6": "accounts/fireworks/models/kimi-k2p6",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiny live Fireworks logprob smoke against one frozen row.")
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "frozen")
    parser.add_argument("--judge", choices=sorted(JUDGE_MODELS), default="qwen3_8b")
    parser.add_argument("--lane", default="gpt55_medium")
    parser.add_argument("--row-id", type=int, default=0)
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "live_smoke" / "fireworks_judge_smoke.json")
    parser.add_argument("--strict-tolerance", type=float, default=None)
    parser.add_argument("--prompt-cache-key", default=None, help="Optional Fireworks routing-affinity/cache key.")
    parser.add_argument("--seed", type=int, default=None, help="Optional Fireworks sampling seed.")
    parser.add_argument("--max-tokens", type=int, default=1, help="Number of completion tokens to request after echo.")
    parser.add_argument("--return-token-ids", action="store_true", help="Ask Fireworks to return token ids.")
    parser.add_argument("--raw-output", action="store_true", help="Ask Fireworks to include raw output details.")
    parser.add_argument(
        "--explicit-default-sampling",
        action="store_true",
        help="Pin neutral sampling/filtering parameters instead of relying on model defaults.",
    )
    parser.add_argument(
        "--include-target-token-details",
        action="store_true",
        help="Save target-token offsets/tokens/logprobs for debugging tiny live smokes.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        raise SystemExit("FIREWORKS_API_KEY is not set")

    data_root = args.data_root if args.data_root.is_absolute() else ROOT / args.data_root
    out = args.out if args.out.is_absolute() else ROOT / args.out
    row = load_generation_row(data_root, args.lane, args.row_id)
    prompt = scaffold_prompt(row, str(row["z_B"]))
    target = target_text(row)
    frozen = load_frozen_scores(data_root, args.judge, args.lane, args.row_id)
    fresh = score_fireworks(
        api_key,
        JUDGE_MODELS[args.judge],
        prompt,
        target,
        prompt_cache_key=args.prompt_cache_key,
        seed=args.seed,
        max_tokens=args.max_tokens,
        return_token_ids=args.return_token_ids,
        raw_output=args.raw_output,
        explicit_default_sampling=args.explicit_default_sampling,
        include_target_token_details=args.include_target_token_details,
    )
    result = {
        "judge": args.judge,
        "model": JUDGE_MODELS[args.judge],
        "lane": args.lane,
        "row_id": args.row_id,
        "paper_id": row["paper_id"],
        "cut_id": row["cut_id"],
        "prompt_chars": len(prompt),
        "target_chars": len(target),
        "fresh": fresh,
        "frozen": frozen,
        "delta": {
            "raw_per_token": fresh["raw_per_token"] - frozen["raw_per_token"],
            "clip2": fresh["clip2"] - frozen["clip2"],
            "target_token_count": fresh["target_token_count"] - frozen["target_token_count"],
        },
    }
    write_json(out, result)
    if args.strict_tolerance is not None:
        delta = abs(result["delta"]["clip2"])
        if delta > args.strict_tolerance:
            raise SystemExit(f"Live clip2 delta {delta:.6f} exceeded tolerance {args.strict_tolerance}")
    print(json.dumps({k: result[k] for k in ("judge", "model", "lane", "row_id", "delta")}, indent=2))
    print(f"Wrote live smoke result to {out}")


def load_generation_row(data_root: Path, lane: str, row_id: int) -> dict[str, Any]:
    path = data_root / "generations" / lane / f"{lane}_joined_stripped.jsonl"
    for row in read_jsonl(path):
        if int(row["dataset_row_index"]) == row_id:
            return row
    raise RuntimeError(f"Missing row {row_id} in {path}")


def target_text(row: dict[str, Any]) -> str:
    env = str(row["env"])
    return str(row["y"]) + "\n" + env_close(env)


def scaffold_prompt(row: dict[str, Any], z: str) -> str:
    env = str(row["env"])
    open_delim = env_open(env)
    close_delim = env_close(env)
    x_eq = str(row["x_eq"])
    return (
        "% First equation:\n"
        f"{open_delim}\n"
        f"{x_eq}{z}\n"
        f"{close_delim}\n\n"
        "% Same equation:\n"
        f"{open_delim}\n"
        f"{x_eq}"
    )


def env_open(env: str) -> str:
    return r"\[" if env == "bracket-display" else f"\\begin{{{env}}}"


def env_close(env: str) -> str:
    return r"\]" if env == "bracket-display" else f"\\end{{{env}}}"


def load_frozen_scores(data_root: Path, judge: str, lane: str, row_id: int) -> dict[str, Any]:
    score_dir = "small_qwen_current_full731" if judge == "qwen3_8b" else "kimi_k2p6_current_full731"
    path = data_root / "scores" / score_dir / "combined_target_token_logprobs.csv"
    logprobs: list[float] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["model_lane"] == lane and row["condition"] == "scaffold_z_predictor" and int(row["dataset_row_index"]) == row_id:
                logprobs.append(float(row["token_logprob"]))
    if not logprobs:
        raise RuntimeError(f"No frozen token logprobs for {judge} {lane} row {row_id}")
    return {
        "target_token_count": len(logprobs),
        "raw_per_token": sum(logprobs) / len(logprobs),
        "clip2": metric_score(logprobs, "clip2"),
    }


def score_fireworks(
    api_key: str,
    model: str,
    prompt: str,
    target: str,
    *,
    prompt_cache_key: str | None = None,
    seed: int | None = None,
    max_tokens: int = 1,
    return_token_ids: bool = False,
    raw_output: bool = False,
    explicit_default_sampling: bool = False,
    include_target_token_details: bool = False,
) -> dict[str, Any]:
    full_prompt = prompt + target
    body = {
        "model": model,
        "prompt": full_prompt,
        "max_tokens": max_tokens,
        "echo": True,
        "logprobs": 1,
        "temperature": 0,
    }
    if prompt_cache_key is not None:
        body["prompt_cache_key"] = prompt_cache_key
    if seed is not None:
        body["seed"] = seed
    if return_token_ids:
        body["return_token_ids"] = True
    if raw_output:
        body["raw_output"] = True
    if explicit_default_sampling:
        body.update(
            {
                "top_p": 1,
                "top_k": 0,
                "min_p": 0,
                "typical_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "repetition_penalty": 1,
            }
        )
    data = post_json(FIREWORKS_COMPLETIONS_URL, api_key, body)
    payload = extract_logprobs(data)
    offsets = normalized_text_offsets(payload, full_prompt)
    boundary = len(prompt)
    target_end = len(full_prompt)
    token_logprobs = payload["token_logprobs"]
    tokens = payload.get("tokens") or []
    token_ids = payload.get("token_ids") or []
    target_indices = [
        idx
        for idx, (lp, offset) in enumerate(zip(token_logprobs, offsets))
        if lp is not None and boundary <= int(offset) < target_end
    ]
    target_logprobs = [
        float(token_logprobs[idx])
        for idx in target_indices
    ]
    if not target_logprobs:
        raise RuntimeError("Live Fireworks response contained no target-token logprobs")
    target_token_ids = [
        int(token_ids[idx])
        for idx in target_indices
        if idx < len(token_ids) and token_ids[idx] is not None
    ]
    result = {
        "target_token_count": len(target_logprobs),
        "raw_per_token": sum(target_logprobs) / len(target_logprobs),
        "clip2": metric_score(target_logprobs, "clip2"),
        "usage": data.get("usage"),
        "response_model": data.get("model"),
    }
    if target_token_ids:
        digest = hashlib.sha256(",".join(map(str, target_token_ids)).encode("utf-8")).hexdigest()
        result["target_token_ids_sha256"] = digest
    if include_target_token_details:
        details = []
        for idx in target_indices:
            details.append(
                {
                    "index": idx,
                    "offset": offsets[idx],
                    "token": tokens[idx] if idx < len(tokens) else None,
                    "token_id": token_ids[idx] if idx < len(token_ids) else None,
                    "logprob": token_logprobs[idx],
                }
            )
        result["target_token_details"] = details
    if raw_output and isinstance(data.get("choices"), list) and data["choices"]:
        choice = data["choices"][0]
        raw = choice.get("raw_output")
        if isinstance(raw, dict):
            prompt_ids = raw.get("prompt_token_ids")
            completion_ids = raw.get("completion_token_ids")
            result["raw_output_summary"] = {
                "prompt_token_count": len(prompt_ids) if isinstance(prompt_ids, list) else None,
                "completion_token_count": len(completion_ids) if isinstance(completion_ids, list) else None,
            }
    return result


def post_json(url: str, api_key: str, body: dict[str, Any]) -> dict[str, Any]:
    try:
        import requests  # type: ignore
    except ImportError:
        requests = None
    if requests is not None:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
            timeout=90,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Fireworks HTTP {response.status_code}: {response.text[:1000]}")
        return response.json()

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "equation-splits-repro-live-smoke/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Fireworks HTTP {exc.code}: {text[:1000]}") from exc


def extract_logprobs(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        logprobs = choices[0].get("logprobs")
        if isinstance(logprobs, dict) and isinstance(logprobs.get("token_logprobs"), list):
            return logprobs
    raise RuntimeError("Fireworks response did not contain completion logprobs")


def normalized_text_offsets(payload: dict[str, Any], source_text: str) -> list[int]:
    offsets = [int(offset) for offset in payload.get("text_offset") or []]
    if not offsets:
        raise RuntimeError("Fireworks response did not contain text offsets")
    tokens = payload.get("tokens")
    if not isinstance(tokens, list) or len(tokens) < 2:
        return offsets
    first = tokens[0]
    if not isinstance(first, str) or source_text.startswith(first):
        return offsets
    if first.startswith("<") and first.endswith(">") and offsets[1] == len(first):
        return [offsets[0], *[offset - len(first) for offset in offsets[1:]]]
    return offsets


if __name__ == "__main__":
    main()
