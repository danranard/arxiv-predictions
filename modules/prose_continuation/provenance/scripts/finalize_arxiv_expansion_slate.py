"""Finalize a source-validated arXiv expansion slate."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "training documents" / "arxiv sources"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-csv", type=Path, required=True)
    parser.add_argument("--source-summary-csv", type=Path, required=True)
    parser.add_argument("--output-prefix", default="2026-04-28_candidate40c")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--target", type=int, default=40)
    parser.add_argument(
        "--exclude-ids",
        nargs="*",
        default=[],
        help="Additional IDs to skip after dry-run cut validation.",
    )
    args = parser.parse_args()

    candidates = read_rows(args.candidate_csv)
    source_by_id = {row["arxiv_id"]: row for row in read_rows(args.source_summary_csv)}

    final_rows = []
    rejected_rows = []
    for row in candidates:
        source = source_by_id.get(row["arxiv_id"])
        if row.get("eyeball_status") != "keep":
            continue
        if row["arxiv_id"] in set(args.exclude_ids):
            rejected = {**row, "source_validation_reason": "excluded after cut-manifest validation"}
            if source:
                rejected.update(
                    {
                        "source_status": source.get("status", ""),
                        "archive_kind": source.get("archive_kind", ""),
                        "main_path": source.get("main_path", ""),
                        "main_chars": source.get("main_chars", ""),
                        "own_body_chars": source.get("own_body_chars", ""),
                        "included_tex_chars": source.get("included_tex_chars", ""),
                        "container_like": source.get("container_like", ""),
                        "container_reason": source.get("container_reason", ""),
                        "promoted_to": source.get("promoted_to", ""),
                    }
                )
            rejected_rows.append(rejected)
            continue
        ok, reason = source_ok(source)
        merged = {**row}
        if source:
            merged.update(
                {
                    "source_status": source.get("status", ""),
                    "archive_kind": source.get("archive_kind", ""),
                    "main_path": source.get("main_path", ""),
                    "main_chars": source.get("main_chars", ""),
                    "own_body_chars": source.get("own_body_chars", ""),
                    "included_tex_chars": source.get("included_tex_chars", ""),
                    "container_like": source.get("container_like", ""),
                    "container_reason": source.get("container_reason", ""),
                    "promoted_to": source.get("promoted_to", ""),
                }
            )
        merged["source_validation_reason"] = reason
        if ok and len(final_rows) < args.target:
            final_rows.append(merged)
        elif not ok:
            rejected_rows.append(merged)

    if len(final_rows) < args.target:
        raise RuntimeError(f"Only found {len(final_rows)} source-valid rows")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    final_csv = args.output_dir / f"{args.output_prefix}_final40_source_validated.csv"
    rejected_csv = args.output_dir / f"{args.output_prefix}_source_rejects.csv"
    ids_txt = args.output_dir / f"{args.output_prefix}_final40_ids.txt"
    review_md = args.output_dir / f"{args.output_prefix}_final40_review.md"

    write_csv(final_csv, final_rows)
    write_csv(rejected_csv, rejected_rows)
    ids_txt.write_text("\n".join(row["arxiv_id"] for row in final_rows) + "\n", encoding="utf-8")
    write_review(review_md, final_rows, rejected_rows)

    print(f"final_rows={len(final_rows)}")
    print(f"source_rejects={len(rejected_rows)}")
    print(f"final_csv={final_csv}")
    print(f"source_rejects_csv={rejected_csv}")
    print(f"ids_txt={ids_txt}")
    print(f"review_md={review_md}")
    return 0


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def source_ok(source: dict[str, str] | None) -> tuple[bool, str]:
    if source is None:
        return False, "not downloaded/source summary missing"
    if source.get("status") != "ok":
        return False, f"download failed: {source.get('error', '')}"
    if source.get("main_path", "") == "":
        return False, "no TeX main candidate"
    if source.get("has_documentclass") != "True" or source.get("has_begin_document") != "True":
        return False, "main candidate lacks documentclass or begin document"
    if source.get("container_like") == "True":
        return False, "container-like main TeX"
    try:
        own_body_chars = int(source.get("own_body_chars") or 0)
    except ValueError:
        own_body_chars = 0
    if own_body_chars < 25000:
        return False, f"too little direct body text: {own_body_chars}"
    return True, "source-valid"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_review(
    path: Path, final_rows: list[dict[str, str]], rejected_rows: list[dict[str, str]]
) -> None:
    lines = [
        "# Candidate 40C Final Source-Validated Slate",
        "",
        "Chosen before any predictor or judge scoring. The slate excludes all IDs",
        "in `USED_PAPERS.md`, uses arXiv past-week category pages for",
        "`quant-ph`, `hep-th`, and `math-ph`, applies a lightweight professional-fit",
        "eyeball scan, then requires a usable promoted main TeX source.",
        "",
        "## Final 40",
        "",
    ]
    for index, row in enumerate(final_rows, start=1):
        lines.append(
            f"{index}. `{row['arxiv_id']}` - {row['title']} "
            f"({row['pages']} pages; {row['categories']})"
        )
        lines.append(
            f"   - source: `{row.get('main_path', '')}`, own_body_chars={row.get('own_body_chars', '')}, "
            f"included_tex_chars={row.get('included_tex_chars', '')}"
        )
        lines.append(f"   - scan: {row.get('eyeball_reasons', '')}")
    lines.extend(["", "## Source Rejects From Downloaded Keep Candidates", ""])
    for row in rejected_rows:
        lines.append(f"- `{row['arxiv_id']}` - {row['title']}")
        lines.append(f"  - {row.get('source_validation_reason', '')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
