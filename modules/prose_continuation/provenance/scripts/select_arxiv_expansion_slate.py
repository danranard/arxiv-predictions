"""Select a pre-scoring arXiv expansion slate with lightweight eyeball flags."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from list_recent_arxiv_candidates import query_arxiv_list_pages  # noqa: E402


USED_REGISTRY = ROOT / "USED_PAPERS.md"
DEFAULT_OUTPUT_DIR = ROOT / "training documents" / "arxiv sources"

CORE_CATEGORIES = {"quant-ph", "hep-th", "math-ph"}
GOOD_AUX_CATEGORIES = {
    "gr-qc",
    "cond-mat.stat-mech",
    "cond-mat.str-el",
    "math.AP",
    "math.DG",
    "math.DS",
    "math.PR",
    "math.SP",
    "math.QA",
    "math.RT",
    "math.OA",
    "math.AG",
    "cs.CC",
    "cs.IT",
}

PROFESSIONAL_POSITIVE_TERMS = (
    "theorem",
    "proof",
    "bound",
    "algorithm",
    "complexity",
    "amplitudes",
    "holographic",
    "conformal",
    "quantum field",
    "operator",
    "symmetry",
    "entropy",
    "stochastic",
    "spectral",
    "asymptotic",
    "renormalization",
    "supersymmetric",
    "gauge",
    "black hole",
    "quantum",
)

EYE_REJECT_TERMS = (
    "phd thesis",
    "doctoral dissertation",
    "thesis",
    "primer",
    "visit to",
    "reflections on",
    "popular",
    "perspective",
    "tutorial",
    "review",
    "comment on",
    "reply to",
    "conference proceedings",
)

BORDERLINE_TERMS = (
    "submitted to",
    "to appear",
    "note on",
    "a note on",
    "comments welcome",
    "prepared for submission",
    "proceedings",
    "based on",
)

CRACKPOTISH_TERMS = (
    "theory of everything",
    "consciousness",
    "vortex",
    "aether",
    "ether",
    "anti-gravity",
    "antigravity",
    "free energy",
    "cold fusion",
    "new physics of",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--categories", nargs="+", default=["quant-ph", "hep-th", "math-ph"])
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument("--min-pages", type=int, default=25)
    parser.add_argument("--target-keep", type=int, default=40)
    parser.add_argument("--target-download", type=int, default=65)
    parser.add_argument(
        "--min-arxiv-id",
        default="2604.17000",
        help="Exclude older numeric IDs from update-driven past-week listings.",
    )
    parser.add_argument(
        "--output-prefix",
        default="2026-04-28_candidate40c",
        help="Prefix for CSV and Markdown files under the output directory.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    used_ids = read_used_ids(USED_REGISTRY)
    papers = query_arxiv_list_pages(args.categories, args.max_results)
    page_filtered = [
        paper
        for paper in papers
        if paper.pages is not None and paper.pages >= args.min_pages
    ]

    rows = []
    for paper in page_filtered:
        if paper.arxiv_id in used_ids:
            continue
        if numeric_arxiv_id_key(paper.arxiv_id) < numeric_arxiv_id_key(args.min_arxiv_id):
            continue
        rows.append(classify(paper))

    rows.sort(
        key=lambda row: (
            status_rank(row["eyeball_status"]),
            int(row["score"]),
            int(row["pages"]),
            row["arxiv_id"],
        ),
        reverse=True,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / f"{args.output_prefix}_candidate_pool.csv"
    write_csv(csv_path, rows)

    download_rows = rows[: args.target_download]
    download_path = args.output_dir / f"{args.output_prefix}_download_ids.txt"
    download_path.write_text(
        "\n".join(row["arxiv_id"] for row in download_rows) + "\n",
        encoding="utf-8",
    )

    selected_rows = [row for row in rows if row["eyeball_status"] == "keep"][: args.target_keep]
    md_path = args.output_dir / f"{args.output_prefix}_candidate_review.md"
    write_review(
        md_path,
        rows,
        selected_rows,
        download_rows,
        used_ids,
        categories=args.categories,
        min_pages=args.min_pages,
    )

    print(f"total_entries={len(papers)}")
    print(f"page_filtered={len(page_filtered)}")
    print(f"unused_page_filtered={len(rows)}")
    print(f"keep={sum(1 for row in rows if row['eyeball_status'] == 'keep')}")
    print(f"borderline={sum(1 for row in rows if row['eyeball_status'] == 'borderline')}")
    print(f"reject={sum(1 for row in rows if row['eyeball_status'] == 'reject')}")
    print(f"candidate_pool_csv={csv_path}")
    print(f"download_ids={download_path}")
    print(f"review_md={md_path}")
    return 0


def read_used_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"`(\d{4}\.\d{4,5})`", text))


def numeric_arxiv_id_key(arxiv_id: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})\.(\d{4,5})", arxiv_id)
    if not match:
        return (0, 0)
    return (int(match.group(1)), int(match.group(2)))


def classify(paper) -> dict[str, str | int]:
    title = paper.title or ""
    comments = paper.comments or ""
    cats = paper.categories or []
    haystack = f"{title} {comments} {paper.summary}".lower()
    reasons: list[str] = []

    score = int(paper.score)
    core_count = sum(1 for category in cats if category in CORE_CATEGORIES)
    aux_count = sum(1 for category in cats if category in GOOD_AUX_CATEGORIES)
    score += 4 * core_count + aux_count

    positive_hits = [term for term in PROFESSIONAL_POSITIVE_TERMS if term in haystack]
    score += min(len(positive_hits), 6)
    if positive_hits:
        reasons.append("technical terms: " + ", ".join(positive_hits[:4]))

    reject_hits = [term for term in EYE_REJECT_TERMS if term in haystack]
    crackpot_hits = [term for term in CRACKPOTISH_TERMS if term in haystack]
    borderline_hits = [term for term in BORDERLINE_TERMS if term in haystack]

    if crackpot_hits:
        status = "reject"
        reasons.append("crackpot-ish flag: " + ", ".join(crackpot_hits))
        score -= 25
    elif reject_hits:
        status = "reject"
        reasons.append("professional-fit reject flag: " + ", ".join(reject_hits))
        score -= 12
    elif core_count == 0:
        status = "borderline"
        reasons.append("no core category despite category-page match")
        score -= 4
    elif paper.pages and paper.pages > 160:
        status = "borderline"
        reasons.append("very long; likely thesis/monograph/manual-like")
        score -= 4
    elif borderline_hits:
        status = "borderline"
        reasons.append("eyeball-check phrase: " + ", ".join(borderline_hits[:3]))
        score -= 2
    else:
        status = "keep"
        reasons.append("looks like ordinary technical arXiv paper")

    return {
        "arxiv_id": paper.arxiv_id,
        "title": title,
        "eyeball_status": status,
        "eyeball_reasons": "; ".join(reasons),
        "score": score,
        "pages": paper.pages or 0,
        "primary_category": paper.primary_category,
        "categories": " ".join(cats),
        "comments": comments,
        "link": f"https://arxiv.org/abs/{paper.arxiv_id}",
    }


def status_rank(status: str) -> int:
    return {"keep": 2, "borderline": 1, "reject": 0}.get(status, -1)


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_review(
    path: Path,
    rows: list[dict[str, str | int]],
    selected_rows: list[dict[str, str | int]],
    download_rows: list[dict[str, str | int]],
    used_ids: set[str],
    categories: list[str],
    min_pages: int,
) -> None:
    lines = [
        "# Candidate 40C Review",
        "",
        "Pre-scoring candidate slate generated from arXiv past-week category pages.",
        "",
        "Selection settings:",
        "",
        f"- categories: `{', '.join(categories)}`",
        f"- min_pages: `{min_pages}`",
        f"- excluded registry IDs: `{len(used_ids)}`",
        f"- unused page-qualified candidates: `{len(rows)}`",
        f"- provisional download set: `{len(download_rows)}`",
        f"- provisional keep set before source validation: `{len(selected_rows)}`",
        "",
        "The eyeball scan is deliberately conservative. `borderline` rows are",
        "not necessarily bad; they are the likely hand-review positives.",
        "",
        "## Provisional Keep 40",
        "",
    ]
    for index, row in enumerate(selected_rows, start=1):
        lines.append(
            f"{index}. `{row['arxiv_id']}` - {row['title']} "
            f"({row['pages']} pages; {row['categories']})"
        )
        lines.append(f"   - {row['eyeball_reasons']}")
    lines.extend(["", "## Borderline / Hand-Review Candidates", ""])
    for row in [row for row in rows if row["eyeball_status"] == "borderline"][:40]:
        lines.append(
            f"- `{row['arxiv_id']}` - {row['title']} "
            f"({row['pages']} pages; {row['categories']})"
        )
        lines.append(f"  - {row['eyeball_reasons']}")
    lines.extend(["", "## Rejected By Eyeball Flags", ""])
    for row in [row for row in rows if row["eyeball_status"] == "reject"][:40]:
        lines.append(
            f"- `{row['arxiv_id']}` - {row['title']} "
            f"({row['pages']} pages; {row['categories']})"
        )
        lines.append(f"  - {row['eyeball_reasons']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
