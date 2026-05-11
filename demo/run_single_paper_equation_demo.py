from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pilot_equation_cut_prompts import build_cuts, clean_tex, env_close  # noqa: E402


DEMO = ROOT / "demo"
SOURCE_TEX = DEMO / "arxiv_2307_05326" / "arxiv-2307-05326.tex"
FROZEN = DEMO / "frozen"
CUTS = FROZEN / "cuts_demo10.jsonl"
GENERATIONS = FROZEN / "generations_demo10.jsonl"
SCORES = FROZEN / "qwen3_8b_scores_demo10.csv"
TOKEN_SCORES = FROZEN / "qwen3_8b_token_logprobs_demo10.csv"
REPORT = FROZEN / "report.md"

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
FIREWORKS_COMPLETIONS_URL = "https://api.fireworks.ai/inference/v1/completions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or inspect the single-paper equation-suffix demo.")
    parser.add_argument("--rebuild-cuts", action="store_true", help="Rebuild the deterministic 10-cut demo set.")
    parser.add_argument("--show-cuts", action="store_true", help="Print selected X/Y snippets.")
    parser.add_argument("--call-openai", action="store_true", help="Regenerate nano low/high forecasts using OpenAI.")
    parser.add_argument("--call-fireworks", action="store_true", help="Regenerate Qwen3-8B logprob scores using Fireworks.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing live-generation or score files.")
    parser.add_argument("--openai-model", default="gpt-5.4-nano")
    parser.add_argument("--openai-low-effort", default="low")
    parser.add_argument("--openai-medium-effort", default="medium")
    parser.add_argument("--max-output-tokens", type=int, default=220)
    parser.add_argument("--retry-empty", action="store_true", help="When regenerating, only retry empty existing outputs.")
    parser.add_argument("--fireworks-model", default="accounts/fireworks/models/qwen3-8b")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay between OpenAI calls.")
    args = parser.parse_args()

    FROZEN.mkdir(parents=True, exist_ok=True)
    if args.rebuild_cuts:
        rebuild_cuts()
    if args.show_cuts:
        show_cuts()
    if args.call_openai:
        generate_openai(args)
    if args.call_fireworks:
        score_fireworks(args)

    if not GENERATIONS.exists() or not SCORES.exists():
        print("Frozen demo generations/scores are not both present yet.")
        print("Use --call-openai --call-fireworks to create them, or --show-cuts to inspect the task without APIs.")
        return

    write_report()
    print(REPORT.read_text(encoding="utf-8"))


def rebuild_cuts() -> None:
    tex = clean_tex(SOURCE_TEX.read_text(encoding="utf-8", errors="replace"))
    cuts, stats = build_cuts(
        tex=tex,
        paper_id="2307.05326",
        y_min=50,
        y_max=400,
        slack=40,
        predictor_context_chars=10000,
        bare_tail_multiplier=1.0,
        min_predictor_context_chars=10000,
    )
    if len(cuts) < 10:
        raise SystemExit(f"Expected at least 10 accepted cuts, found {len(cuts)}")
    indices = [round(i * (len(cuts) - 1) / 9) for i in range(10)]
    selected = []
    for demo_row_index, source_cut_index in enumerate(indices):
        row = asdict(cuts[source_cut_index])
        row["demo_row_index"] = demo_row_index
        row["source_cut_index"] = source_cut_index
        selected.append(row)
    write_jsonl(CUTS, selected)
    write_json(FROZEN / "cut_selection_manifest.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_tex": str(SOURCE_TEX.relative_to(ROOT)),
        "paper_id": "2307.05326",
        "accepted_cut_count": len(cuts),
        "selected_source_cut_indices": indices,
        "selection_rule": "10 evenly spaced accepted cuts in source order",
        "extractor_stats": stats,
    })
    print(f"Wrote {CUTS} with selected indices {indices}")


def show_cuts() -> None:
    rows = read_jsonl(CUTS)
    for row in rows:
        print("=" * 80)
        print(
            f"demo_row_index={row['demo_row_index']} cut_id={row['cut_id']} "
            f"env={row['env']} op={row['operator']} y_len={row['y_len']} "
            f"line={row['cut_source_line']}"
        )
        print("\nX_eq:")
        print(clip(row["x_eq"], 700))
        print("\nY:")
        print(clip(row["y"], 700))


