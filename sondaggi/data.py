"""Parse and prepare referendum polling data (Italian locale)."""

import locale
import re
from math import nan

import numpy as np
import pandas as pd
from babel.dates import get_month_names
from babel.numbers import parse_decimal

locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")

_IT_MONTHS = "|".join(
    re.escape(m) for m in get_month_names("wide", locale="it_IT").values()
)
_ITALIAN_DATE_RE = re.compile(rf"^\d{{1,2}}\s+({_IT_MONTHS})\s+\d{{4}}$")
_ITALIAN_NUMBER_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*(?:,\d+)?$|^\d+(?:,\d+)?$")

CLEAN_COLUMNS = [
    "date",
    "istituto",
    "yes_norm",
    "no_norm",
    "sample_size",
    "error_margin",
]


def _to_date(s: str | float):
    if pd.isna(s) or not isinstance(s, str) or not (s := s.strip()):
        return pd.NaT
    return (
        pd.to_datetime(s, format="%d %B %Y", errors="coerce")
        if _ITALIAN_DATE_RE.match(s)
        else pd.NaT
    )


def _to_number(s: str | float):
    if pd.isna(s) or not (s := str(s).strip()) or s == "nan":
        return nan
    return (
        float(parse_decimal(s, locale="it_IT")) if _ITALIAN_NUMBER_RE.match(s) else nan
    )


def _norm_date_cell(s: str | float) -> str | float:
    if pd.isna(s):
        return s
    head = str(s).split("[")[0].strip()
    p = head.split()[:3]
    return " ".join(p) if len(p) == 3 else head


def _clean_table(df: pd.DataFrame) -> None:
    df["Data pubblicazione"] = df["Data pubblicazione"].apply(_norm_date_cell)
    for col in ("Sì", "No", "Indeciso"):
        df[col] = (
            (
                df[col]
                .replace("N.D.", np.nan)
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            .replace("", np.nan)
            .replace("nan", np.nan)
        )
    df["Campione"] = df["Campione"].astype(str).str.strip().replace("", np.nan)
    df["Margine di errore"] = (
        df["Margine di errore"]
        .astype(str)
        .str.replace("±", "", regex=False)
        .str.strip()
    ).replace("", np.nan)


def _wavg(g: pd.DataFrame, w: pd.Series, c: str):
    return (g[c] * w).sum() / w.sum() if w.sum() > 0 else g[c].mean()


def merge_same_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    def agg(g):
        w = g["sample_size"].fillna(0)
        return pd.Series(
            {
                "date": g.name,
                "istituto": ", ".join(g["istituto"].astype(str).unique()),
                "yes_norm": _wavg(g, w, "yes_norm"),
                "no_norm": _wavg(g, w, "no_norm"),
                "sample_size": w.sum(),
                "error_margin": _wavg(g, w, "error_margin"),
            }
        )

    return (
        df.groupby("date", as_index=False)
        .apply(agg)
        .reset_index(drop=True)[CLEAN_COLUMNS]
    )


def prepare_data(df: pd.DataFrame, merge: bool = False) -> pd.DataFrame:
    mask = (
        df["Data pubblicazione"]
        .astype(str)
        .str.contains(r"\d{1,2}\s+\w+\s+\d{4}", na=False, regex=True)
        & df["Sì"].astype(str).str.contains("%", na=False)
        & df["No"].astype(str).str.contains("%", na=False)
    )
    df = df[mask].copy()
    _clean_table(df)
    df["date"] = df["Data pubblicazione"].apply(_to_date)
    yes, no = df["Sì"].apply(_to_number), df["No"].apply(_to_number)
    tot = yes + no
    resp = tot + np.nan_to_num(df["Indeciso"].apply(_to_number), nan=0)
    camp = df["Campione"].apply(_to_number)
    df["sample_size"] = np.where(resp > 0, camp * tot / resp, camp)
    df["error_margin"] = df["Margine di errore"].apply(_to_number)
    df["istituto"] = df["Istituto"].astype(str)
    df["yes_norm"], df["no_norm"] = yes / tot * 100, no / tot * 100
    out = (
        df[df[["date", "yes_norm", "no_norm"]].notna().all(axis=1)]
        .sort_values("date")
        .reset_index(drop=True)[CLEAN_COLUMNS]
    )
    return merge_same_date(out) if merge else out
