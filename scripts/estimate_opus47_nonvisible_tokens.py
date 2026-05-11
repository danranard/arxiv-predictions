from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "frozen" / "equation_splits"
OUT_DIR = DATA_ROOT / "derived"
OUT_ROWS = OUT_DIR / "opus47_usage_anthropic_token_estimates.csv"
OUT_SUMMARY = OUT_DIR / "opus47_usage_anthropic_token_estimates_summary.json"

GENERATION_FILES = {
    ("old731", "opus47_low"): DATA_ROOT
    / "generations"
    / "old731"
    / "opus47_low"
    / "claude_opus47_low_partial_joined.jsonl",
    ("old731", "opus47_medium"): DATA_ROOT
    / "generations"
    / "old731"
    / "opus47_medium"
    / "claude_opus47_medium_partial_joined.jsonl",
    ("new632", "opus47_low"): DATA_ROOT
    / "generations"
    / "new632"
    / "opus47_low"
    / "claude_opus47_low_new632_current_joined.jsonl",
    ("new632", "opus47_medium"): DATA_ROOT
    / "generations"
    / "new632"
    / "opus47_medium"
    / "claude_opus47_medium_new632_current_joined.jsonl",
}

FIELDNAMES = [
    "component_bundle",
    "model_lane",
    "paper_id",
    "cut_id",
    "super_key",
    "anthropic_request_id",
    "anthropic_output_tokens",
    "visible_forecast_anthropic_message_tokens",
    "message_overhead_tokens_subtracted",
    "visible_forecast_anthropic_tokens",
    "estimated_nonvisible_output_tokens",
    "z_chars",
    "count_model",
    "count_method",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate Opus 4.7 non-visible output tokens using Anthropic count_tokens."
    )
    parser.add_argument("--model", default="claude-opus-4-7")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--save-every", type=int, default=25)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument(
        "--message-overhead-tokens",
        type=int,
        default=11,
        help="Subtract this fixed single-message overhead from count_tokens results for visible-text estimates.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is required.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pending = build_rows(args.model)
    if args.limit is not None:
        pending = pending[: args.limit]

    existing = read_existing(OUT_ROWS)
    todo = [row for row in pending if row_key(row) not in existing]
    print(json.dumps({"total_rows": len(pending), "cached_rows": len(existing), "todo_rows": len(todo)}, indent=2))

    completed = dict(existing)
    done_since_save = 0
    with ThreadPoolExecutor(max_workers=max(args.workers, 1)) as executor:
        futures = {executor.submit(count_one, row, api_key, args.model, args.sleep): row for row in todo}
        for future in as_completed(futures):
            row = future.result()
            apply_overhead(row, args.message_overhead_tokens)
            completed[row_key(row)] = row
            done_since_save += 1
            if done_since_save >= args.save_every:
                write_rows(OUT_ROWS, completed.values())
                write_summary(OUT_SUMMARY, completed.values(), args.model)
                print(json.dumps({"saved_rows": len(completed), "remaining": len(pending) - len(completed)}))
                done_since_save = 0

    for row in completed.values():
        apply_overhead(row, args.message_overhead_tokens)
    write_rows(OUT_ROWS, completed.values())
    summary = write_summary(OUT_SUMMARY, completed.values(), args.model, args.message_overhead_tokens)
    print(json.dumps(summary, indent=2))


