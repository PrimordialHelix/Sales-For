"""Data preparation for the animated sales chart in the Analytics page."""
from __future__ import annotations

import numpy as np
import pandas as pd


def prepare_animated_sales_data(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    group_col: str | None = None,
    max_groups: int = 6,
) -> pd.DataFrame:
    """Aggregate sales by month and optionally retain only the top groups."""
    required = [date_col, sales_col]
    if group_col is not None:
        required.append(group_col)
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Columns not found: {missing}")
    if max_groups < 1:
        raise ValueError("max_groups must be at least 1")

    data = df.loc[:, required].copy()
    dates = pd.to_datetime(data[date_col], errors="coerce")
    sales = pd.to_numeric(data[sales_col], errors="coerce")
    valid = dates.notna() & sales.notna() & np.isfinite(sales)
    data = data.loc[valid].copy()
    data["Month"] = dates.loc[valid].dt.to_period("M").astype(str)
    data["Sales"] = sales.loc[valid]

    if group_col is None:
        monthly = data.groupby("Month", as_index=False, sort=True)["Sales"].sum()
        return monthly[["Month", "Sales"]]

    data["Group"] = data[group_col].astype("string").fillna("Unknown")
    top_groups = (
        data.groupby("Group", sort=True)["Sales"]
        .sum()
        .sort_values(ascending=False, kind="stable")
        .head(max_groups)
        .index
    )
    data["Group"] = data["Group"].where(data["Group"].isin(top_groups), "Other groups")
    monthly = (
        data.groupby(["Month", "Group"], as_index=False, sort=True, observed=True)["Sales"]
        .sum()
    )
    return monthly[["Month", "Sales", "Group"]]
