"""Join OpenAI Batch equation-generation outputs back to the cut dataset."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = (
    ROOT
    / "experiments"
    / "2026-04-30_equation_cut_pilot_5papers_p20_v0"
    / "equation_cut_dataset_5papers_p20_v0.jsonl"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--batch-output", type=Path, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--allow-partial", action="store_true", help="Write completed rows and report errors instead of failing.")
    args = parser.parse_args()

    dataset_path = resolve(args.dataset)
    batch_output_paths = [resolve(path) for path in args.batch_output]
    out_path = resolve(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(dataset_path)
    by_custom_id = {custom_id_for_row(row): row for row in rows}
    outputs: list[dict[str, Any]] = []
    for batch_output_path in batch_output_paths:
        outputs.extend(read_jsonl(batch_output_path))

    joined: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    output_by_custom_id: dict[str, dict[str, Any]] = {}
    for item in outputs:
        output_by_custom_id[str(item.get("custom_id", ""))] = item

    for item in output_by_custom_id.values():
        custom_id = str(item.get("custom_id", ""))
        seen.add(custom_id)
        source = by_custom_id.get(custom_id)
        if source is None:
            errors.append({"custom_id": custom_id, "error": "unknown_custom_id"})
            continue
        text, extract_error = extract_output_text(item)
        if extract_error:
            errors.append({"custom_id": custom_id, "error": extract_error})
            if args.allow_partial:
                continue
        budget = int(source["budget_chars"])
        z_b = text[:budget]
        y = str(source["y"])
        joined.append(
            {
                **source,
                "generation_run_name": args.run_name,
                "custom_id": custom_id,
                "z_raw": text,
                "z_B": z_b,
                "z_len": len(text),
                "zB_len": len(z_b),
                "truncated": len(text) > budget,
                "exact_raw": text == y,
                "exact_B": z_b == y,
                "common_prefix": common_prefix_len(z_b, y),
            }
        )

    missing = sorted(set(by_custom_id) - seen)
    if missing and not args.allow_partial:
        errors.extend({"custom_id": custom_id, "error": "missing_output"} for custom_id in missing)
    if errors:
        error_path = out_path.with_suffix(".errors.json")
        error_path.write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.allow_partial:
            raise RuntimeError(f"Found {len(errors)} join errors; wrote {error_path}")

    joined.sort(key=lambda row: int(row["dataset_row_index"]))
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in joined:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    stats = summarize(joined)
    stats.update(
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "script": "scripts/join_equation_openai_outputs.py",
            "run_name": args.run_name,
            "dataset_path": str(dataset_path.relative_to(ROOT)),
            "batch_output_paths": [str(path.relative_to(ROOT)) for path in batch_output_paths],
            "joined_path": str(out_path.relative_to(ROOT)),
            "allow_partial": args.allow_partial,
            "error_count": len(errors),
        }
    )
    stats_path = out_path.with_suffix(".summary.json")
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def custom_id_for_row(row: dict[str, Any]) -> str:
    return (
        f"eq_suffix|row-{int(row['dataset_row_index']):04d}|"
        f"{row['paper_id']}|eq-{int(row['equation_index']):04d}|cut-{int(row['cut_id']):04d}"
    )


def extract_output_text(item: dict[str, Any]) -> tuple[str, str | None]:
    if item.get("error"):
        return "", f"batch_item_error:{item['error']}"
    response = item.get("response") or {}
    if int(response.get("status_code", 0)) >= 400:
        return "", f"http_status:{response.get('status_code')}"
    body = response.get("body") or {}
    if body.get("status") != "completed":
        return "", f"response_status:{body.get('status')}"

    pieces: list[str] = []
    for output in body.get("output") or []:
        for content in output.get("content") or []:
            if content.get("type") == "output_text":
                pieces.append(str(content.get("text", "")))
    if not pieces:
        return "", "no_output_text"
    return "".join(pieces), None


def common_prefix_len(left: str, right: str) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [int(row["z_len"]) for row in rows]
    prefixes = [int(row["common_prefix"]) for row in rows]
    return {
        "row_count": len(rows),
        "z_len_min": min(lengths) if lengths else None,
        "z_len_median": median(lengths),
        "z_len_mean": mean(lengths),
        "z_len_max": max(lengths) if lengths else None,
        "truncated_count": sum(bool(row["truncated"]) for row in rows),
        "exact_raw_count": sum(bool(row["exact_raw"]) for row in rows),
        "exact_B_count": sum(bool(row["exact_B"]) for row in rows),
        "common_prefix_mean": mean(prefixes),
        "common_prefix_median": median(prefixes),
    }


def mean(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def median(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


if __name__ == "__main__":
    main()
