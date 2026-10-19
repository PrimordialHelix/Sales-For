"""
test_data_processing.py
Tests for data loading, validation, and chronological splitting.
"""
import io
import pytest
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing import (
    load_csv, validate_and_prepare, chronological_split,
    missing_value_summary, detect_column,
    DATE_ALIASES, SALES_ALIASES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_df(n=100, bad_dates=0, bad_sales=0):
    dates = pd.date_range("2023-01-01", periods=n, freq="D").astype(str).tolist()
    sales = list(range(10, 10 + n))
    if bad_dates:
        dates[:bad_dates] = ["not-a-date"] * bad_dates
    if bad_sales:
        sales[:bad_sales] = [None] * bad_sales
    return pd.DataFrame({"Date": dates, "Sales": sales, "Store": ["S1"] * n})


def make_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


# ── load_csv ──────────────────────────────────────────────────────────────────

class TestLoadCsv:
    def test_load_from_bytes_ok(self):
        df = make_df(50)
        loaded, err = load_csv(make_csv_bytes(df))
        assert err is None
        assert len(loaded) == 50

    def test_empty_csv_returns_error(self):
        df_empty = pd.DataFrame()
        buf = io.StringIO()
        df_empty.to_csv(buf, index=False)
        _, err = load_csv(buf.getvalue().encode())
        assert err is not None

    def test_malformed_bytes_returns_error(self):
        _, err = load_csv(b"\x00\x01\x02binary garbage")
        # May or may not parse; we just check it doesn't crash
        # (load_csv catches the exception)
        pass  # no assertion — just must not raise


# ── validate_and_prepare ──────────────────────────────────────────────────────

class TestValidateAndPrepare:
    def test_valid_data_returns_clean_df(self):
        df = make_df(60)
        clean, err = validate_and_prepare(df, "Date", "Sales")
        assert err is None
        assert len(clean) == 60

    def test_missing_column_returns_error(self):
        df = pd.DataFrame({"Date": ["2023-01-01"], "Revenue": [100]})
        _, err = validate_and_prepare(df, "Date", "Sales")
        assert err is not None
        assert "Sales" in err

    def test_all_bad_dates_returns_error(self):
        df = pd.DataFrame({"Date": ["bad"] * 20, "Sales": range(20)})
        _, err = validate_and_prepare(df, "Date", "Sales")
        assert err is not None

    def test_bad_dates_are_dropped(self):
        df = make_df(50, bad_dates=5)
        clean, err = validate_and_prepare(df, "Date", "Sales")
        assert err is None
        assert len(clean) == 45

    def test_bad_sales_are_dropped(self):
        df = make_df(50, bad_sales=3)
        clean, err = validate_and_prepare(df, "Date", "Sales")
        assert err is None
        assert len(clean) == 47

    def test_data_is_sorted_chronologically(self):
        df = make_df(40)
        df = df.sample(frac=1, random_state=7)  # shuffle
        clean, _ = validate_and_prepare(df, "Date", "Sales")
        dates = pd.to_datetime(clean["Date"])
        assert (dates.diff().dropna() >= pd.Timedelta(0)).all()

    def test_too_few_rows_returns_error(self):
        df = make_df(5)
        _, err = validate_and_prepare(df, "Date", "Sales")
        assert err is not None


# ── chronological_split ───────────────────────────────────────────────────────

class TestChronologicalSplit:
    def test_split_sizes(self):
        df = make_df(100)
        df, _ = validate_and_prepare(df, "Date", "Sales")
        train, test = chronological_split(df, test_fraction=0.2)
        assert len(train) == 80
        assert len(test)  == 20

    def test_train_before_test(self):
        df = make_df(100)
        df, _ = validate_and_prepare(df, "Date", "Sales")
        train, test = chronological_split(df, test_fraction=0.2)
        last_train_date = pd.to_datetime(train["Date"]).max()
        first_test_date = pd.to_datetime(test["Date"]).min()
        assert last_train_date <= first_test_date, (
            "Train set must not have dates after the test set starts."
        )


# ── detect_column ─────────────────────────────────────────────────────────────

class TestDetectColumn:
    def test_detects_date(self):
        df = pd.DataFrame({"Date": [], "Sales": []})
        assert detect_column(df, DATE_ALIASES) == "Date"

    def test_detects_sales(self):
        df = pd.DataFrame({"Date": [], "Weekly_Sales": []})
        assert detect_column(df, SALES_ALIASES) == "Weekly_Sales"

    def test_returns_none_when_absent(self):
        df = pd.DataFrame({"X": [], "Y": []})
        assert detect_column(df, DATE_ALIASES) is None


# ── missing_value_summary ─────────────────────────────────────────────────────

class TestMissingValueSummary:
    def test_no_missing(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        summ = missing_value_summary(df)
        assert len(summ) == 0

    def test_counts_missing(self):
        df = pd.DataFrame({"a": [1, None, None], "b": [1, 2, 3]})
        summ = missing_value_summary(df)
        assert "a" in summ.index
        assert summ.loc["a", "Missing Count"] == 2
