from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equation_splits_repro.headlines import reproduce_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce headline equation-suffix tables from frozen artifacts.")
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "frozen")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "headlines")
    args = parser.parse_args()

    data_root = args.data_root if args.data_root.is_absolute() else ROOT / args.data_root
    out = args.out if args.out.is_absolute() else ROOT / args.out
    report = reproduce_all(data_root, out)
    print(f"Wrote headline outputs to {out}")
    print(f"Final benchmark rows: {report['dataset_audit']['final_rows']}")


if __name__ == "__main__":
    main()

