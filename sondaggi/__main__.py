"""Entry point for python -m sondaggi."""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from .data import prepare_data
from .fetch import download_sondaggi
from .plot import plot_loess

CSV_RAW = Path("sondaggi.csv")
CSV_CLEAN = Path("sondaggi_clean.csv")


def main(args: argparse.Namespace) -> None:
    download_sondaggi(CSV_RAW)
    df = prepare_data(
        pd.read_csv(CSV_RAW), merge=args.merge, start_date=args.start_date
    )
    df.to_csv(CSV_CLEAN, index=False)
    plot_loess(df, args.frac, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frac", type=float, default=0.4)
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument(
        "--merge", action="store_true", help="Merge polls on the same date"
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        help="Consider only polls from this date (YYYY-MM-DD) onwards",
    )
    main(parser.parse_args())
