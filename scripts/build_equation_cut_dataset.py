"""Build a larger deterministic equation-cut dataset from 2026 TeX sources."""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pilot_equation_cut_prompts as eqpilot


ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "training documents"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-cuts", type=int, default=500)
    parser.add_argument("--cuts-per-paper", type=int, default=10)
    parser.add_argument("--min-paper-cuts", type=int, default=10)
    parser.add_argument("--min-file-bytes", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=20260430)
    parser.add_argument(
        "--tex-root",
        type=Path,
        default=TRAINING,
        help="Directory containing promoted arXiv main .tex files named like arxiv-2604-17369.tex.",
    )
    parser.add_argument("--y-min", type=int, default=50)
    parser.add_argument("--y-max", type=int, default=400)
    parser.add_argument("--slack", type=int, default=40)
    parser.add_argument("--predictor-context-chars", type=int, default=10000)
    parser.add_argument("--min-predictor-context-chars", type=int, default=10000)
    parser.add_argument("--bare-tail-multiplier", type=float, default=1.0)
    parser.add_argument(
        "--exclude-paper-ids",
        nargs="*",
        default=[],
        help="Paper IDs to skip, e.g. IDs already used in a previous dataset.",
    )
    parser.add_argument(
        "--exclude-paper-ids-file",
        type=Path,
        help="Optional text/CSV file of paper IDs to skip. CSV may contain a paper_id column.",
    )
    parser.add_argument(
        "--include-paper-ids",
        nargs="*",
        default=[],
        help="If set, only scan these paper IDs.",
    )
    parser.add_argument(
        "--include-paper-ids-file",
        type=Path,
        help="Optional text/CSV file of paper IDs to scan. CSV may contain a paper_id column.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "generated_cuts",
    )
    args = parser.parse_args()

    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_root = resolve(args.tex_root)

    scan_rows: list[dict] = []
    eligible: list[dict] = []
    included_ids = {normalize_paper_id(paper_id) for paper_id in args.include_paper_ids}
    included_ids.update(load_paper_ids(args.include_paper_ids_file))
    excluded_ids = {normalize_paper_id(paper_id) for paper_id in args.exclude_paper_ids}
    excluded_ids.update(load_paper_ids(args.exclude_paper_ids_file))
    for tex_path in discover_tex_files(tex_root, args.min_file_bytes):
        paper_id = paper_id_from_path(tex_path)
        if included_ids and normalize_paper_id(paper_id) not in included_ids:
            continue
        if normalize_paper_id(paper_id) in excluded_ids:
            scan_rows.append(
                {
                    "paper_id": paper_id,
                    "tex_file": relpath(tex_path),
                    "status": "excluded",
                    "reason": "paper_id_excluded",
                }
            )
            continue
        try:
            tex = eqpilot.clean_tex(tex_path.read_text(encoding="utf-8", errors="replace"))
            cuts, stats = eqpilot.build_cuts(
                tex,
                paper_id,
                args.y_min,
                args.y_max,
                args.slack,
                args.predictor_context_chars,
                args.bare_tail_multiplier,
                args.min_predictor_context_chars,
            )
        except Exception as exc:
            scan_rows.append(
                {
                    "paper_id": paper_id,
                    "tex_file": relpath(tex_path),
                    "status": "error",
                    "error": repr(exc),
                }
            )
            continue

        title = extract_title(tex)
        scan_row = {
            "paper_id": paper_id,
            "title": title,
            "tex_file": relpath(tex_path),
            "status": "eligible" if len(cuts) >= args.min_paper_cuts else "too_few_cuts",
            "file_bytes": tex_path.stat().st_size,
            "qualifying_cuts": len(cuts),
            "display_equations": stats["display_equations"],
            "stats": stats,
        }
        scan_rows.append(scan_row)
        if len(cuts) >= args.min_paper_cuts:
            eligible.append({"path": tex_path, "paper_id": paper_id, "title": title, "cuts": cuts, "stats": stats})

    if not eligible:
        raise RuntimeError("No eligible papers found.")

    rng = random.Random(args.seed)
    rng.shuffle(eligible)

    selected_rows: list[dict] = []
    paper_summaries: list[dict] = []
    for paper_rank, item in enumerate(eligible):
        if len(selected_rows) >= args.target_cuts:
            break
        needed = args.target_cuts - len(selected_rows)
        count = min(args.cuts_per_paper, needed, len(item["cuts"]))
        selected = choose_spread_cuts(item["cuts"], count, seed=args.seed + 1009 * paper_rank)
        selected_ids = {cut.cut_id for cut in selected}
        sorted_all = sorted(item["cuts"], key=lambda c: (c.cut_source_line, c.cut_source_char, c.cut_id))
        source_rank = {cut.cut_id: idx for idx, cut in enumerate(sorted_all)}
        paper_summaries.append(
            {
                "paper_id": item["paper_id"],
                "title": item["title"],
                "tex_file": relpath(item["path"]),
                "paper_selection_rank": paper_rank,
                "qualifying_cuts": len(item["cuts"]),
                "selected_cuts": len(selected),
                "operator_classes": dict(Counter(cut.operator_class for cut in selected)),
                "env_classes": dict(Counter(cut.env_class for cut in selected)),
                "stats": item["stats"],
            }
        )
        for selected_rank, cut in enumerate(selected):
            row = asdict(cut)
            row.update(
                {
                    "dataset_row_index_source_order": len(selected_rows),
                    "paper_title": item["title"],
                    "paper_source_path": relpath(item["path"]),
                    "paper_selection_rank": paper_rank,
                    "selection_method": "paper_shuffle_then_source_order_stratified_random",
                    "selection_seed": args.seed + 1009 * paper_rank,
                    "selected_rank_within_paper": selected_rank,
                    "source_order_rank_within_paper": source_rank[cut.cut_id],
                    "source_order_quantile_within_paper": source_rank[cut.cut_id] / max(1, len(sorted_all) - 1),
                    "selected_from_total_qualifying_cuts": len(item["cuts"]),
                    "selected_cut_id_set_size": len(selected_ids),
                }
            )
            selected_rows.append(row)

    if len(selected_rows) < args.target_cuts:
        raise RuntimeError(f"Only selected {len(selected_rows)} cuts, target was {args.target_cuts}.")

    shuffled = list(selected_rows)
    rng = random.Random(args.seed + 77)
    rng.shuffle(shuffled)
    for rank, row in enumerate(shuffled):
        row["dataset_row_index"] = rank
        row["global_shuffle_rank"] = rank
        row["analysis_tier"] = analysis_tier(rank)

    dataset_path = out_dir / "equation_cut_dataset.jsonl"
    with dataset_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(shuffled, key=lambda r: r["dataset_row_index"]):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/build_equation_cut_dataset.py",
        "dataset_path": str(dataset_path.relative_to(ROOT)),
        "tex_root": relpath(tex_root),
        "target_cuts": args.target_cuts,
        "total_rows": len(shuffled),
        "paper_count": len(paper_summaries),
        "eligible_paper_count": len(eligible),
        "scanned_paper_count": len(scan_rows),
        "cuts_per_paper": args.cuts_per_paper,
        "min_paper_cuts": args.min_paper_cuts,
        "min_file_bytes": args.min_file_bytes,
        "seed": args.seed,
        "included_paper_ids": sorted(included_ids),
        "excluded_paper_ids": sorted(excluded_ids),
        "y_min": args.y_min,
        "y_max": args.y_max,
        "slack": args.slack,
        "predictor_context_chars": args.predictor_context_chars,
        "min_predictor_context_chars": args.min_predictor_context_chars,
        "bare_tail_multiplier": args.bare_tail_multiplier,
        "analysis_tiers": {
            "pilot20": "global ranks 0..19",
            "dev100_extra": "global ranks 20..99, so first 100 rows are pilot+dev",
            "dev250_extra": "global ranks 100..249, so first 250 rows are pilot+dev+extra",
            "light_holdout": "global ranks 250+",
        },
        "operator_classes": dict(Counter(row["operator_class"] for row in shuffled)),
        "env_classes": dict(Counter(row["env_class"] for row in shuffled)),
        "papers": paper_summaries,
    }
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "paper_scan_summary.json", scan_rows)
    write_readme(out_dir, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def discover_tex_files(tex_root: Path, min_file_bytes: int) -> list[Path]:
    by_resolved: dict[str, Path] = {}
    for pattern in ("arxiv-26*.tex", "arXiv-26*.tex"):
        for path in tex_root.glob(pattern):
            if path.stat().st_size >= min_file_bytes:
                by_resolved[str(path.resolve()).lower()] = path
    return sorted(by_resolved.values())


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_paper_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    path = resolve(path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    ids: set[str] = set()
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if "," in first_line and "paper_id" in first_line:
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(text))
        for row in reader:
            value = row.get("paper_id") or row.get("arxiv_id") or ""
            if value.strip():
                ids.add(normalize_paper_id(value.strip()))
        return ids
    for line in text.splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        ids.add(normalize_paper_id(value.split(",")[0]))
    return ids


def paper_id_from_path(path: Path) -> str:
    return path.stem.replace("arxiv-", "").replace("arXiv-", "").replace("-", ".")


def normalize_paper_id(paper_id: str) -> str:
    return paper_id.replace("arxiv-", "").replace("arXiv-", "").replace("-", ".")


def extract_title(tex: str) -> str | None:
    match = re.search(r"\\title(?:\[[^\]]*\])?\{(?P<title>.*?)\}", tex[:20000], flags=re.DOTALL)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group("title")).strip()
    title = title.replace(r"\\", " ")
    return title or None


