from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.metrics import metric_score, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny no-network smoke test of clip2 scoring/stat code.")
    parser.add_argument("--fixture", type=Path, default=ROOT / "data" / "fixtures" / "tiny_slice")
    args = parser.parse_args()
    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    rows = load_token_rows(fixture / "token_logprobs.csv")
    by_key: dict[tuple[str, int, str], list[float]] = {}
    for row in rows:
        key = (row["model_lane"], int(row["row_id"]), row["condition"])
        by_key.setdefault(key, []).append(float(row["token_logprob"]))

    diffs = []
    for row_id in sorted({key[1] for key in by_key}):
        z_key = ("toy_model", row_id, "scaffold_z_predictor")
        bare_key = ("controls", row_id, "bare_B")
        diffs.append(metric_score(by_key[z_key], "clip2") - metric_score(by_key[bare_key], "clip2"))
    summary = summarize(diffs)
    expected_mean = 0.4166666666666667
    if abs(summary["mean"] - expected_mean) > 1e-12:
        raise SystemExit(f"Unexpected fixture mean: {summary['mean']} != {expected_mean}")
    print("Fixture smoke passed.")
    print(summary)


def load_token_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()