def generate_openai(args: argparse.Namespace) -> None:
    if GENERATIONS.exists() and not args.force and not args.retry_empty:
        raise SystemExit(f"{GENERATIONS} already exists; pass --force to overwrite.")
    api_key = require_env("OPENAI_API_KEY")
    cuts = read_jsonl(CUTS)
    existing = read_jsonl(GENERATIONS) if GENERATIONS.exists() and args.retry_empty else []
    existing_by_key = {(row["demo_row_index"], row["model_lane"]): row for row in existing}
    out_rows = [] if args.force and not args.retry_empty else [
        row for row in existing if row.get("z", "") or not args.retry_empty
    ]
    lanes = [
        ("nano_low", args.openai_low_effort),
        ("nano_medium", args.openai_medium_effort),
    ]
    for cut in cuts:
        for lane, effort in lanes:
            old = existing_by_key.get((cut["demo_row_index"], lane))
            if old is not None and old.get("z", ""):
                continue
            response = openai_response(
                api_key=api_key,
                model=args.openai_model,
                prompt=cut["predictor_prompt"],
                effort=effort,
                max_output_tokens=args.max_output_tokens,
            )
            text = extract_openai_text(response).strip()
            out_rows.append({
                "demo_row_index": cut["demo_row_index"],
                "paper_id": cut["paper_id"],
                "cut_id": cut["cut_id"],
                "model_lane": lane,
                "openai_model": args.openai_model,
                "reasoning_effort": effort,
                "z": text,
                "z_chars": len(text),
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "response_id": response.get("id"),
            })
            print(f"generated row={cut['demo_row_index']} lane={lane} chars={len(text)}", flush=True)
            if args.sleep:
                time.sleep(args.sleep)
    write_jsonl(GENERATIONS, out_rows)


def score_fireworks(args: argparse.Namespace) -> None:
    if SCORES.exists() and not args.force:
        raise SystemExit(f"{SCORES} already exists; pass --force to overwrite.")
    api_key = require_env("FIREWORKS_API_KEY")
    cuts = {row["demo_row_index"]: row for row in read_jsonl(CUTS)}
    generations = read_jsonl(GENERATIONS)
    generation_map = {(row["demo_row_index"], row["model_lane"]): row["z"] for row in generations}

    jobs = []
    for idx, cut in sorted(cuts.items()):
        jobs.append(make_job(cut, "bare_B", cut["bare_b_judge_prompt_prefix"]))
        for lane in ["nano_low", "nano_medium"]:
            z = generation_map[(idx, lane)]
            jobs.append(make_job(cut, lane, scaffold_prefix(cut, z)))

    score_rows: list[dict[str, Any]] = []
    token_rows: list[dict[str, Any]] = []
    for job in jobs:
        payload = fireworks_completion(
            api_key=api_key,
            model=args.fireworks_model,
            prompt=job["prompt"] + job["target"],
        )
        target_tokens = extract_target_tokens(payload, job["prompt"], job["target"])
        if not target_tokens:
            raise RuntimeError(f"No target tokens for row {job['demo_row_index']} condition {job['condition']}")
        raw = statistics.mean(tok["token_logprob"] for tok in target_tokens)
        clip2 = statistics.mean(max(tok["token_logprob"], -2.0) for tok in target_tokens)
        score_rows.append({
            "demo_row_index": job["demo_row_index"],
            "paper_id": job["paper_id"],
            "cut_id": job["cut_id"],
            "condition": job["condition"],
            "target_tokens": len(target_tokens),
            "raw_mean_logprob": raw,
            "clip2_mean_logprob": clip2,
            "judge_model": args.fireworks_model,
        })
        for tok in target_tokens:
            token_rows.append({
                "demo_row_index": job["demo_row_index"],
                "paper_id": job["paper_id"],
                "cut_id": job["cut_id"],
                "condition": job["condition"],
                **tok,
            })
        print(f"scored row={job['demo_row_index']} condition={job['condition']} clip2={clip2:+.4f}", flush=True)
    write_csv(SCORES, score_rows)
    write_csv(TOKEN_SCORES, token_rows)


def make_job(cut: dict[str, Any], condition: str, prefix: str) -> dict[str, Any]:
    leading = leading_whitespace(cut["y"])
    y_body = cut["y"][len(leading):]
    return {
        "demo_row_index": cut["demo_row_index"],
        "paper_id": cut["paper_id"],
        "cut_id": cut["cut_id"],
        "condition": condition,
        "prompt": prefix + leading,
        "target": y_body + "\n" + env_close(cut["env"]),
    }


def scaffold_prefix(cut: dict[str, Any], z: str) -> str:
    return (
        "% First equation:\n"
        f"{env_open(cut['env'])}\n"
        f"{cut['x_eq']}{z}\n"
        f"{env_close(cut['env'])}\n\n"
        "% Same equation:\n"
        f"{env_open(cut['env'])}\n"
        f"{cut['x_eq']}"
    )


