"""
test_feature_engineering.py
Tests for calendar, lag, rolling feature generation and no-leakage guarantees.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feature_engineering import (
    add_calendar_features,
    add_lag_features,
    add_rolling_features,
    build_feature_matrix,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_ts(n=60, start="2023-01-01"):
    """Simple daily time-series DataFrame."""
    dates = pd.date_range(start, periods=n, freq="D")
    sales = np.arange(10, 10 + n, dtype=float)
    return pd.DataFrame({"Date": dates, "Sales": sales})


# ── Calendar features ─────────────────────────────────────────────────────────

class TestCalendarFeatures:
    def test_adds_all_columns(self):
        df = make_ts(10)
        out = add_calendar_features(df, "Date")
        for col in ["_year","_month","_day","_day_of_week",
                    "_day_of_year","_week_of_year","_quarter"]:
            assert col in out.columns, f"Missing column: {col}"

    def test_year_correct(self):
        df = make_ts(5, start="2024-01-01")
        out = add_calendar_features(df, "Date")
        assert (out["_year"] == 2024).all()

    def test_month_january(self):
        df = make_ts(5, start="2024-01-01")
        out = add_calendar_features(df, "Date")
        assert out["_month"].iloc[0] == 1

    def test_no_nan_introduced(self):
        df = make_ts(30)
        out = add_calendar_features(df, "Date")
        cal_cols = [c for c in out.columns if c.startswith("_")]
        assert out[cal_cols].isna().sum().sum() == 0


# ── Lag features — no leakage ─────────────────────────────────────────────────

class TestLagFeatures:
    def test_lag1_value(self):
        df = make_ts(10)
        out = add_lag_features(df, "Sales", lags=[1])
        # Row 1's lag_1 should equal row 0's Sales
        assert out["_lag_1"].iloc[1] == df["Sales"].iloc[0]

    def test_lag1_first_row_is_nan(self):
        df = make_ts(10)
        out = add_lag_features(df, "Sales", lags=[1])
        assert pd.isna(out["_lag_1"].iloc[0])

    def test_lag7_value(self):
        df = make_ts(20)
        out = add_lag_features(df, "Sales", lags=[7])
        assert out["_lag_7"].iloc[7] == df["Sales"].iloc[0]

    def test_no_future_leakage_lag1(self):
        """lag_1 at row i must equal Sales at row i-1, never row i or later."""
        df = make_ts(30)
        out = add_lag_features(df, "Sales", lags=[1])
        for i in range(1, len(out)):
            expected = out["Sales"].iloc[i - 1]
            actual   = out["_lag_1"].iloc[i]
            assert actual == expected, (
                f"Leakage at row {i}: lag_1={actual}, expected={expected}"
            )

    def test_grouped_lag(self):
        df = pd.concat([
            pd.DataFrame({"Date": pd.date_range("2023-01-01", periods=10), "Store": "A",
                          "Sales": np.arange(10, 20, dtype=float)}),
            pd.DataFrame({"Date": pd.date_range("2023-01-01", periods=10), "Store": "B",
                          "Sales": np.arange(100, 110, dtype=float)}),
        ]).reset_index(drop=True)
        out = add_lag_features(df, "Sales", lags=[1], group_cols=["Store"])
        # First row of each group must be NaN
        assert pd.isna(out[out["Store"] == "A"]["_lag_1"].iloc[0])
        assert pd.isna(out[out["Store"] == "B"]["_lag_1"].iloc[0])
        # Second row of group A must be 10 (first sales of A)
        assert out[out["Store"] == "A"]["_lag_1"].iloc[1] == 10.0


# ── Rolling features — no leakage ────────────────────────────────────────────

class TestRollingFeatures:
    def test_rolling_uses_past_only(self):
        """roll_mean_3 at row i must use rows i-3 to i-1 (shifted by 1)."""
        df = make_ts(10)
        out = add_rolling_features(df, "Sales", windows=[3])
        # At row 3 (0-indexed): window = rows 0,1,2 = 10,11,12 → mean=11
        expected = np.mean([10, 11, 12])
        actual   = out["_roll_mean_3"].iloc[3]
        assert abs(actual - expected) < 1e-6, (
            f"Rolling mean wrong at row 3: got {actual}, expected {expected}"
        )

    def test_roll_mean_no_nan_after_warmup(self):
        df = make_ts(20)
        out = add_rolling_features(df, "Sales", windows=[3])
        # After shift(1), row 0 has no past value and is NaN — that is the
        # intended past-only behaviour.  Rows 1+ must be non-NaN (min_periods=1).
        assert out["_roll_mean_3"].iloc[1:].notna().all()


# ── build_feature_matrix ──────────────────────────────────────────────────────

class TestBuildFeatureMatrix:
    def test_returns_correct_shapes(self):
        df = make_ts(80)
        X, y, names = build_feature_matrix(df, "Date", "Sales")
        assert len(X) == len(y)
        assert len(names) == X.shape[1]

    def test_no_target_in_X(self):
        df = make_ts(80)
        X, y, names = build_feature_matrix(df, "Date", "Sales")
        assert "Sales" not in X.columns

    def test_X_has_no_nan(self):
        df = make_ts(80)
        X, y, names = build_feature_matrix(df, "Date", "Sales")
        assert X.isna().sum().sum() == 0, "X must have no NaN after feature engineering"

    def test_insufficient_data_raises(self):
        df = make_ts(4)   # too small
        with pytest.raises(ValueError, match="Not enough"):
            build_feature_matrix(df, "Date", "Sales")

    def test_with_promo_column(self):
        df = make_ts(80)
        df["Promo"] = np.random.randint(0, 2, size=len(df))
        X, y, names = build_feature_matrix(df, "Date", "Sales", promo_col="Promo")
        assert "_promo" in X.columns
