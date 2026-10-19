"""
test_forecasting.py
Tests for the recursive multi-step forecasting engine.
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing import validate_and_prepare, chronological_split
from src.feature_engineering import build_feature_matrix
from src.model_training import train_linear_regression, evaluate_model
from src.forecasting import generate_forecast, make_forecast_dates


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_ts(n=120, start="2022-01-01"):
    dates = pd.date_range(start, periods=n, freq="D")
    rng = np.random.default_rng(42)
    sales = 100 + np.arange(n) * 0.2 + rng.normal(0, 5, n)
    return pd.DataFrame({"Date": dates.astype(str), "Sales": sales})


def build_and_train(n=120):
    df_raw = make_ts(n)
    df_clean, _ = validate_and_prepare(df_raw, "Date", "Sales")
    X, y, feat_names = build_feature_matrix(df_clean, "Date", "Sales")
    train_end = int(len(X) * 0.8)
    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    model = train_linear_regression(X_train, y_train)
    return model, df_clean, feat_names


# ── make_forecast_dates ───────────────────────────────────────────────────────

class TestMakeForecastDates:
    def test_correct_count(self):
        start = pd.Timestamp("2023-06-01")
        dates = make_forecast_dates(start, horizon=7)
        assert len(dates) == 7

    def test_starts_after_start_date(self):
        start = pd.Timestamp("2023-06-01")
        dates = make_forecast_dates(start, horizon=7)
        assert dates[0] > start

    def test_daily_frequency(self):
        start = pd.Timestamp("2023-01-01")
        dates = make_forecast_dates(start, horizon=5)
        diffs = pd.Series(dates).diff().dropna()
        assert (diffs == pd.Timedelta("1D")).all()


# ── generate_forecast ─────────────────────────────────────────────────────────

class TestGenerateForecast:
    def test_returns_correct_rows(self):
        model, df_clean, feat_names = build_and_train()
        last_date = pd.to_datetime(df_clean["Date"]).max()
        forecast_dates = make_forecast_dates(last_date, horizon=14)
        config = {
            "date_col": "Date", "sales_col": "Sales",
            "feature_names": feat_names,
            "lags": [1, 7, 14, 28], "windows": [7, 14, 28],
        }
        result = generate_forecast(model, df_clean, forecast_dates, config)
        assert len(result) == 14

    def test_no_negative_predictions(self):
        model, df_clean, feat_names = build_and_train()
        last_date = pd.to_datetime(df_clean["Date"]).max()
        forecast_dates = make_forecast_dates(last_date, horizon=30)
        config = {
            "date_col": "Date", "sales_col": "Sales",
            "feature_names": feat_names,
            "lags": [1, 7, 14, 28], "windows": [7, 14, 28],
        }
        result = generate_forecast(model, df_clean, forecast_dates, config)
        assert (result["Predicted_Sales"] >= 0).all()

    def test_forecast_dates_are_in_future(self):
        model, df_clean, feat_names = build_and_train()
        last_date = pd.to_datetime(df_clean["Date"]).max()
        forecast_dates = make_forecast_dates(last_date, horizon=7)
        config = {
            "date_col": "Date", "sales_col": "Sales",
            "feature_names": feat_names,
            "lags": [1, 7, 14, 28], "windows": [7, 14, 28],
        }
        result = generate_forecast(model, df_clean, forecast_dates, config)
        min_fc_date = pd.to_datetime(result["Date"]).min()
        assert min_fc_date > last_date

    def test_no_actual_future_sales_used(self):
        """
        Verify the forecasting engine does not read sales values beyond the
        history end.  We tamper with the DataFrame after the last history date
        and confirm predictions do not change — because generate_forecast
        never reads those rows.
        """
        model, df_clean, feat_names = build_and_train()
        last_date = pd.to_datetime(df_clean["Date"]).max()
        forecast_dates = make_forecast_dates(last_date, horizon=7)
        config = {
            "date_col": "Date", "sales_col": "Sales",
            "feature_names": feat_names,
            "lags": [1, 7, 14, 28], "windows": [7, 14, 28],
        }

        # Baseline forecast
        result_normal = generate_forecast(model, df_clean, forecast_dates, config)

        # Tamper: append fake future rows with absurd sales
        future_rows = pd.DataFrame({
            "Date": forecast_dates.astype(str),
            "Sales": [999_999] * len(forecast_dates),
        })
        df_with_future = pd.concat([df_clean, future_rows], ignore_index=True)
        df_with_future["Date"] = pd.to_datetime(df_with_future["Date"])

        # The engine should ignore the appended future rows
        # (it filters to history <= last_date before computing lags)
        result_tampered = generate_forecast(model, df_with_future, forecast_dates, config)

        # Predictions must be identical (future rows not consumed)
        np.testing.assert_array_almost_equal(
            result_normal["Predicted_Sales"].values,
            result_tampered["Predicted_Sales"].values,
            decimal=2,
        )

    def test_csv_export(self, tmp_path):
        model, df_clean, feat_names = build_and_train()
        last_date = pd.to_datetime(df_clean["Date"]).max()
        forecast_dates = make_forecast_dates(last_date, horizon=7)
        config = {
            "date_col": "Date", "sales_col": "Sales",
            "feature_names": feat_names,
            "lags": [1, 7, 14, 28], "windows": [7, 14, 28],
        }
        result = generate_forecast(model, df_clean, forecast_dates, config)
        csv_path = tmp_path / "forecast.csv"
        result.to_csv(csv_path, index=False)
        reloaded = pd.read_csv(csv_path)
        assert len(reloaded) == 7
        assert "Predicted_Sales" in reloaded.columns


# ── RMSE calculation ──────────────────────────────────────────────────────────

class TestModelEvaluation:
    def test_rmse_non_negative(self):
        model, df_clean, feat_names = build_and_train()
        X, y, _ = build_feature_matrix(df_clean, "Date", "Sales")
        n_test = int(len(X) * 0.2)
        X_test, y_test = X.iloc[-n_test:], y.iloc[-n_test:]
        metrics = evaluate_model(model, X_test, y_test)
        assert metrics["rmse"] >= 0
        assert metrics["mae"] >= 0

    def test_rmse_formula(self):
        """Manual RMSE check against sklearn output."""
        model, df_clean, feat_names = build_and_train()
        X, y, _ = build_feature_matrix(df_clean, "Date", "Sales")
        n_test = int(len(X) * 0.2)
        X_test, y_test = X.iloc[-n_test:], y.iloc[-n_test:]
        preds = np.clip(model.predict(X_test), 0, None)
        manual_rmse = float(np.sqrt(np.mean((y_test.values - preds) ** 2)))
        metrics = evaluate_model(model, X_test, y_test)
        assert abs(metrics["rmse"] - manual_rmse) < 1e-6
