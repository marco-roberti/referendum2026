"""Tests for data module: parsing, cleaning, merge, prepare_data."""

from math import nan

import numpy as np
import pandas as pd
import pytest

import sondaggi.data as data

# Parametrized parsing cases (not tabular; kept in code)
TO_DATE_CASES = [
    ("30 settembre 2025", "valid"),
    ("6 ottobre 2025", "valid"),
    ("15 gennaio 2026", "valid"),
    ("", "NaT"),
    ("  ", "NaT"),
    ("N.D.", "NaT"),
    ("invalid", "NaT"),
    ("32 gennaio 2025", "NaT"),
]

TO_NUMBER_CASES = [
    ("44,5", 44.5),
    ("800", 800.0),
    ("1.000", 1000.0),
    ("3,14", 3.14),
]

TO_NUMBER_INVALID = ["nan", "N.D.", "abc"]

NORM_DATE_CASES = [
    ("30 settembre 2025[108]", "30 settembre 2025"),
    ("15 gennaio 2026", "15 gennaio 2026"),
    ("30 ottobre 2025 – Approvazione definitiva", "30 ottobre 2025"),
]


def _is_nan(x):
    return x is nan or (isinstance(x, float) and np.isnan(x))


class TestToDate:
    """_to_date parsing."""

    @pytest.mark.parametrize("s,expect", TO_DATE_CASES)
    def test_from_cases(self, s, expect):
        result = data._to_date(s)
        if expect == "valid":
            assert not pd.isna(result)
            assert result is not pd.NaT
            assert hasattr(result, "year")
        else:
            assert result is pd.NaT or (pd.isna(result) and result is not None)

    def test_non_string_returns_NaT(self):
        assert data._to_date(123) is pd.NaT


class TestToNumber:
    """_to_number parsing (Italian decimal)."""

    @pytest.mark.parametrize("s,expected", TO_NUMBER_CASES)
    def test_valid_italian_number(self, s, expected):
        result = data._to_number(s)
        assert result == pytest.approx(expected)

    @pytest.mark.parametrize("s", TO_NUMBER_INVALID + ["", np.nan])
    def test_invalid_returns_nan(self, s):
        assert _is_nan(data._to_number(s))


class TestNormDateCell:
    """_norm_date_cell: strip citations and keep d MMMM yyyy."""

    @pytest.mark.parametrize("s,expected", NORM_DATE_CASES)
    def test_from_cases(self, s, expected):
        assert data._norm_date_cell(s) == expected

    def test_na_passthrough(self):
        assert pd.isna(data._norm_date_cell(np.nan))


class TestMergeSameDate:
    """merge_same_date aggregates rows by date."""

    def test_empty_unchanged(self):
        df = pd.DataFrame(columns=data.CLEAN_COLUMNS)
        result = data.merge_same_date(df)
        assert result.empty
        assert list(result.columns) == data.CLEAN_COLUMNS

    def test_no_duplicate_dates_unchanged(self, clean_df):
        result = data.merge_same_date(clean_df)
        assert len(result) == len(clean_df)
        pd.testing.assert_frame_equal(
            result.sort_values("date").reset_index(drop=True),
            clean_df.sort_values("date").reset_index(drop=True),
        )

    def test_same_date_merged_weighted(self, clean_df_same_date):
        result = data.merge_same_date(clean_df_same_date)
        n_unique_dates = clean_df_same_date["date"].nunique()
        assert len(result) == n_unique_dates
        assert set(result.columns) == set(data.CLEAN_COLUMNS)
        merged_row = result[result["date"] == clean_df_same_date["date"].iloc[0]].iloc[
            0
        ]
        assert merged_row["sample_size"] == 800.0 + 200.0
        assert "A" in merged_row["istituto"] and "C" in merged_row["istituto"]


class TestPrepareData:
    """prepare_data: full pipeline."""

    def test_merge_false_returns_clean_columns_and_valid_rows(self, raw_df):
        result = data.prepare_data(raw_df, merge=False)
        assert list(result.columns) == data.CLEAN_COLUMNS
        assert len(result) >= 1
        assert result[["date", "yes_norm", "no_norm"]].notna().all().all()

    def test_merge_true_can_reduce_rows(self, raw_df_two_dates):
        no_merge = data.prepare_data(raw_df_two_dates, merge=False)
        with_merge = data.prepare_data(raw_df_two_dates, merge=True)
        assert len(with_merge) <= len(no_merge)

    def test_filters_out_bad_rows(self, raw_df_bad):
        result = data.prepare_data(raw_df_bad, merge=False)
        assert len(result) == 0
