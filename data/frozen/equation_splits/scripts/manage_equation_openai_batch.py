"""Submit, check, and collect equation-cut OpenAI Batch jobs."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
OPENAI_BASE_URL = "https://api.openai.com/v1"


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("--manifest", type=Path, required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--manifest", type=Path, required=True)

    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--manifest", type=Path, required=True)

    args = parser.parse_args()
    client = OpenAIClient()
    manifest_path = resolve(args.manifest)
    manifest = read_json(manifest_path)

    if args.command == "submit":
        submit(client, manifest_path, manifest)
    elif args.command == "status":
        status(client, manifest_path, manifest)
    elif args.command == "collect":
        collect(client, manifest_path, manifest)


def submit(client: "OpenAIClient", manifest_path: Path, manifest: dict[str, Any]) -> None:
    if manifest.get("batch_id"):
        print(json.dumps({"already_submitted": True, "batch_id": manifest["batch_id"], "status": manifest.get("batch_status")}, indent=2))
        return
    request_path = resolve(Path(manifest["request_jsonl_path"]))
    upload = client.upload_batch_file(request_path)
    batch = client.create_batch(
        upload["id"],
        metadata={
            "project": "rlvr_text_prediction",
            "run": "equation_cut_pilot_5papers_p20",
            "model": manifest.get("model", ""),
            "reasoning_effort": manifest.get("reasoning_effort", "none"),
            "request_count": str(manifest.get("request_count", "")),
        },
    )
    manifest.update(
        {
            "submitted": True,
            "submitted_utc": datetime.now(timezone.utc).isoformat(),
            "input_file_id": upload["id"],
            "batch_id": batch["id"],
            "batch_status": batch.get("status"),
            "raw_batch": batch,
            "status_checks": [
                {
                    "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "status": batch.get("status"),
                    "request_counts": batch.get("request_counts"),
                    "output_file_id": batch.get("output_file_id"),
                    "error_file_id": batch.get("error_file_id"),
                }
            ],
        }
    )
    write_json(manifest_path, manifest)
    print(json.dumps({"submitted": True, "batch_id": batch["id"], "status": batch.get("status"), "request_count": manifest.get("request_count")}, indent=2))


def status(client: "OpenAIClient", manifest_path: Path, manifest: dict[str, Any]) -> None:
    batch_id = require_batch_id(manifest)
    batch = client.retrieve_batch(batch_id)
    check = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "status": batch.get("status"),
        "request_counts": batch.get("request_counts"),
        "output_file_id": batch.get("output_file_id"),
        "error_file_id": batch.get("error_file_id"),
    }
    manifest["batch_status"] = batch.get("status")
    manifest["raw_batch"] = batch
    manifest.setdefault("status_checks", []).append(check)
    write_json(manifest_path, manifest)
    print(json.dumps(check, indent=2))


def collect(client: "OpenAIClient", manifest_path: Path, manifest: dict[str, Any]) -> None:
    batch_id = require_batch_id(manifest)
    batch = client.retrieve_batch(batch_id)
    manifest["batch_status"] = batch.get("status")
    manifest["raw_batch"] = batch
    out_file_id = batch.get("output_file_id")
    err_file_id = batch.get("error_file_id")
    if not out_file_id and not err_file_id:
        write_json(manifest_path, manifest)
        print(json.dumps({"collected": False, "status": batch.get("status"), "reason": "no output/error file yet"}, indent=2))
        return

    output_dir = manifest_path.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"collected": True, "status": batch.get("status")}
    if out_file_id:
        out_path = output_dir / f"{batch_id}_output.jsonl"
        out_path.write_bytes(client.download_file(out_file_id))
        manifest["output_jsonl_path"] = str(out_path.relative_to(ROOT))
        result["output_jsonl_path"] = str(out_path)
    if err_file_id:
        err_path = output_dir / f"{batch_id}_errors.jsonl"
        err_path.write_bytes(client.download_file(err_file_id))
        manifest["error_jsonl_path"] = str(err_path.relative_to(ROOT))
        result["error_jsonl_path"] = str(err_path)
    write_json(manifest_path, manifest)
    print(json.dumps(result, indent=2))


def require_batch_id(manifest: dict[str, Any]) -> str:
    batch_id = manifest.get("batch_id")
    if not batch_id:
        raise RuntimeError("Manifest has no batch_id; submit first.")
    return str(batch_id)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class OpenAIClient:
    def __init__(self, base_url: str = OPENAI_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def upload_batch_file(self, path: Path) -> dict[str, Any]:
        with path.open("rb") as handle:
            response = requests.post(
                f"{self.base_url}/files",
                headers=self.headers,
                data={"purpose": "batch"},
                files={"file": (path.name, handle, "application/jsonl")},
                timeout=120,
            )
        return checked_json(response, "upload batch file")

    def create_batch(self, input_file_id: str, metadata: dict[str, str]) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/batches",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "input_file_id": input_file_id,
                "endpoint": "/v1/responses",
                "completion_window": "24h",
                "metadata": metadata,
            },
            timeout=120,
        )
        return checked_json(response, "create batch")

    def retrieve_batch(self, batch_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/batches/{batch_id}",
            headers=self.headers,
            timeout=120,
        )
        return checked_json(response, "retrieve batch")

    def download_file(self, file_id: str) -> bytes:
        response = requests.get(
            f"{self.base_url}/files/{file_id}/content",
            headers=self.headers,
            timeout=300,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"download file failed: HTTP {response.status_code}: {response.text[:1000]}")
        return response.content


def checked_json(response: requests.Response, action: str) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError(f"{action} returned non-JSON HTTP {response.status_code}: {response.text[:1000]}") from exc
    if response.status_code >= 400:
        raise RuntimeError(f"{action} failed: HTTP {response.status_code}: {json.dumps(data)[:2000]}")
    return data


if __name__ == "__main__":
    main()
