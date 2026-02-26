"""Tests for data module: parsing, cleaning, merge, prepare_data."""

import warnings
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

# Ref-stripping: Wikipedia-style [1]..[N] removed before parsing
STRIP_WIKI_REF_CASES = [
    ("30 settembre 2025[108]", "30 settembre 2025"),
    ("15 gennaio 2026[1]", "15 gennaio 2026"),
    ("text[1] and [2] more", "text and more"),
    ("[3] leading", "leading"),
    ("trailing[99]", "trailing"),
]

NORM_DATE_CASES = [
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


class TestStripWikiRefs:
    """_strip_wiki_refs / _strip_wikipedia_refs: remove [1]..[N] everywhere."""

    @pytest.mark.parametrize("s,expected", STRIP_WIKI_REF_CASES)
    def test_strip_wiki_refs_scalar(self, s, expected):
        assert data._strip_wiki_refs(s) == expected

    def test_strip_wiki_refs_na_passthrough(self):
        assert pd.isna(data._strip_wiki_refs(np.nan))

    def test_strip_wikipedia_refs_on_df(self):
        df = pd.DataFrame({"A": ["30 settembre 2025[108]", "x[1]"], "B": [1, 2]})
        data._strip_wikipedia_refs(df)
        assert df["A"].tolist() == ["30 settembre 2025", "x"]
        assert df["B"].tolist() == [1, 2]


class TestNormDateCell:
    """_norm_date_cell: keep first 3 tokens (d MMMM yyyy); refs stripped earlier."""

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
        with pytest.warns(Warning, match="Row 1:"):
            result = data.prepare_data(raw_df_bad, merge=False)
        assert len(result) == 0

    def test_no_warning_when_all_rows_valid(self, raw_df):
        with warnings.catch_warnings(record=True) as record:
            warnings.simplefilter("always", Warning)
            data.prepare_data(raw_df, merge=False)
        assert len(record) == 0