def build_rows(model: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (component, lane), path in GENERATION_FILES.items():
        for raw in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(raw)
            output_tokens = item["anthropic_usage"]["output_tokens"]
            z = item.get("z_raw") or ""
            super_key = item.get("super_key") or f"{component}:{item['paper_id']}:{item['cut_id']}"
            rows.append(
                {
                    "component_bundle": component,
                    "model_lane": lane,
                    "paper_id": item["paper_id"],
                    "cut_id": str(item["cut_id"]),
                    "super_key": super_key,
                    "anthropic_request_id": item.get("anthropic_request_id", ""),
                    "anthropic_output_tokens": int(output_tokens),
                    "z_raw": z,
                    "z_chars": len(z),
                    "count_model": model,
                    "count_method": "Anthropic messages/count_tokens on visible z_raw, adjusted by subtracting a single-message overhead estimate.",
                }
            )
    rows.sort(key=lambda r: (r["component_bundle"], r["model_lane"], r["paper_id"], int(r["cut_id"])))
    return rows


def count_one(row: dict[str, Any], api_key: str, model: str, sleep: float) -> dict[str, Any]:
    if sleep:
        time.sleep(sleep)
    visible_tokens = anthropic_count_tokens(api_key, model, row["z_raw"])
    out = {key: row[key] for key in FIELDNAMES if key in row}
    out["visible_forecast_anthropic_message_tokens"] = visible_tokens
    return out


def apply_overhead(row: dict[str, Any], message_overhead_tokens: int) -> None:
    raw = int(row.get("visible_forecast_anthropic_message_tokens", row.get("visible_forecast_anthropic_tokens", 0)))
    row["visible_forecast_anthropic_message_tokens"] = raw
    row["message_overhead_tokens_subtracted"] = message_overhead_tokens
    visible = max(0, raw - message_overhead_tokens)
    row["visible_forecast_anthropic_tokens"] = visible
    row["estimated_nonvisible_output_tokens"] = int(row["anthropic_output_tokens"]) - visible


def anthropic_count_tokens(api_key: str, model: str, content: str) -> int:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages/count_tokens",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    delay = 2.0
    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read().decode("utf-8")
            return int(json.loads(body)["input_tokens"])
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in {429, 500, 502, 503, 504} and attempt < 7:
                retry_after = exc.headers.get("retry-after")
                wait = float(retry_after) if retry_after else delay
                time.sleep(wait)
                delay = min(delay * 1.8, 60.0)
                continue
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Anthropic count_tokens failed with HTTP {status}: {detail}") from exc
        except Exception:
            if attempt < 7:
                time.sleep(delay)
                delay = min(delay * 1.8, 60.0)
                continue
            raise
    raise RuntimeError("Anthropic count_tokens failed after retries.")


def row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row["component_bundle"]), str(row["model_lane"]), str(row["super_key"]))


def read_existing(path: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            for key in [
                "anthropic_output_tokens",
                "visible_forecast_anthropic_message_tokens",
                "message_overhead_tokens_subtracted",
                "visible_forecast_anthropic_tokens",
                "estimated_nonvisible_output_tokens",
                "z_chars",
            ]:
                if key in row:
                    row[key] = int(row[key])
            if "visible_forecast_anthropic_message_tokens" not in row:
                row["visible_forecast_anthropic_message_tokens"] = int(row["visible_forecast_anthropic_tokens"])
            out[row_key(row)] = row
    return out


def write_rows(path: Path, rows: Any) -> None:
    ordered = sorted(rows, key=lambda r: (r["component_bundle"], r["model_lane"], r["paper_id"], int(r["cut_id"])))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(ordered)


def write_summary(path: Path, rows: Any, model: str, message_overhead_tokens: int) -> dict[str, Any]:
    rows = list(rows)
    by_lane: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_lane.setdefault(row["model_lane"], []).append(row)
    summary = {
        "created_from": "frozen Anthropic Opus 4.7 generation rows",
        "count_model": model,
        "count_endpoint": "https://api.anthropic.com/v1/messages/count_tokens",
        "message_overhead_tokens_subtracted": message_overhead_tokens,
        "method_note": (
            "For each saved Opus row, visible_forecast_anthropic_message_tokens is the Anthropic "
            "count_tokens result for z_raw as a single user message. Because count_tokens counts "
            "message structure as well as text, visible_forecast_anthropic_tokens subtracts a fixed "
            "single-message overhead estimated from a one-character probe. estimated_nonvisible_output_tokens "
            "is saved anthropic_usage.output_tokens minus that adjusted visible-token estimate. Anthropic "
            "does not expose a separate hidden-thinking token field in these saved rows. Opus 4.7 may "
            "also use tokenizer/accounting details not shared with earlier Claude models or OpenAI models."
        ),
        "overall_n": len(rows),
        "lanes": {},
    }
    for lane, lane_rows in sorted(by_lane.items()):
        hidden = [int(row["estimated_nonvisible_output_tokens"]) for row in lane_rows]
        visible = [int(row["visible_forecast_anthropic_tokens"]) for row in lane_rows]
        output = [int(row["anthropic_output_tokens"]) for row in lane_rows]
        summary["lanes"][lane] = {
            "n": len(lane_rows),
            "mean_output_tokens": statistics.mean(output),
            "mean_visible_forecast_anthropic_tokens": statistics.mean(visible),
            "mean_estimated_nonvisible_output_tokens": statistics.mean(hidden),
            "median_estimated_nonvisible_output_tokens": statistics.median(hidden),
        }
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    main()
