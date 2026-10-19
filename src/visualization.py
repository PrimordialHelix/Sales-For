"""
visualization.py
----------------
Plotly and Matplotlib chart factory for the Streamlit dashboard.

Every function returns a plotly Figure (or matplotlib Figure where noted)
so the caller can do st.plotly_chart(fig) or st.pyplot(fig).
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


PALETTE = px.colors.qualitative.Bold
ACTUAL_COLOR    = "#4C9BE8"
FORECAST_COLOR  = "#F4845F"
LR_COLOR        = "#7EC8A0"
XGB_COLOR       = "#E8B84B"


# ── Sales over time ───────────────────────────────────────────────────────────

def plot_sales_over_time(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    title: str = "Sales Over Time",
    store_col: Optional[str] = None,
    item_col: Optional[str] = None,
    max_series: int = 6,
) -> go.Figure:
    """Line chart of daily/weekly/monthly sales, optionally per store/item."""
    group_col = store_col or item_col
    if group_col and group_col in df.columns:
        groups = df[group_col].unique()[:max_series]
        fig = go.Figure()
        for g in groups:
            sub = df[df[group_col] == g].sort_values(date_col)
            agg = sub.groupby(date_col)[sales_col].sum().reset_index()
            fig.add_trace(go.Scatter(
                x=agg[date_col], y=agg[sales_col],
                mode="lines", name=str(g),
            ))
    else:
        agg = df.groupby(date_col)[sales_col].sum().reset_index()
        fig = px.line(agg, x=date_col, y=sales_col, color_discrete_sequence=[ACTUAL_COLOR])

    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Sales",
        template="plotly_dark", hovermode="x unified",
    )
    return fig


# ── Sales distribution ────────────────────────────────────────────────────────

def plot_sales_distribution(
    df: pd.DataFrame,
    sales_col: str,
    title: str = "Sales Distribution",
) -> go.Figure:
    fig = px.histogram(
        df, x=sales_col, nbins=50,
        color_discrete_sequence=[ACTUAL_COLOR],
        title=title,
    )
    fig.update_layout(template="plotly_dark", xaxis_title="Sales", yaxis_title="Count")
    return fig


# ── Monthly / daily averages ──────────────────────────────────────────────────

def plot_avg_by_period(
    df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    period: str = "month",   # "month" | "dayofweek"
) -> go.Figure:
    dt = pd.to_datetime(df[date_col])
    if period == "month":
        df2 = df.copy()
        df2["_period"] = dt.dt.month
        labels = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]
        agg = df2.groupby("_period")[sales_col].mean().reset_index()
        agg["Label"] = agg["_period"].apply(lambda m: labels[m-1])
        title = "Average Sales by Month"
        x_col = "Label"
    else:
        df2 = df.copy()
        df2["_period"] = dt.dt.dayofweek
        labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        agg = df2.groupby("_period")[sales_col].mean().reset_index()
        agg["Label"] = agg["_period"].apply(lambda d: labels[d])
        title = "Average Sales by Day of Week"
        x_col = "Label"

    fig = px.bar(
        agg, x=x_col, y=sales_col,
        color_discrete_sequence=[ACTUAL_COLOR],
        title=title,
    )
    fig.update_layout(template="plotly_dark", yaxis_title="Avg Sales")
    return fig


# ── Promo comparison ──────────────────────────────────────────────────────────

def plot_promo_comparison(
    df: pd.DataFrame,
    sales_col: str,
    promo_col: str,
) -> go.Figure:
    avg = df.groupby(promo_col)[sales_col].mean().reset_index()
    avg["Promotion"] = avg[promo_col].map({0: "No Promo", 1: "Promo"})
    fig = px.bar(
        avg, x="Promotion", y=sales_col,
        color="Promotion",
        color_discrete_map={"No Promo": ACTUAL_COLOR, "Promo": FORECAST_COLOR},
        title="Average Sales: Promo vs No Promo",
    )
    fig.update_layout(template="plotly_dark", yaxis_title="Avg Sales", showlegend=False)
    return fig


# ── Correlation heatmap ───────────────────────────────────────────────────────

def plot_correlation_heatmap(
    df: pd.DataFrame,
    cols: Optional[List[str]] = None,
) -> go.Figure:
    num_df = df.select_dtypes(include=[np.number])
    if cols:
        num_df = num_df[[c for c in cols if c in num_df.columns]]
    corr = num_df.corr().round(2)
    fig = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Correlation Heatmap",
    )
    fig.update_layout(template="plotly_dark")
    return fig


# ── Actual vs Predicted (evaluation) ─────────────────────────────────────────

def plot_actual_vs_predicted(
    dates,
    actual: np.ndarray,
    pred_lr: Optional[np.ndarray] = None,
    pred_xgb: Optional[np.ndarray] = None,
    date_col: str = "Date",
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=actual, name="Actual", mode="lines",
        line=dict(color=ACTUAL_COLOR, width=2),
    ))
    if pred_lr is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=pred_lr, name="Linear Regression", mode="lines",
            line=dict(color=LR_COLOR, dash="dash"),
        ))
    if pred_xgb is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=pred_xgb, name="XGBoost", mode="lines",
            line=dict(color=XGB_COLOR, dash="dot"),
        ))
    fig.update_layout(
        title="Actual vs Predicted Sales (Test Set)",
        xaxis_title=date_col, yaxis_title="Sales",
        template="plotly_dark", hovermode="x unified",
    )
    return fig


# ── Model comparison bar chart ────────────────────────────────────────────────

def plot_model_comparison(metrics: dict) -> go.Figure:
    """
    metrics = {"Linear Regression": {"rmse": 12.3, "mae": 9.1},
               "XGBoost":           {"rmse": 8.7,  "mae": 7.0}}
    """
    models = list(metrics.keys())
    rmses  = [metrics[m]["rmse"] for m in models]
    maes   = [metrics[m]["mae"]  for m in models]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["RMSE (lower is better)",
                                        "MAE (lower is better)"])
    fig.add_trace(go.Bar(x=models, y=rmses, marker_color=[LR_COLOR, XGB_COLOR],
                         name="RMSE", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=models, y=maes, marker_color=[LR_COLOR, XGB_COLOR],
                         name="MAE", showlegend=False), row=1, col=2)
    fig.update_layout(title="Model Comparison", template="plotly_dark")
    return fig


# ── Future forecast chart ─────────────────────────────────────────────────────

def plot_forecast(
    history_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    date_col: str,
    sales_col: str,
    tail_days: int = 90,
) -> go.Figure:
    hist = history_df.sort_values(date_col).tail(tail_days)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist[date_col], y=hist[sales_col],
        name="Historical Sales", mode="lines",
        line=dict(color=ACTUAL_COLOR, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df[date_col], y=forecast_df["Predicted_Sales"],
        name="Forecast", mode="lines+markers",
        line=dict(color=FORECAST_COLOR, width=2, dash="dash"),
        marker=dict(size=5),
    ))
    # Shaded forecast region
    if len(forecast_df):
        start = forecast_df[date_col].min()
        end   = forecast_df[date_col].max()
        fig.add_vrect(
            x0=str(start), x1=str(end),
            fillcolor=FORECAST_COLOR, opacity=0.07,
            line_width=0,
            annotation_text="Forecast Period",
            annotation_position="top left",
        )
    fig.update_layout(
        title="Sales Forecast",
        xaxis_title="Date", yaxis_title="Sales",
        template="plotly_dark", hovermode="x unified",
    )
    return fig


# ── Feature importance bar chart ─────────────────────────────────────────────

def plot_feature_importance(importance_dict: dict, top_n: int = 15) -> go.Figure:
    items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    names = [i[0] for i in items]
    vals  = [i[1] for i in items]
    fig = px.bar(
        x=vals, y=names, orientation="h",
        color_discrete_sequence=[XGB_COLOR],
        title=f"Top {top_n} Feature Importances",
    )
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Importance", yaxis_title="Feature",
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ── Category / store comparison ───────────────────────────────────────────────

def plot_group_comparison(
    df: pd.DataFrame,
    group_col: str,
    sales_col: str,
    top_n: int = 10,
) -> go.Figure:
    agg = (df.groupby(group_col)[sales_col].sum()
           .nlargest(top_n).reset_index())
    fig = px.bar(
        agg, x=group_col, y=sales_col,
        color=group_col,
        title=f"Total Sales by {group_col} (Top {top_n})",
    )
    fig.update_layout(template="plotly_dark", showlegend=False,
                      yaxis_title="Total Sales")
    return fig