def choose_spread_cuts(cuts: list[eqpilot.EquationCut], count: int, seed: int) -> list[eqpilot.EquationCut]:
    if len(cuts) <= count:
        return list(cuts)
    ordered = sorted(cuts, key=lambda c: (c.cut_source_line, c.cut_source_char, c.cut_id))
    rng = random.Random(seed)
    chosen: list[eqpilot.EquationCut] = []
    n = len(ordered)
    for idx in range(count):
        start = idx * n // count
        end = (idx + 1) * n // count
        bucket = ordered[start:end] or [ordered[min(start, n - 1)]]
        chosen.append(rng.choice(bucket))
    return sorted(chosen, key=lambda c: (c.cut_source_line, c.cut_source_char, c.cut_id))


def analysis_tier(rank: int) -> str:
    if rank < 20:
        return "pilot20"
    if rank < 100:
        return "dev100_extra"
    if rank < 250:
        return "dev250_extra"
    return "light_holdout"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_readme(out_dir: Path, manifest: dict) -> None:
    lines = [
        f"# {out_dir.name}",
        "",
        f"Created: {manifest['created_utc']}",
        "",
        "Main artifact:",
        "",
        "```text",
        Path(manifest["dataset_path"]).name,
        "```",
        "",
        "Construction:",
        "",
        "- 2026 TeX files from `training documents`, excluding tiny files.",
        f"- If `included_paper_ids` is nonempty, scanning is restricted to those IDs; this run has {len(manifest.get('included_paper_ids', []))} included IDs.",
        f"- Excluded paper IDs: {len(manifest.get('excluded_paper_ids', []))}.",
        "- Require at least 10k cleaned-document chars before each equation.",
        "- One cut per display equation.",
        "- Skip display equations containing obvious diagram/graphics markup such as `tikzpicture`.",
        "- Cut at an operator/relation site in the middle third of the cleaned equation body.",
        "- `Y` is the full remaining equation suffix after the cut, with 50 <= len(Y) <= 400.",
        "- Predictor context is the previous 10k chars before the equation.",
        "- `B = len(Y)+40`; `bare_B` uses the previous `B` chars before the equation plus equation prefix.",
        "- Rows are globally shuffled with a fixed seed and have `analysis_tier` labels.",
        "",
        "Cut metadata includes `operator_class`, `operator_left_char`, `operator_right_char`, whitespace-adjacency flags, `env_class`, `x_eq_len`, `y_len`, line counts, and `cut_near_tex_linebreak`.",
        "",
        "Counts:",
        "",
        f"- rows: {manifest['total_rows']}",
        f"- papers selected: {manifest['paper_count']}",
        f"- eligible papers scanned: {manifest['eligible_paper_count']}",
        f"- scanned TeX files: {manifest['scanned_paper_count']}",
        f"- included paper IDs: {len(manifest.get('included_paper_ids', []))}",
        f"- excluded paper IDs: {len(manifest.get('excluded_paper_ids', []))}",
        f"- operator classes: `{manifest['operator_classes']}`",
        f"- env classes: `{manifest['env_classes']}`",
        "",
        "Analysis tiers:",
        "",
        "- `pilot20`: first 20 shuffled rows.",
        "- `dev100_extra`: rows 20-99; first 100 rows are the standard small dev slice.",
        "- `dev250_extra`: rows 100-249.",
        "- `light_holdout`: rows 250+.",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
