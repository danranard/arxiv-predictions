from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.io_utils import read_json, read_jsonl, require_files, sha256_file


REQUIRED_FILES = [
    "AUDIT_REPORT.json",
    "MANIFEST.json",
    "equation_splits/README.md",
    "equation_splits/MANIFEST.json",
    "equation_splits/data/cuts_all1363.jsonl",
    "equation_splits/data/cuts_old731.jsonl",
    "equation_splits/data/cuts_new632.jsonl",
    "equation_splits/data/paper_list.csv",
    "equation_splits/derived/model_summaries.csv",
    "equation_splits/derived/row_lifts_clip2_raw.csv",
    "equation_splits/derived/row_lifts_all_softenings.csv",
    "equation_splits/derived/model_summaries_all_softenings.csv",
    "equation_splits/derived/thinking_comparisons_clip2_paper_clustered.csv",
    "equation_splits/derived/thinking_comparisons_all_softenings.csv",
    "equation_splits/derived/opus47_usage_anthropic_token_estimates.csv",
    "equation_splits/derived/opus47_usage_anthropic_token_estimates_summary.json",
    "data/cuts_731.jsonl",
    "data/cuts_731_metadata.csv",
    "data/paper_provenance.csv",
    "generations/FINAL_BUNDLE_MANIFEST.json",
    "scores/small_qwen_current_full731/combined_equation_scores.csv",
    "scores/small_qwen_current_full731/combined_target_token_logprobs.csv",
    "scores/small_qwen_current_full731/softened_model_summary.json",
    "scores/kimi_k2p6_current_full731/combined_equation_scores.csv",
    "scores/kimi_k2p6_current_full731/combined_target_token_logprobs.csv",
    "scores/kimi_k2p6_current_full731/softened_model_summary.json",
    "scores/heldout33_softresid_no_z_control/README.md",
]

PROSE_REQUIRED_FILES = [
    "README.md",
    "MANIFEST.json",
    "WEIGHTS_AND_TRAINING.md",
    "analysis/audit_summary.json",
    "analysis/forecast_clip2_sft_vs_bareB_clip2_sft_summary.csv",
    "analysis/forecast_clip2_sft_vs_bareB_clip2_sft_joined.csv",
    "provenance/paper_list.csv",
    "provenance/selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl",
    "source_scores/forecast_scaffold_y200_completion_scores.csv",
    "source_scores/forecast_scaffold_y1000_completion_scores.csv",
    "source_scores/bare_context_y200_completion_scores.csv",
    "source_scores/bare_context_y1000_completion_scores.csv",
    "source_scores/base_qwen_frozen_prefix_windows/README.md",
    "source_scores/base_qwen_frozen_prefix_windows/summary_by_model_window_control.csv",
    "source_scores/base_qwen_frozen_prefix_windows/representative_gpt55_high.csv",
]

DEMO_REQUIRED_FILES = [
    "README.md",
    "run_single_paper_equation_demo.py",
    "arxiv_2307_05326/arxiv-2307-05326.tex",
    "frozen/cut_selection_manifest.json",
    "frozen/cuts_demo10.jsonl",
    "frozen/generations_demo10.jsonl",
    "frozen/qwen3_8b_scores_demo10.csv",
    "frozen/qwen3_8b_token_logprobs_demo10.csv",
    "frozen/report.md",
]

LANES = ["gpt55_none", "gpt55_low", "gpt55_medium", "gpt55_high", "nano_low", "nano_medium", "nano_high"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check that frozen artifacts needed for headline reproduction exist.")
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "frozen")
    parser.add_argument("--check-sha256", action="store_true", help="Also verify paths present in MANIFEST.json.")
    args = parser.parse_args()
    data_root = args.data_root if args.data_root.is_absolute() else ROOT / args.data_root

    missing = require_files(data_root, REQUIRED_FILES)
    prose_root = ROOT / "modules" / "prose_continuation"
    missing.extend([f"modules/prose_continuation/{item}" for item in require_files(prose_root, PROSE_REQUIRED_FILES)])
    demo_root = ROOT / "demo"
    missing.extend([f"demo/{item}" for item in require_files(demo_root, DEMO_REQUIRED_FILES)])
    for lane in LANES:
        missing.extend(
            require_files(
                data_root,
                [
                    f"generations/{lane}/{lane}_joined_stripped.jsonl",
                    f"generations/{lane}/{lane}_joined_stripped.strip_summary.json",
                ],
            )
        )
    if missing:
        raise SystemExit("Missing required files:\n" + "\n".join(f"- {item}" for item in missing))

    audit = read_json(data_root / "AUDIT_REPORT.json")
    if audit["source_rows"] != 740:
        raise SystemExit(f"Expected 740 source rows, found {audit['source_rows']}")
    if audit["scored_731_unique_paper_cut_keys"] != 731:
        raise SystemExit(f"Expected 731 final keys, found {audit['scored_731_unique_paper_cut_keys']}")
    if audit["generation_counts"]["nano_high"]["rows"] != 721:
        raise SystemExit("Expected nano_high to have 721 completed generation rows")
    check_row_ids(data_root)
    check_equation_super(data_root)
    check_prose_module(prose_root)
    check_demo(demo_root)

    if args.check_sha256:
        check_manifest_hashes(data_root)

    print("Frozen artifact manifest checks passed.")
    print("Rows: 1363 combined equation cuts, plus legacy 731-cut first component and prose-continuation module.")


