"""
data_processing.py
------------------
Handles CSV loading, column validation, missing-value treatment,
and chronological train/test splitting.

All public functions return (result, error_message).  If error_message
is not None the caller should surface it to the user instead of using
the result.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd


# ── Column-name aliases ──────────────────────────────────────────────────────

DATE_ALIASES = {"date", "ds", "datum", "fecha", "time", "timestamp", "week", "day"}
SALES_ALIASES = {
    "sales", "weekly_sales", "daily_sales", "units", "quantity", "qty",
    "revenue", "amount", "target", "y", "volume",
}
PROMO_ALIASES = {"promo", "promotion", "is_promo", "ispromo", "deal", "offer"}
STORE_ALIASES = {"store", "store_id", "store_nbr", "storeid", "shop"}
ITEM_ALIASES  = {"item", "item_id", "product", "sku", "product_id", "sku_id"}


# ── Public helpers ────────────────────────────────────────────────────────────

def detect_column(df: pd.DataFrame, aliases: set) -> Optional[str]:
    """Return the first column whose lower-case name is in *aliases*, else None."""
    for col in df.columns:
        if col.strip().lower() in aliases:
            return col
    return None


def load_csv(
    source,           # str path | Path | UploadedFile | bytes
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load a CSV file from disk path, bytes, or a Streamlit UploadedFile.

    Returns (DataFrame, None) on success, (None, error_str) on failure.
    """
    try:
        if isinstance(source, (str, Path)):
            df = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
        elif isinstance(source, bytes):
            df = pd.read_csv(io.BytesIO(source), encoding="utf-8-sig", low_memory=False)
        else:
            # Streamlit UploadedFile
            df = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
    except Exception as exc:
        return None, f"Could not read CSV: {exc}"

    if df.empty:
        return None, "The uploaded file is empty."

    # Strip BOM / whitespace from column names
    df.columns = [c.strip() for c in df.columns]
    return df, None


def validate_and_prepare(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    store_col: Optional[str] = None,
    item_col: Optional[str] = None,
    extra_feature_cols: Optional[List[str]] = None,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Validate columns, parse dates, coerce sales to numeric, drop bad rows,
    sort chronologically, and return a clean working DataFrame.

    Returns (clean_df, None) or (None, error_str).
    """
    required = [date_col, sales_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None, f"Required columns not found: {missing}"

    work = df.copy()

    # ── Parse date ──
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    bad_dates = work[date_col].isna().sum()
    if bad_dates == len(work):
        return None, f"Column '{date_col}' could not be parsed as dates."
    if bad_dates > 0:
        work = work.dropna(subset=[date_col])

    # ── Parse sales ──
    work[sales_col] = pd.to_numeric(work[sales_col], errors="coerce")
    bad_sales = work[sales_col].isna().sum()
    if bad_sales == len(work):
        return None, f"Column '{sales_col}' contains no valid numeric values."
    if bad_sales > 0:
        work = work.dropna(subset=[sales_col])

    # ── Drop duplicate rows ──
    before = len(work)
    work = work.drop_duplicates()
    dropped = before - len(work)

    # ── Sort chronologically ──
    sort_keys = [date_col]
    if store_col and store_col in work.columns:
        sort_keys = [store_col] + sort_keys
    if item_col and item_col in work.columns:
        sort_keys = [item_col] + sort_keys
    work = work.sort_values(sort_keys).reset_index(drop=True)

    if len(work) < 10:
        return None, (
            f"Only {len(work)} valid rows remain after cleaning — "
            "not enough for modelling."
        )

    return work, None


def chronological_split(
    df: pd.DataFrame,
    test_fraction: float = 0.2,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split *df* (already sorted by date) into train and test sets using
    a fixed cutpoint.  No shuffling — preserves time ordering.
    """
    cutoff = int(len(df) * (1 - test_fraction))
    return df.iloc[:cutoff].copy(), df.iloc[cutoff:].copy()


def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame summarising missing values per column."""
    missing = df.isna().sum()
    pct = (missing / len(df) * 100).round(2)
    return pd.DataFrame({"Missing Count": missing, "Missing %": pct})[missing > 0]
