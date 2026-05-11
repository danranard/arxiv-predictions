"""Run prepared equation OpenAI Responses requests via ordinary async calls.

This reads the same JSONL prepared for OpenAI Batch and writes batch-like
output JSONL so scripts/join_equation_openai_outputs.py can consume it.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
OPENAI_BASE_URL = "https://api.openai.com/v1"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-jsonl", type=Path, required=True)
    parser.add_argument("--out-jsonl", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--request-timeout", type=float, default=120.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--progress-every", type=int, default=5)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    request_path = resolve(args.request_jsonl)
    out_path = resolve(args.out_jsonl)
    summary_path = resolve(args.summary_json) if args.summary_json else out_path.with_suffix(".summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    requests_in = read_jsonl(request_path)
    if args.offset:
        requests_in = requests_in[args.offset :]
    if args.limit is not None:
        requests_in = requests_in[: args.limit]

    completed = set() if args.no_resume else completed_custom_ids(out_path)
    todo = [item for item in requests_in if str(item.get("custom_id")) not in completed]

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAIResponsesClient(api_key=api_key, timeout=args.request_timeout)

    lock = threading.Lock()
    started = time.time()
    counts = {"completed": len(completed), "new_completed": 0, "failed": 0}
    print(
        json.dumps(
            {
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "request_jsonl": str(request_path.relative_to(ROOT)),
                "out_jsonl": str(out_path.relative_to(ROOT)),
                "input_count": len(requests_in),
                "already_completed": len(completed),
                "todo_count": len(todo),
                "max_workers": args.max_workers,
            },
            indent=2,
        ),
        flush=True,
    )

    def write_result(result: dict[str, Any]) -> None:
        with lock:
            with out_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            if result.get("error"):
                counts["failed"] += 1
            else:
                counts["new_completed"] += 1
                counts["completed"] += 1
            done_now = counts["new_completed"] + counts["failed"]
            if done_now % max(args.progress_every, 1) == 0 or done_now == len(todo):
                write_summary(summary_path, request_path, out_path, requests_in, counts, started)
                print(
                    json.dumps(
                        {
                            "progress_utc": datetime.now(timezone.utc).isoformat(),
                            "done_new": done_now,
                            "todo": len(todo),
                            "completed_total": counts["completed"],
                            "failed_new": counts["failed"],
                            "elapsed_sec": round(time.time() - started, 2),
                        }
                    ),
                    flush=True,
                )

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        future_to_item = {
            pool.submit(
                call_one,
                client,
                item,
                max_retries=args.max_retries,
                retry_base_seconds=args.retry_base_seconds,
            ): item
            for item in todo
        }
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "custom_id": str(item.get("custom_id", "")),
                    "response": None,
                    "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
                }
            write_result(result)

    write_summary(summary_path, request_path, out_path, requests_in, counts, started)
    print(json.dumps(json.loads(summary_path.read_text(encoding="utf-8")), indent=2), flush=True)


class OpenAIResponsesClient:
    def __init__(self, api_key: str, timeout: float, base_url: str = OPENAI_BASE_URL) -> None:
        self.url = f"{base_url.rstrip('/')}/responses"
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def create_response(self, body: dict[str, Any]) -> tuple[int, dict[str, str], dict[str, Any] | str]:
        response = requests.post(self.url, headers=self.headers, json=body, timeout=self.timeout)
        headers = {
            "x-request-id": response.headers.get("x-request-id", ""),
            "openai-processing-ms": response.headers.get("openai-processing-ms", ""),
        }
        try:
            data: dict[str, Any] | str = response.json()
        except Exception:
            data = response.text[:4000]
        return response.status_code, headers, data


def call_one(
    client: OpenAIResponsesClient,
    item: dict[str, Any],
    *,
    max_retries: int,
    retry_base_seconds: float,
) -> dict[str, Any]:
    custom_id = str(item.get("custom_id", ""))
    body = dict(item.get("body") or {})
    last_error: dict[str, Any] | None = None
    for attempt in range(max_retries + 1):
        status_code, headers, data = client.create_response(body)
        if status_code < 400:
            return {
                "custom_id": custom_id,
                "response": {
                    "status_code": status_code,
                    "request_id": headers.get("x-request-id"),
                    "body": data,
                },
                "error": None,
            }
        last_error = {
            "status_code": status_code,
            "headers": headers,
            "body": data,
            "attempt": attempt,
        }
        if status_code not in {408, 409, 429, 500, 502, 503, 504} or attempt >= max_retries:
            break
        sleep_for = retry_base_seconds * (2**attempt) + random.random()
        time.sleep(sleep_for)
    return {
        "custom_id": custom_id,
        "response": {
            "status_code": int(last_error.get("status_code", 0)) if last_error else 0,
            "request_id": (last_error or {}).get("headers", {}).get("x-request-id"),
            "body": (last_error or {}).get("body"),
        },
        "error": {"type": "http_error", "detail": last_error},
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def completed_custom_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not item.get("error"):
                done.add(str(item.get("custom_id", "")))
    return done


def write_summary(
    path: Path,
    request_path: Path,
    out_path: Path,
    requests_in: list[dict[str, Any]],
    counts: dict[str, int],
    started: float,
) -> None:
    data = {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/run_equation_openai_responses_async.py",
        "request_jsonl": str(request_path.relative_to(ROOT)),
        "out_jsonl": str(out_path.relative_to(ROOT)),
        "input_count": len(requests_in),
        "completed_total": counts["completed"],
        "new_completed": counts["new_completed"],
        "failed_new": counts["failed"],
        "elapsed_sec": round(time.time() - started, 2),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve(path: Path | None) -> Path:
    if path is None:
        raise RuntimeError("Unexpected empty path")
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
