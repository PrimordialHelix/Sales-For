"""
forecasting.py
--------------
Multi-step recursive forecasting engine.

Public API
----------
build_forecast_df(last_history_df, forecast_dates, config) → DataFrame
    Constructs a feature DataFrame for future dates using recursive lag
    filling — predicted values from previous steps feed into lag features
    for subsequent steps.  No actual future sales values are used.

generate_forecast(model, last_history_df, forecast_dates, config)
    → pd.DataFrame with columns [date_col, "Predicted_Sales"]
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import warnings

import numpy as np
import pandas as pd

from src.feature_engineering import add_calendar_features


# ── Core forecasting engine ───────────────────────────────────────────────────

def generate_forecast(
    model,
    history_df: pd.DataFrame,
    forecast_dates: pd.DatetimeIndex,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """
    Recursively predict sales for each date in *forecast_dates*.

    Parameters
    ----------
    model          : fitted sklearn/XGBoost Pipeline
    history_df     : cleaned historical DataFrame (sorted by date)
    forecast_dates : dates to predict (pd.DatetimeIndex)
    config         : dict with keys —
        date_col, sales_col, promo_col (opt), store_col (opt),
        item_col (opt), feature_names (list[str]),
        lags (list[int]), windows (list[int]),
        future_promo (0 or 1, default 0),
        store_filter (str, opt), item_filter (str, opt)

    Returns
    -------
    pd.DataFrame with columns [date_col, "Predicted_Sales"]
    """
    date_col    = config["date_col"]
    sales_col   = config["sales_col"]
    promo_col   = config.get("promo_col")
    store_col   = config.get("store_col")
    item_col    = config.get("item_col")
    feature_names = config["feature_names"]
    lags        = config.get("lags", [1, 7, 14, 28])
    windows     = config.get("windows", [7, 14, 28])
    future_promo = int(config.get("future_promo", 0))
    store_filter = config.get("store_filter")
    item_filter  = config.get("item_filter")

    # Filter history to the relevant group
    hist = history_df.copy()
    if store_col and store_filter and store_col in hist.columns:
        hist = hist[hist[store_col] == store_filter]
    if item_col and item_filter and item_col in hist.columns:
        hist = hist[hist[item_col] == item_filter]

    hist = hist.sort_values(date_col).reset_index(drop=True)

    # Hard cutoff: discard any rows whose date is >= the first forecast date.
    # This ensures that even if the caller accidentally passes a DataFrame
    # with future rows appended, they never influence lag/rolling computation.
    first_forecast_date = forecast_dates[0]
    hist[date_col] = pd.to_datetime(hist[date_col])
    hist = hist[hist[date_col] < first_forecast_date].reset_index(drop=True)

    # Build a rolling buffer of past sales for lag/rolling computation
    past_sales = list(hist[sales_col].values)

    predictions = []

    for fd in forecast_dates:
        row = {date_col: fd}

        # Calendar features
        row["_year"]          = fd.year
        row["_month"]         = fd.month
        row["_day"]           = fd.day
        row["_day_of_week"]   = fd.dayofweek
        row["_day_of_year"]   = fd.dayofyear
        row["_week_of_year"]  = fd.isocalendar()[1]
        row["_quarter"]       = fd.quarter
        row["_is_month_start"] = int(fd.is_month_start)
        row["_is_month_end"]   = int(fd.is_month_end)

        # Promo
        if promo_col or "_promo" in feature_names:
            row["_promo"] = future_promo

        # Lag features — use past_sales buffer
        for lag in lags:
            col = f"_lag_{lag}"
            if col in feature_names:
                idx = len(past_sales) - lag
                row[col] = past_sales[idx] if idx >= 0 else np.nan

        # Rolling mean features — use past_sales buffer
        for w in windows:
            col = f"_roll_mean_{w}"
            if col in feature_names:
                window_vals = past_sales[-w:] if len(past_sales) >= w else past_sales
                row[col] = float(np.mean(window_vals)) if window_vals else np.nan

        # One-hot encoded store/item columns
        for fn in feature_names:
            if fn not in row:
                # Try to infer from store/item filter
                if store_col and fn.startswith(f"{store_col}_"):
                    suffix = fn[len(store_col)+1:]
                    row[fn] = 1 if str(store_filter) == suffix else 0
                elif item_col and fn.startswith(f"{item_col}_"):
                    suffix = fn[len(item_col)+1:]
                    row[fn] = 1 if str(item_filter) == suffix else 0
                else:
                    row[fn] = 0  # unknown → 0

        # Build feature vector in the EXACT order used during training
        X_row = pd.DataFrame([{fn: row.get(fn, 0) for fn in feature_names}])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pred = float(model.predict(X_row)[0])
        pred = max(pred, 0.0)   # no negative sales

        predictions.append({date_col: fd, "Predicted_Sales": round(pred, 2)})
        past_sales.append(pred)  # feed prediction back for next step's lags

    return pd.DataFrame(predictions)


def make_forecast_dates(
    start_date: pd.Timestamp,
    horizon: int,
    freq: str = "D",
) -> pd.DatetimeIndex:
    """Return *horizon* future dates starting at *start_date* (exclusive)."""
    return pd.date_range(start=start_date + pd.Timedelta(days=1),
                         periods=horizon, freq=freq)
