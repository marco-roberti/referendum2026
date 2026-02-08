"""Tests for fetch module: download_sondaggi."""

from unittest.mock import Mock

import pandas as pd
import pytest

import sondaggi.fetch as fetch


class TestDownloadSondaggi:
    """download_sondaggi finds table and writes CSV."""

    def test_writes_csv_when_table_found(
        self, fetch_csv_path, monkeypatch, fetch_table_ok_df
    ):
        monkeypatch.setattr(
            "sondaggi.fetch.requests.get",
            Mock(return_value=Mock(text="<table/>")),
        )
        monkeypatch.setattr(
            "sondaggi.fetch.pd.read_html", lambda _: [fetch_table_ok_df]
        )
        fetch.download_sondaggi(fetch_csv_path)
        assert fetch_csv_path.exists()
        df = pd.read_csv(fetch_csv_path)
        assert "Istituto" in df.columns and "Sì" in df.columns

    def test_raises_when_table_not_found(self, fetch_csv_path, monkeypatch):
        monkeypatch.setattr(
            "sondaggi.fetch.requests.get",
            Mock(return_value=Mock(text="<html/>")),
        )
        monkeypatch.setattr(
            "sondaggi.fetch.pd.read_html",
            lambda _: [pd.DataFrame({"A": [1]})],
        )
        with pytest.raises(SystemExit):
            fetch.download_sondaggi(fetch_csv_path)
        assert not fetch_csv_path.exists()
