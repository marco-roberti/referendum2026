"""Pytest configuration and shared fixtures."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parent / "data"

RAW_CSV_COLUMNS = [
    "Data pubblicazione",
    "Istituto",
    "Committente",
    "Campione",
    "Margine di errore",
    "Sì",
    "No",
    "Indeciso",
    "Distacco",
]


@pytest.fixture
def raw_df():
    """Minimal raw DataFrame that passes prepare_data mask."""
    row = {
        "Data pubblicazione": "15 gennaio 2026[1]",
        "Istituto": "Test Istituto",
        "Committente": "Test",
        "Campione": "1000",
        "Margine di errore": "±3,1",
        "Sì": "44,5%",
        "No": "38,2%",
        "Indeciso": "17,3%",
        "Distacco": 63,
    }
    return pd.DataFrame([row], columns=RAW_CSV_COLUMNS)


@pytest.fixture
def raw_df_two_dates():
    """Two rows, same date (for merge tests)."""
    return pd.read_csv(DATA_DIR / "raw_two_rows.csv")


@pytest.fixture
def raw_df_bad():
    """One row that fails prepare_data mask."""
    row = {
        "Data pubblicazione": "not a date",
        "Istituto": "X",
        "Committente": "",
        "Campione": "100",
        "Margine di errore": "±3",
        "Sì": "x",
        "No": "y",
        "Indeciso": "0%",
        "Distacco": 0,
    }
    return pd.DataFrame([row], columns=RAW_CSV_COLUMNS)


@pytest.fixture
def clean_df():
    """Prepared-style DataFrame (after prepare_data)."""
    return pd.read_csv(DATA_DIR / "clean_three_rows.csv", parse_dates=["date"])


@pytest.fixture
def clean_df_same_date():
    """Same as clean_df but two rows share one date (for merge)."""
    return pd.read_csv(DATA_DIR / "clean_same_date.csv", parse_dates=["date"])


@pytest.fixture
def clean_plot_minimal():
    """Enough rows for plot (cubic interpolation needs > 2 points)."""
    return pd.read_csv(DATA_DIR / "clean_plot_minimal.csv", parse_dates=["date"])


@pytest.fixture
def fetch_table_ok_df():
    """Minimal table when fetch finds the right HTML table."""
    return pd.DataFrame({"Istituto": ["X"], "Sì": ["50%"], "No": ["50%"]})


@pytest.fixture
def fetch_csv_path(tmp_path):
    return tmp_path / "out.csv"


@pytest.fixture
def simple_xy():
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    y = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    return x, y, np.ones(5)


@pytest.fixture
def loess_series():
    """(dates_series, values_series, weights_series) for TestLoess."""
    dates = pd.Series(
        pd.to_datetime(["2025-10-01", "2025-10-15", "2025-11-01", "2025-11-15"])
    )
    values = pd.Series([50.0, 52.0, 48.0, 55.0])
    weights = pd.Series([800.0, 1000.0, 600.0, 900.0], index=dates.index)
    return dates, values, weights


@pytest.fixture
def dates_series(loess_series):
    return loess_series[0]


@pytest.fixture
def values_series(loess_series):
    return loess_series[1]


@pytest.fixture
def weights_series(loess_series):
    return loess_series[2]


@pytest.fixture
def loess_result(dates_series, values_series, weights_series):
    import sondaggi.loess as loess

    return loess.loess(dates_series, values_series, frac=0.5, weights=weights_series)
