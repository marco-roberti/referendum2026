"""Download referendum polling table from Wikipedia."""

from io import StringIO
from pathlib import Path

import pandas as pd
import requests

WIKI_URL = "https://it.wikipedia.org/wiki/Referendum_costituzionale_in_Italia_del_2026"


def download_sondaggi(csv_path: Path) -> None:
    """Download the Sondaggi table from Wikipedia and save as CSV."""
    html = requests.get(
        WIKI_URL, headers={"User-Agent": "Mozilla/5.0 (compatible; Python script)"}
    ).text
    table = next(
        (
            t
            for t in pd.read_html(StringIO(html))
            if "Istituto" in t.columns and "Sì" in t.columns
        ),
        None,
    )
    if table is None:
        raise SystemExit("Could not find Sondaggi table on Wikipedia.")
    table.to_csv(csv_path, index=False)
