from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.io_utils import read_jsonl, write_json, write_text


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or run a tiny OpenAI generation smoke request.")
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "frozen")
    parser.add_argument("--row-id", type=int, default=0)
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--max-output-tokens", type=int, default=80)
    parser.add_argument("--call", action="store_true", help="Actually call OpenAI. Without this, only write request preview.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "live_smoke" / "openai_generation")
    args = parser.parse_args()

    data_root = args.data_root if args.data_root.is_absolute() else ROOT / args.data_root
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    row = load_cut_row(data_root, args.row_id)
    prompt = str(row["predictor_prompt"])
    request_body = {
        "model": args.model,
        "input": prompt,
        "max_output_tokens": args.max_output_tokens,
        "store": False,
        "tools": [],
    }
    if args.reasoning_effort:
        request_body["reasoning"] = {"effort": args.reasoning_effort}

    request_record = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "row_id": args.row_id,
        "paper_id": row["paper_id"],
        "cut_id": row["cut_id"],
        "prompt_chars": len(prompt),
        "true_y_not_sent": row["y"],
        "request_body": request_body,
    }
    write_json(out_dir / "request_preview.json", request_record)
    write_text(out_dir / "prompt_preview.txt", prompt)

    if not args.call:
        print(f"Wrote OpenAI request preview to {out_dir}; use --call to send it.")
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")
    response = post_json(OPENAI_RESPONSES_URL, api_key, request_body)
    write_json(out_dir / "response.json", response)
    text = extract_response_text(response)
    write_text(out_dir / "response_text.txt", text)
    print(json.dumps({"model": args.model, "row_id": args.row_id, "response_chars": len(text), "out_dir": str(out_dir)}, indent=2))


def load_cut_row(data_root: Path, row_id: int) -> dict[str, Any]:
    for row in read_jsonl(data_root / "data" / "cuts_731.jsonl"):
        if int(row["dataset_row_index"]) == row_id:
            return row
    raise RuntimeError(f"Missing row {row_id}")


def post_json(url: str, api_key: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {text[:1000]}") from exc


def extract_response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    chunks: list[str] = []
    for item in response.get("output", []) or []:
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "".join(chunks)


if __name__ == "__main__":
    main()

