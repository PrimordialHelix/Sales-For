"""
feature_engineering.py
-----------------------
Creates calendar, lag, and rolling features from a sorted time-series
DataFrame.  All lag/rolling operations use only PAST values — no future
leakage.

Public API
----------
add_calendar_features(df, date_col)          → df with year/month/dow/doy cols
add_lag_features(df, sales_col, lags,
                 group_cols)                 → df with lag columns (NaN-safe)
add_rolling_features(df, sales_col, windows,
                     group_cols)             → df with rolling-mean columns
build_feature_matrix(df, date_col,
                     sales_col, ...)         → (X, y, feature_names)
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


# ── Calendar ──────────────────────────────────────────────────────────────────

def add_calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Add year, month, day_of_week, day_of_year, week_of_year, quarter."""
    out = df.copy()
    dt = pd.to_datetime(out[date_col])
    out["_year"]         = dt.dt.year
    out["_month"]        = dt.dt.month
    out["_day"]          = dt.dt.day
    out["_day_of_week"]  = dt.dt.dayofweek          # 0=Monday
    out["_day_of_year"]  = dt.dt.dayofyear
    out["_week_of_year"] = dt.dt.isocalendar().week.astype(int)
    out["_quarter"]      = dt.dt.quarter
    out["_is_month_start"] = dt.dt.is_month_start.astype(int)
    out["_is_month_end"]   = dt.dt.is_month_end.astype(int)
    return out


# ── Lag features ──────────────────────────────────────────────────────────────

def add_lag_features(
    df: pd.DataFrame,
    sales_col: str,
    lags: List[int],
    group_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Create lag features for each value in *lags*.

    Uses .shift(lag) within each group (or globally) so that row i only
    sees values from row i-lag and earlier — zero leakage.
    """
    out = df.copy()
    for lag in lags:
        col_name = f"_lag_{lag}"
        if group_cols:
            out[col_name] = out.groupby(group_cols)[sales_col].shift(lag)
        else:
            out[col_name] = out[sales_col].shift(lag)
    return out


# ── Rolling features ─────────────────────────────────────────────────────────

def add_rolling_features(
    df: pd.DataFrame,
    sales_col: str,
    windows: List[int],
    group_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Create rolling-mean features.

    Uses shift(1) before rolling so the window never includes the current
    row — guarantees past-only information.
    """
    out = df.copy()
    for w in windows:
        col_name = f"_roll_mean_{w}"
        if group_cols:
            out[col_name] = (
                out.groupby(group_cols)[sales_col]
                .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
            )
        else:
            out[col_name] = (
                out[sales_col].shift(1).rolling(w, min_periods=1).mean()
            )
    return out


# ── Full feature matrix ───────────────────────────────────────────────────────

DEFAULT_LAGS    = [1, 7, 14, 28]
DEFAULT_WINDOWS = [7, 14, 28]


def build_feature_matrix(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    promo_col: Optional[str] = None,
    store_col: Optional[str] = None,
    item_col: Optional[str] = None,
    extra_num_cols: Optional[List[str]] = None,
    extra_cat_cols: Optional[List[str]] = None,
    lags: Optional[List[int]] = None,
    windows: Optional[List[int]] = None,
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Build the full feature matrix X and target y.

    Steps
    -----
    1. Add calendar features.
    2. Add lag features (grouped by store/item when available).
    3. Add rolling-mean features (grouped by store/item when available).
    4. One-hot encode store/item/extra_cat_cols.
    5. Drop rows where any lag/rolling feature is NaN (start of series).
    6. Return X (DataFrame), y (Series), feature_names (list of str).

    The caller is responsible for fitting scalers/encoders on X_train only.
    """
    if lags is None:
        lags = DEFAULT_LAGS
    if windows is None:
        windows = DEFAULT_WINDOWS

    group_cols: List[str] = []
    if store_col and store_col in df.columns:
        group_cols.append(store_col)
    if item_col and item_col in df.columns:
        group_cols.append(item_col)

    work = df.copy()

    # Ensure chronological order within groups
    sort_keys = group_cols + [date_col]
    work = work.sort_values(sort_keys).reset_index(drop=True)

    # 1. Calendar
    work = add_calendar_features(work, date_col)

    # 2. Lag features (only if enough history)
    n_rows = len(work)
    safe_lags = [l for l in lags if l < n_rows // 2]
    if safe_lags:
        work = add_lag_features(work, sales_col, safe_lags,
                                group_cols=group_cols or None)

    # 3. Rolling features
    safe_windows = [w for w in windows if w < n_rows // 2]
    if safe_windows:
        work = add_rolling_features(work, sales_col, safe_windows,
                                    group_cols=group_cols or None)

    # 4. Promo
    if promo_col and promo_col in work.columns:
        work["_promo"] = pd.to_numeric(work[promo_col], errors="coerce").fillna(0)

    # 5. Extra numeric
    if extra_num_cols:
        for col in extra_num_cols:
            if col in work.columns:
                work[col] = pd.to_numeric(work[col], errors="coerce")

    # 6. One-hot encode categoricals
    cat_cols_to_encode = []
    if store_col and store_col in work.columns:
        cat_cols_to_encode.append(store_col)
    if item_col and item_col in work.columns:
        cat_cols_to_encode.append(item_col)
    if extra_cat_cols:
        cat_cols_to_encode.extend(
            [c for c in extra_cat_cols if c in work.columns]
        )

    if cat_cols_to_encode:
        work = pd.get_dummies(work, columns=cat_cols_to_encode, drop_first=False)

    # 7. Select feature columns (everything added, excluding raw date & target)
    exclude = {date_col, sales_col}
    if promo_col:
        exclude.add(promo_col)

    feature_cols = [
        c for c in work.columns
        if c not in exclude
        and c not in (extra_cat_cols or [])
        and not c.startswith("Holiday_Name")
        and work[c].dtype in [np.float64, np.float32, np.int64, np.int32,
                               np.uint8, bool, np.bool_]
    ]

    # Drop rows with NaN in any feature or target
    needed = feature_cols + [sales_col]
    work = work.dropna(subset=needed).reset_index(drop=True)

    if len(work) < 5:
        raise ValueError(
            "Not enough valid rows after feature engineering. "
            "Try a dataset with more history (at least 60+ rows per group)."
        )

    X = work[feature_cols]
    y = work[sales_col]
    return X, y, feature_cols