def check_row_ids(data_root: Path) -> None:
    rows = read_jsonl(data_root / "data" / "cuts_731.jsonl")
    ids = [row.get("row_id_731") for row in rows]
    expected = list(range(731))
    if ids != expected:
        raise SystemExit("Expected contiguous row_id_731 values 0..730 in data/cuts_731.jsonl")


def check_equation_super(data_root: Path) -> None:
    root = data_root / "equation_splits"
    rows = read_jsonl(root / "data" / "cuts_all1363.jsonl")
    old_rows = read_jsonl(root / "data" / "cuts_old731.jsonl")
    new_rows = read_jsonl(root / "data" / "cuts_new632.jsonl")
    if len(rows) != 1363:
        raise SystemExit(f"Expected 1363 combined equation rows, found {len(rows)}")
    if len(old_rows) != 731 or len(new_rows) != 632:
        raise SystemExit(f"Expected old/new equation rows 731/632, found {len(old_rows)}/{len(new_rows)}")
    component_counts: dict[str, int] = {}
    super_keys: set[str] = set()
    for row in rows:
        component = row.get("component_bundle")
        component_counts[component] = component_counts.get(component, 0) + 1
        key = row.get("super_key")
        if not key:
            raise SystemExit("Combined equation row missing super_key")
        super_keys.add(key)
    if component_counts != {"old731": 731, "new632": 632}:
        raise SystemExit(f"Unexpected component_bundle counts: {component_counts}")
    if len(super_keys) != len(rows):
        raise SystemExit("Expected unique super_key values in cuts_all1363.jsonl")


def check_prose_module(prose_root: Path) -> None:
    audit = read_json(prose_root / "analysis" / "audit_summary.json")
    for window in ["200", "1000"]:
        item = audit["windows"][window]
        if item["joined_rows"] != 2265:
            raise SystemExit(f"Expected prose joined rows 2265 for window {window}, found {item['joined_rows']}")
        if item["target_mismatch_count"] != 0:
            raise SystemExit(f"Expected no prose target mismatches for window {window}")
        if item["joined_duplicate_keys"] != 0:
            raise SystemExit(f"Expected no prose duplicate joined keys for window {window}")


def check_demo(demo_root: Path) -> None:
    cuts = read_jsonl(demo_root / "frozen" / "cuts_demo10.jsonl")
    generations = read_jsonl(demo_root / "frozen" / "generations_demo10.jsonl")
    if len(cuts) != 10:
        raise SystemExit(f"Expected 10 demo cuts, found {len(cuts)}")
    lanes = {}
    for row in generations:
        lanes[row["model_lane"]] = lanes.get(row["model_lane"], 0) + 1
        if not row.get("z"):
            raise SystemExit("Expected all demo generations to be nonempty")
    if lanes != {"nano_low": 10, "nano_medium": 10}:
        raise SystemExit(f"Unexpected demo generation lane counts: {lanes}")


def check_manifest_hashes(data_root: Path) -> None:
    manifest = read_json(data_root / "MANIFEST.json")
    failures: list[str] = []
    for item in manifest.get("files", []):
        raw_path = item["path"].replace("\\", "/")
        if raw_path.startswith("data/frozen/"):
            relative = raw_path[len("data/frozen/") :]
        else:
            relative = raw_path
        path = data_root / relative
        if not path.exists():
            failures.append(f"{relative}: missing")
            continue
        digest = sha256_file(path)
        if digest != item["sha256"]:
            failures.append(f"{relative}: expected {item['sha256']} got {digest}")
    if failures:
        raise SystemExit("SHA256 check failures:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