def env_open(env: str) -> str:
    return r"\[" if env == "bracket-display" else f"\\begin{{{env}}}"


def write_report() -> None:
    scores = read_csv(SCORES)
    generations = read_jsonl(GENERATIONS)
    by_row: dict[int, dict[str, dict[str, str]]] = {}
    for row in scores:
        by_row.setdefault(int(row["demo_row_index"]), {})[row["condition"]] = row
    lines = [
        "# Single-Paper Equation Demo Report",
        "",
        "Paper: arXiv:2307.05326. This is a pipeline demo, not part of the headline benchmark.",
        "",
        "Metric: `clip2`; contrast: predictor forecast condition minus `bare_B`.",
        "",
        "| row | nano low lift | nano medium lift | bare_B clip2 | low clip2 | medium clip2 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    low_diffs = []
    medium_diffs = []
    for idx in sorted(by_row):
        row = by_row[idx]
        bare = float(row["bare_B"]["clip2_mean_logprob"])
        low = float(row["nano_low"]["clip2_mean_logprob"])
        medium = float(row["nano_medium"]["clip2_mean_logprob"])
        low_diffs.append(low - bare)
        medium_diffs.append(medium - bare)
        lines.append(f"| {idx} | {low - bare:+.4f} | {medium - bare:+.4f} | {bare:+.4f} | {low:+.4f} | {medium:+.4f} |")
    lines += [
        "",
        f"Nano low mean lift: {mean(low_diffs):+.4f} +/- {stderr(low_diffs):.4f}; positive {sum(x > 0 for x in low_diffs)}/{len(low_diffs)}.",
        f"Nano medium mean lift: {mean(medium_diffs):+.4f} +/- {stderr(medium_diffs):.4f}; positive {sum(x > 0 for x in medium_diffs)}/{len(medium_diffs)}.",
        "",
        "Interpretation note: this is a 10-cut single-paper pipeline demo. It is not meant to establish a benchmark/model-ordering result by itself; the main reported equation-suffix results use many more cuts across many papers.",
        "",
        f"Frozen generations: `{GENERATIONS.relative_to(ROOT)}` ({len(generations)} rows).",
        f"Frozen scores: `{SCORES.relative_to(ROOT)}`.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def openai_response(api_key: str, model: str, prompt: str, effort: str, max_output_tokens: int) -> dict[str, Any]:
    body = {
        "model": model,
        "input": prompt,
        "reasoning": {"effort": effort},
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    return post_json(OPENAI_RESPONSES_URL, api_key, body, timeout=180)


def extract_openai_text(response: dict[str, Any]) -> str:
    if "output_text" in response:
        return str(response["output_text"])
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                chunks.append(content.get("text", ""))
    return "".join(chunks)


def fireworks_completion(api_key: str, model: str, prompt: str) -> dict[str, Any]:
    body = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 0,
        "echo": True,
        "logprobs": 1,
        "temperature": 0,
    }
    return post_json(FIREWORKS_COMPLETIONS_URL, api_key, body, timeout=180)


def extract_target_tokens(payload: dict[str, Any], prompt: str, target: str) -> list[dict[str, Any]]:
    choice = payload["choices"][0]
    logprobs = choice["logprobs"]
    tokens = logprobs["tokens"]
    token_ids = logprobs.get("token_ids") or [""] * len(tokens)
    token_logprobs = logprobs["token_logprobs"]
    offsets = logprobs.get("text_offset")
    if offsets is None:
        raise RuntimeError("Fireworks response lacks text_offset")
    start = len(prompt)
    end = start + len(target)
    rows = []
    target_index = 0
    for full_index, (token, token_id, token_logprob, offset) in enumerate(zip(tokens, token_ids, token_logprobs, offsets)):
        if token_logprob is None:
            continue
        offset = int(offset)
        if start <= offset < end:
            lp = float(token_logprob)
            rows.append({
                "target_token_index": target_index,
                "full_token_index": full_index,
                "text_offset": offset,
                "relative_text_offset": offset - start,
                "token": token,
                "token_id": token_id,
                "token_logprob": lp,
                "clip2_logprob": max(lp, -2.0),
            })
            target_index += 1
    return rows


def post_json(url: str, api_key: str, body: dict[str, Any], timeout: int) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "rlvr-equation-demo/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is not set")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def leading_whitespace(text: str) -> str:
    idx = 0
    while idx < len(text) and text[idx].isspace():
        idx += 1
    return text[:idx]


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def stderr(values: list[float]) -> float:
    if len(values) < 2:
        return float("nan")
    return statistics.stdev(values) / math.sqrt(len(values))


def clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[clipped]..."


if __name__ == "__main__":
    main()
