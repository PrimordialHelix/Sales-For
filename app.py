"""
app.py  — AI-Based Sales Forecasting Using Machine Learning
============================================================
Streamlit dashboard for Project #42, Section 315 B.

Run:  py -m streamlit run app.py
"""
from __future__ import annotations

import io
import base64
import hashlib
from html import escape as escape_html
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_lottie import st_lottie

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.data_processing import (
    DATE_ALIASES, ITEM_ALIASES, PROMO_ALIASES, SALES_ALIASES, STORE_ALIASES,
    chronological_split, detect_column, load_csv, missing_value_summary,
    validate_and_prepare,
)
from src.feature_engineering import build_feature_matrix
from src.forecasting import generate_forecast, make_forecast_dates
from src.animated_analytics import prepare_animated_sales_data
from src.visualization import (
    plot_actual_vs_predicted, plot_avg_by_period, plot_correlation_heatmap,
    plot_feature_importance, plot_forecast, plot_group_comparison,
    plot_model_comparison, plot_promo_comparison, plot_sales_distribution,
    plot_sales_over_time,
)
from src.styles import SALESCAST_CSS

def svg_data_uri(path: Path) -> str:
    """Embed a local SVG asset so it renders reliably in Streamlit markdown."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


SALESCAST_MARK = svg_data_uri(ROOT / "assets" / "salescast-mark.svg")
SALESCAST_WORDMARK = svg_data_uri(ROOT / "assets" / "salescast-wordmark.svg")


@st.cache_data
def load_salescast_animation() -> dict:
    """Load the locally bundled Lottie animation."""
    import json

    with (ROOT / "assets" / "salescast-lottie.json").open(encoding="utf-8") as animation_file:
        return json.load(animation_file)


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SALESCAST | Intelligent Sales Analytics",
    page_icon=str(ROOT / "assets" / "salescast-mark.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(SALESCAST_CSS, unsafe_allow_html=True)

# ── Session-state initialisation ──────────────────────────────────────────────
for key, default in {
    "df": None, "clean_df": None, "config": {},
    "model_lr": None, "model_xgb": None,
    "metrics": {}, "feature_names": [],
    "X_test": None, "y_test": None,
    "test_dates": None,
    "active_page": "Dashboard",
    "intro_revealed": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.pop("page_override", None) == "📂 Dataset":
    st.session_state.active_page = "Data Explorer"


def render_metric_card(
    label: str,
    value: str,
    detail: str = "",
    accent: str = "teal",
) -> None:
    """Render a consistently styled card with escaped, data-backed content."""
    allowed_accents = {"teal", "purple", "emerald", "blue", "pink"}
    accent_class = accent if accent in allowed_accents else "teal"
    st.markdown(
        f'<div class="metric-card accent-{accent_class}">'
        f'<div class="metric-label">{escape_html(label)}</div>'
        f'<div class="metric-value">{escape_html(value)}</div>'
        f'<div class="metric-detail">{escape_html(detail)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_section_heading(title: str, description: str = "") -> None:
    """Render a consistent heading for analytical sections."""
    description_html = (
        f"<p>{escape_html(description)}</p>" if description else ""
    )
    st.markdown(
        f'<div class="section-heading"><div><h2>{escape_html(title)}</h2>'
        f"{description_html}</div></div>",
        unsafe_allow_html=True,
    )


def render_chart(figure, **kwargs) -> None:
    """Apply the SALESCAST chart surface and typography before rendering."""
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", family="Inter, sans-serif"),
        margin=dict(l=18, r=18, t=58, b=18),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    figure.update_xaxes(gridcolor="rgba(148, 163, 184, .12)", zerolinecolor="rgba(148, 163, 184, .18)")
    figure.update_yaxes(gridcolor="rgba(148, 163, 184, .12)", zerolinecolor="rgba(148, 163, 184, .18)")
    st.plotly_chart(figure, use_container_width=True, **kwargs)


def reset_dataset_state(df_raw: pd.DataFrame) -> None:
    """Discard results tied to an older input dataset."""
    st.session_state.df = df_raw
    st.session_state.clean_df = None
    st.session_state.config = {}
    st.session_state.model_lr = None
    st.session_state.model_xgb = None
    st.session_state.metrics = {}
    st.session_state.feature_names = []
    st.session_state.X_test = None
    st.session_state.y_test = None
    st.session_state.test_dates = None
    st.session_state.pop("last_forecast", None)
    st.session_state.pop("last_forecast_config", None)


def model_r_squared(model_name: str) -> Optional[float]:
    """Calculate R-squared from the stored held-out test data when available."""
    from sklearn.metrics import r2_score

    model = (
        st.session_state.model_lr
        if model_name == "Linear Regression"
        else st.session_state.model_xgb
    )
    X_test = st.session_state.X_test
    y_test = st.session_state.y_test
    if model is None or X_test is None or y_test is None or len(y_test) < 2:
        return None
    predictions = np.clip(model.predict(X_test), 0, None)
    return float(r2_score(y_test, predictions))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div class="salescast-brand">'
        f'<img class="salescast-brand-mark" src="{SALESCAST_MARK}" alt="SALESCAST chart logo">'
        '<div><div class="salescast-brand-name">SALESCAST</div>'
        '<div class="salescast-brand-subtitle">Intelligent Sales Analytics</div></div></div>',
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigation",
        [
            "Dashboard", "Forecast Studio", "Data Explorer",
            "Model Performance", "Analytics", "Reports", "About Project",
        ],
        format_func=lambda value: {
            "Dashboard": "◈  Dashboard",
            "Forecast Studio": "⌁  Forecast Studio",
            "Data Explorer": "▦  Data Explorer",
            "Model Performance": "◉  Model Performance",
            "Analytics": "⌗  Analytics",
            "Reports": "▤  Reports",
            "About Project": "ⓘ  About Project",
        }[value],
        key="active_page",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**WORKSPACE STATUS**")
    if st.session_state.df is not None:
        n = len(st.session_state.df)
        st.success(f"Dataset ready · {n:,} rows")
    else:
        st.warning("No dataset loaded")

    st.markdown("**AVAILABLE MODELS**")
    lr_ok  = st.session_state.model_lr is not None
    xgb_ok = st.session_state.model_xgb is not None
    st.write(f"{'●' if lr_ok else '○'} Linear Regression")
    st.write(f"{'●' if xgb_ok else '○'} XGBoost")
    st.caption("Project #42 · Section 315 B")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    df = st.session_state.clean_df
    metrics = st.session_state.metrics
    cfg = st.session_state.config
    sales_col = cfg.get("sales_col")
    date_col = cfg.get("date_col")
    sales_by_date = None
    total_sales = average_daily = latest_sales = "—"
    latest_detail = "Validate a dataset to show actual sales"
    if df is not None and sales_col in df.columns and date_col in df.columns:
        sales_by_date = df.groupby(date_col)[sales_col].sum().sort_index()
        total_sales = f"{df[sales_col].sum():,.0f}"
        average_daily = f"{sales_by_date.mean():,.1f}"
        latest_sales = f"{sales_by_date.iloc[-1]:,.1f}"
        latest_detail = pd.Timestamp(sales_by_date.index[-1]).strftime("%b %d, %Y")

    forecast_df = st.session_state.get("last_forecast")
    best_model = min(metrics, key=lambda name: metrics[name]["rmse"]) if metrics else None
    forecast_value = (
        f"{forecast_df['Predicted_Sales'].iloc[0]:,.1f}"
        if forecast_df is not None and not forecast_df.empty
        else "—"
    )
    best_rmse = f"{metrics[best_model]['rmse']:,.2f}" if best_model else "—"
    if not st.session_state.intro_revealed:
        title_class = "salescast-title salescast-title--reveal"
        st.session_state.intro_revealed = True
    else:
        title_class = "salescast-title"
    dataset_ready = df is not None
    model_ready = bool(st.session_state.model_lr or st.session_state.model_xgb)
    hero_copy, hero_animation = st.columns([4, 1.15], vertical_alignment="center")
    with hero_copy:
        st.markdown(
            f'<section class="salescast-hero">'
            f'<img class="salescast-hero-wordmark" src="{SALESCAST_WORDMARK}" alt="SALESCAST — Intelligent Sales Analytics">'
            f'<p class="salescast-eyebrow">Forecasting workspace</p>'
            f'<h1 class="{title_class}">Know what comes <span>next.</span></h1>'
            '<p class="salescast-description">A practical forecasting workspace for '
            'exploring historical demand, evaluating models, and planning ahead.</p>'
            '<div class="salescast-status-row">'
            f'<span class="salescast-status"><i class="salescast-status-dot {"is-ready" if dataset_ready else ""}"></i>'
            f'{"Dataset connected" if dataset_ready else "Dataset not connected"}</span>'
            f'<span class="salescast-status"><i class="salescast-status-dot {"is-ready" if model_ready else ""}"></i>'
            f'{"Model ready" if model_ready else "No trained model"}</span>'
            '<span class="salescast-status">Forecasts use your validated data</span>'
            '</div></section>',
            unsafe_allow_html=True,
        )
    with hero_animation:
        with st.container(border=True):
            st_lottie(
                load_salescast_animation(),
                speed=0.85,
                loop=False,
                quality="medium",
                height=160,
                width=160,
                key="salescast_dashboard_lottie",
            )
            st.caption("Sales signal")

    if sales_by_date is None:
        total_detail = average_detail = latest_detail = "Load and validate a dataset to calculate"
    else:
        total_detail = f"{len(df):,} validated records"
        average_detail = f"Across {len(sales_by_date):,} dates"
    metric_columns = st.columns(5)
    with metric_columns[0]:
        render_metric_card("Historical sales", total_sales, total_detail, "teal")
    with metric_columns[1]:
        render_metric_card("Average daily sales", average_daily, average_detail, "blue")
    with metric_columns[2]:
        render_metric_card("Latest actual", latest_sales, latest_detail, "emerald")
    with metric_columns[3]:
        render_metric_card(
            "Next-period forecast", forecast_value,
            "First predicted value" if forecast_df is not None else "Generate a forecast to populate",
            "purple",
        )
    with metric_columns[4]:
        render_metric_card(
            "Best test RMSE", best_rmse,
            best_model or "Train a model to calculate",
            "pink",
        )

    render_section_heading(
        "Historical Sales vs Forecast",
        "Actual sales are shown in teal; the forecast is shown with a dashed line.",
    )
    if df is None:
        st.info("Load and validate a dataset in Data Explorer to view its sales history.")
        if st.button("Open Data Explorer", type="primary", key="dashboard_open_data"):
            st.session_state.page_override = "📂 Dataset"
            st.rerun()
    else:
        chart_history = df
        forecast_config = st.session_state.get("last_forecast_config", {})
        for column_key, filter_key in (("store_col", "store_filter"), ("item_col", "item_filter")):
            column = forecast_config.get(column_key)
            selected = forecast_config.get(filter_key)
            if selected is not None and column in chart_history.columns:
                chart_history = chart_history[chart_history[column] == selected]
        if forecast_df is not None and not forecast_df.empty:
            render_chart(plot_forecast(chart_history, forecast_df, date_col, sales_col, tail_days=180))
        else:
            render_chart(plot_sales_over_time(chart_history, date_col, sales_col, title="Historical Sales"))
            st.caption("Train a model and generate a forecast in Forecast Studio to extend this chart.")

        left, right = st.columns([1.2, 1])
        with left:
            render_section_heading("Seasonal Pattern", "Average sales by calendar month.")
            render_chart(plot_avg_by_period(df, date_col, sales_col, period="month"))
        with right:
            render_section_heading("Demand Distribution", "How observed sales values are distributed.")
            render_chart(plot_sales_distribution(df, sales_col))

    if metrics:
        render_section_heading("Model Snapshot", f"Best current test-set result: {best_model}.")
        cols = st.columns(len(metrics))
        for col, (name, values) in zip(cols, metrics.items()):
            with col:
                r_squared = model_r_squared(name)
                render_metric_card(
                    name,
                    f"RMSE {values['rmse']:,.2f}",
                    f"MAE {values['mae']:,.2f} · R² {r_squared:.3f}" if r_squared is not None
                    else f"MAE {values['mae']:,.2f}",
                    "emerald" if name == best_model else "blue",
                )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DATASET
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Data Explorer":
    render_section_heading("Data Explorer", "Load, validate, and inspect sales data.")

    col_upload, col_sample = st.columns(2)

    with col_upload:
        st.markdown("#### Upload your CSV")
        uploaded = st.file_uploader("Choose a CSV file", type="csv",
                                    help="Supported columns: Date, Sales, Store, Item, Promo, …")
        if uploaded:
            upload_digest = hashlib.sha256(uploaded.getvalue()).hexdigest()
            if st.session_state.get("upload_digest") != upload_digest:
                df_raw, err = load_csv(uploaded)
                if err:
                    st.error(err)
                else:
                    reset_dataset_state(df_raw)
                    st.session_state.upload_digest = upload_digest
                    st.success(f"Uploaded: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
            elif st.session_state.df is not None:
                st.caption(f"Uploaded file ready · {st.session_state.df.shape[0]:,} rows")
        else:
            st.session_state.upload_digest = None

    with col_sample:
        st.markdown("#### Use built-in demonstration data")
        sample_path = ROOT / "data" / "sample_sales.csv"
        if st.button("📥 Load Sample Dataset", use_container_width=True):
            if not sample_path.exists():
                st.error("sample_sales.csv not found in data/. Run the app from the project root.")
            else:
                df_raw, err = load_csv(str(sample_path))
                if err:
                    st.error(err)
                else:
                    reset_dataset_state(df_raw)
                    st.success(f"✅ Loaded sample: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

        st.markdown("""
        <div class="info-box">
        ⚠️ <b>Synthetic Data Notice</b><br>
        The included sample dataset is <b>artificially generated</b> for demonstration.
        It is NOT from Kaggle. See README for instructions to load a real dataset.
        </div>
        """, unsafe_allow_html=True)

    # ── Column configuration ───────────────────────────────────────────────────
    if st.session_state.df is not None:
        df = st.session_state.df
        st.markdown("---")
        render_section_heading("Column Configuration", "Choose the target and optional feature columns.")

        cols = df.columns.tolist()

        auto_date  = detect_column(df, DATE_ALIASES)
        auto_sales = detect_column(df, SALES_ALIASES)
        auto_promo = detect_column(df, PROMO_ALIASES)
        auto_store = detect_column(df, STORE_ALIASES)
        auto_item  = detect_column(df, ITEM_ALIASES)

        c1, c2 = st.columns(2)
        with c1:
            date_col  = st.selectbox("📅 Date column *",  cols,
                                     index=cols.index(auto_date)  if auto_date  in cols else 0)
            sales_col = st.selectbox("💰 Sales / Target column *", cols,
                                     index=cols.index(auto_sales) if auto_sales in cols else 1)
        with c2:
            promo_col  = st.selectbox("🎁 Promotion column (optional)", ["(none)"] + cols,
                                      index=(cols.index(auto_promo)+1) if auto_promo in cols else 0)
            store_col  = st.selectbox("🏪 Store column (optional)", ["(none)"] + cols,
                                      index=(cols.index(auto_store)+1) if auto_store in cols else 0)

        item_col = st.selectbox("📦 Item / Product column (optional)", ["(none)"] + cols,
                                index=(cols.index(auto_item)+1) if auto_item in cols else 0)

        # Extra features
        already_picked = {date_col, sales_col, promo_col, store_col, item_col, "(none)"}
        remaining = [c for c in cols if c not in already_picked]

        num_cols = [c for c in remaining if pd.api.types.is_numeric_dtype(df[c])]
        cat_cols = [c for c in remaining if not pd.api.types.is_numeric_dtype(df[c])]

        extra_num = st.multiselect("🔢 Extra numeric features", num_cols,
                                   default=[c for c in ["Discount_Pct","Base_Price_INR","Price_INR"] if c in num_cols])
        extra_cat = st.multiselect("🏷️ Extra categorical features", cat_cols,
                                   default=[c for c in ["Category"] if c in cat_cols])

        if st.button("✅ Validate & Apply", type="primary", use_container_width=True):
            promo_c = None if promo_col == "(none)" else promo_col
            store_c = None if store_col == "(none)" else store_col
            item_c  = None if item_col  == "(none)" else item_col

            clean, err = validate_and_prepare(
                df, date_col, sales_col,
                store_col=store_c, item_col=item_c,
            )
            if err:
                st.error(f"❌ Validation error: {err}")
            else:
                st.session_state.clean_df = clean
                st.session_state.config = {
                    "date_col":  date_col,
                    "sales_col": sales_col,
                    "promo_col": promo_c,
                    "store_col": store_c,
                    "item_col":  item_c,
                    "extra_num_cols": extra_num,
                    "extra_cat_cols": extra_cat,
                }
                st.success(f"✅ Dataset ready: {len(clean):,} rows after cleaning.")
                # Clear old models on new dataset
                st.session_state.model_lr  = None
                st.session_state.model_xgb = None
                st.session_state.metrics   = {}
                st.session_state.feature_names = []
                st.session_state.X_test = None
                st.session_state.y_test = None
                st.session_state.test_dates = None
                st.session_state.pop("last_forecast", None)
                st.session_state.pop("last_forecast_config", None)

        # ── Data preview ──────────────────────────────────────────────────────
        if st.session_state.clean_df is not None:
            st.markdown("---")
            render_section_heading("Validated Data", "Preview rows and review data-quality indicators.")
            clean = st.session_state.clean_df
            cfg   = st.session_state.config

            raw = st.session_state.df
            metric_columns = st.columns(4)
            with metric_columns[0]:
                render_metric_card("Validated rows", f"{len(clean):,}", "After date/sales validation", "teal")
            with metric_columns[1]:
                render_metric_card("Columns", f"{len(clean.columns):,}", "Available features", "blue")
            with metric_columns[2]:
                date_range = (
                    f"{pd.to_datetime(clean[cfg['date_col']]).min():%b %d, %Y} – "
                    f"{pd.to_datetime(clean[cfg['date_col']]).max():%b %d, %Y}"
                )
                render_metric_card("Date range", date_range, cfg["date_col"], "purple")
            with metric_columns[3]:
                render_metric_card(
                    "Raw duplicate rows",
                    f"{int(raw.duplicated().sum()):,}",
                    "Exact duplicate records in uploaded data",
                    "pink",
                )

            search_text = st.text_input("Search validated rows", placeholder="Search any column value…")
            preview = clean
            if search_text:
                matching_rows = clean.astype(str).apply(
                    lambda column: column.str.contains(
                        search_text, case=False, na=False, regex=False
                    )
                ).any(axis=1)
                preview = clean.loc[matching_rows]
                st.caption(f"{len(preview):,} matching rows")
            st.dataframe(preview.head(200), use_container_width=True)

            miss = missing_value_summary(raw)
            if not miss.empty:
                st.warning("Missing values in the uploaded source data:")
                st.dataframe(miss, use_container_width=True)
            else:
                st.success("No missing values detected in the uploaded source data.")

            numerical = clean.select_dtypes(include=[np.number]).describe().T
            if not numerical.empty:
                with st.expander("Numerical summaries"):
                    st.dataframe(numerical, use_container_width=True)

            with st.expander("📊 Data Types"):
                st.dataframe(clean.dtypes.astype(str).rename("dtype").to_frame(), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: EDA
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    render_section_heading("Analytics", "Explore trends, seasonality, promotions, and relationships.")

    df = st.session_state.clean_df
    if df is None:
        st.warning("⚠️ Please load and validate a dataset first (📂 Dataset page).")
        st.stop()

    cfg = st.session_state.config
    dc, sc = cfg["date_col"], cfg["sales_col"]
    pc, stc, ic = cfg.get("promo_col"), cfg.get("store_col"), cfg.get("item_col")

    # Sample for large datasets to keep EDA fast
    MAX_EDA_ROWS = 200_000
    if len(df) > MAX_EDA_ROWS:
        st.info(f"ℹ️ Dataset has {len(df):,} rows. Showing a random sample of {MAX_EDA_ROWS:,} for EDA charts.")
        eda_df = df.sample(MAX_EDA_ROWS, random_state=42).sort_values(dc)
    else:
        eda_df = df

    st.markdown("#### Animated Monthly Sales")
    animated_group_options = [
        column for column in [stc, ic, "Category"] if column and column in eda_df.columns
    ]
    animated_group = st.selectbox(
        "Color by",
        ["No grouping"] + animated_group_options,
        key="analytics_animated_group",
    )
    st.button("Replay animation", key="analytics_vizzu_replay")
    animated_group_col = None if animated_group == "No grouping" else animated_group
    animated_sales = prepare_animated_sales_data(
        eda_df, dc, sc, group_col=animated_group_col
    )
    if animated_sales.empty:
        st.info("No valid monthly sales values are available for the animated chart.")
    else:
        from st_vizzu import create_vizzu_obj, vizzu_animate, vizzu_plot

        animated_chart = create_vizzu_obj(animated_sales)
        animated_chart.analytics = False
        channels = {"x": "Month", "y": "Sales"}
        if animated_group_col is not None:
            channels["color"] = "Group"
        animated_chart = vizzu_animate(
            animated_chart,
            {
                "channels": channels,
                "geometry": "line",
                "title": "Monthly Sales Trend",
                "sort": "none",
            },
        )
        animated_chart = vizzu_animate(
            animated_chart,
            style_dict={
                "backgroundColor": "#0B1220FF",
                "plot": {
                    "marker": {
                        "colorPalette": (
                            "#2DD4BFFF #8B5CF6FF #38BDF8FF #F472B6FF"
                        )
                    },
                    "xAxis": {
                        "label": {"color": "#94A3B8FF"},
                        "title": {"color": "#CBD5E1FF"},
                        "interlacing": {"color": "#0B1220FF"},
                    },
                    "yAxis": {
                        "label": {"color": "#94A3B8FF"},
                        "title": {"color": "#CBD5E1FF"},
                        "interlacing": {"color": "#0B1220FF"},
                    },
                },
                "title": {"color": "#F8FAFCFF"},
            },
        )
        vizzu_plot(animated_chart, width=960, height=460)
        st.caption(
            "Click Replay animation to replay the monthly trend. Grouped charts "
            "show the six highest-sales groups; the rest are combined."
        )

    # ── Sales over time ────────────────────────────────────────────────────────
    st.markdown("#### 📈 Sales Over Time")
    group_for_time = st.selectbox("Group by", ["(none)"] + [c for c in [stc, ic] if c])
    group_time = None if group_for_time == "(none)" else group_for_time
    fig = plot_sales_over_time(eda_df, dc, sc,
                               store_col=group_time if group_time == stc else None,
                               item_col=group_time  if group_time == ic  else None)
    render_chart(fig)

    # ── Distribution & averages ────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        render_chart(plot_sales_distribution(eda_df, sc))
    with c2:
        period = st.radio("Average sales by", ["month", "dayofweek"], horizontal=True)
        render_chart(plot_avg_by_period(eda_df, dc, sc, period=period))

    # ── Promo comparison ───────────────────────────────────────────────────────
    if pc and pc in eda_df.columns:
        st.markdown("#### 🎁 Promotion Effect")
        render_chart(plot_promo_comparison(eda_df, sc, pc))
    else:
        st.info("ℹ️ No promotion column selected — promotion comparison chart skipped.")

    # ── Group comparison ───────────────────────────────────────────────────────
    group_opts = [c for c in [stc, ic, "Category"] if c and c in eda_df.columns]
    if group_opts:
        st.markdown("#### 🏪 Sales by Group")
        selected_group = st.selectbox("Group by column", group_opts)
        render_chart(plot_group_comparison(eda_df, selected_group, sc))

    # ── Correlation heatmap ────────────────────────────────────────────────────
    st.markdown("#### 🔗 Correlation Heatmap")
    num_cols = eda_df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        render_chart(plot_correlation_heatmap(eda_df, num_cols[:12]))
    else:
        st.info("ℹ️ Not enough numeric columns for a correlation heatmap.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MODEL TRAINING
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Model Performance":
    from src.model_training import (
        evaluate_model, get_feature_importance, get_predictions, save_model,
        train_linear_regression, train_xgboost,
    )

    render_section_heading("Model Performance", "Train and compare models using a chronological holdout.")

    df = st.session_state.clean_df
    if df is None:
        st.warning("⚠️ Please load and validate a dataset first.")
        st.stop()

    cfg = st.session_state.config
    dc, sc = cfg["date_col"], cfg["sales_col"]

    # ── Sampling for large datasets ────────────────────────────────────────────
    MAX_TRAIN_ROWS = 150_000
    if len(df) > MAX_TRAIN_ROWS:
        st.info(
            f"ℹ️ Dataset has {len(df):,} rows. Training on a recent chronological "
            f"sample of {MAX_TRAIN_ROWS:,} rows for speed. "
            "Uncheck to use all data (slower)."
        )
        use_sample = st.checkbox("Use full dataset (slower)", value=False)
        if not use_sample:
            train_df = df.sort_values(dc).tail(MAX_TRAIN_ROWS).reset_index(drop=True)
        else:
            train_df = df
    else:
        train_df = df

    # ── Hyperparameter controls ────────────────────────────────────────────────
    with st.expander("⚙️ Training Options", expanded=False):
        test_size = st.slider("Test set size (%)", 10, 40, 20)
        n_estimators = st.slider("XGBoost: n_estimators", 50, 500, 200, step=50)
        max_depth    = st.slider("XGBoost: max_depth",     3, 10,  5)
        lr_xgb       = st.slider("XGBoost: learning_rate", 0.01, 0.3, 0.05, step=0.01)

    if st.button("🚀 Train Both Models", type="primary", use_container_width=True):
        with st.spinner("Building features…"):
            try:
                X, y, feat_names = build_feature_matrix(
                    train_df,
                    date_col=dc,
                    sales_col=sc,
                    promo_col=cfg.get("promo_col"),
                    store_col=cfg.get("store_col"),
                    item_col=cfg.get("item_col"),
                    extra_num_cols=cfg.get("extra_num_cols"),
                    extra_cat_cols=cfg.get("extra_cat_cols"),
                )
            except ValueError as e:
                st.error(str(e))
                st.stop()

        # Align dates to X index
        dates_all = train_df[dc].iloc[train_df.index.isin(X.index) if hasattr(X.index, 'isin') else slice(None)]
        dates_all = train_df.loc[X.index, dc] if len(X) <= len(train_df) else train_df[dc]

        # Chronological split
        n_test = max(int(len(X) * test_size / 100), 1)
        X_train, X_test = X.iloc[:-n_test], X.iloc[-n_test:]
        y_train, y_test = y.iloc[:-n_test], y.iloc[-n_test:]
        dates_test = train_df.loc[X_test.index, dc] if X_test.index[-1] < len(train_df) else train_df[dc].tail(n_test)

        st.session_state.feature_names = feat_names
        st.session_state.X_test = X_test
        st.session_state.y_test = y_test
        st.session_state.test_dates = dates_test

        metrics = {}

        # Linear Regression
        with st.spinner("Training Linear Regression…"):
            lr_model = train_linear_regression(X_train, y_train)
            lr_metrics = evaluate_model(lr_model, X_test, y_test)
            metrics["Linear Regression"] = lr_metrics
            st.session_state.model_lr = lr_model
            save_model(lr_model, ROOT / "models" / "linear_regression.joblib")

        # XGBoost
        with st.spinner("Training XGBoost…"):
            xgb_model, xgb_err = train_xgboost(
                X_train, y_train,
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=lr_xgb,
            )
            if xgb_err:
                st.error(xgb_err)
            else:
                xgb_metrics = evaluate_model(xgb_model, X_test, y_test)
                metrics["XGBoost"] = xgb_metrics
                st.session_state.model_xgb = xgb_model
                save_model(xgb_model, ROOT / "models" / "xgboost.joblib")

        st.session_state.metrics = metrics
        st.success("✅ Training complete!")

    # ── Results ────────────────────────────────────────────────────────────────
    if st.session_state.metrics:
        metrics = st.session_state.metrics
        st.markdown("---")
        render_section_heading("Evaluation Results", "Metrics are calculated on the held-out test period.")

        best = min(metrics, key=lambda m: metrics[m]["rmse"])
        cols_m = st.columns(len(metrics))
        for i, (name, m) in enumerate(metrics.items()):
            with cols_m[i]:
                badge = " 🏆 Best" if name == best else ""
                r_squared = model_r_squared(name)
                st.metric(f"{name}{badge} · RMSE", f"{m['rmse']:.3f}", f"MAE: {m['mae']:.3f}")
                if r_squared is not None:
                    st.metric("R-squared", f"{r_squared:.3f}")

        st.markdown(f"""
        <div class="info-box">
        🏆 <b>{best}</b> achieved the lowest RMSE of <b>{metrics[best]['rmse']:.3f}</b> on the test set.<br>
        RMSE measures the average prediction error in the same units as sales.
        A lower RMSE means the model's predictions are closer to actual values.
        <i>Note: These results are on the held-out test set only — real-world accuracy may vary.</i>
        </div>
        """, unsafe_allow_html=True)

        # Model comparison chart
        if len(metrics) > 1:
            render_chart(plot_model_comparison(metrics))

        # Actual vs predicted chart
        if st.session_state.X_test is not None:
            X_test = st.session_state.X_test
            y_test = st.session_state.y_test
            test_dates = st.session_state.test_dates

            pred_lr  = get_predictions(st.session_state.model_lr, X_test) if st.session_state.model_lr  else None
            pred_xgb = get_predictions(st.session_state.model_xgb, X_test) if st.session_state.model_xgb else None

            fig_avp = plot_actual_vs_predicted(
                test_dates, y_test.values, pred_lr, pred_xgb, # type: ignore
                date_col=st.session_state.config["date_col"],
            )
            render_chart(fig_avp)

        # Feature importance
        fi_model = st.session_state.model_xgb or st.session_state.model_lr
        if fi_model:
            imp = get_feature_importance(fi_model, st.session_state.feature_names)
            if imp:
                with st.expander("🔬 Feature Importance"):
                    render_chart(plot_feature_importance(imp))


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: FORECAST
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Forecast Studio":
    render_section_heading("Forecast Studio", "Configure a model-backed forecast and export its results.")

    df = st.session_state.clean_df
    if df is None:
        st.warning("⚠️ Please load a dataset first.")
        st.stop()

    model_lr  = st.session_state.model_lr
    model_xgb = st.session_state.model_xgb

    if model_lr is None and model_xgb is None:
        st.warning("⚠️ Please train the models first (🤖 Model Training page).")
        st.stop()

    cfg = st.session_state.config
    dc, sc = cfg["date_col"], cfg["sales_col"]

    st.markdown("""
    <div class="electric-panel">
      <h3>Recursive forecast · real model output</h3>
      <p>Each predicted day feeds the next step's lag features. The engine only uses
      historical sales before the forecast period; future actuals are not used.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ───────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        model_opts = []
        if model_lr:  model_opts.append("Linear Regression")
        if model_xgb: model_opts.append("XGBoost")
        chosen_model_name = st.selectbox("🤖 Choose model", model_opts)
        chosen_model = model_lr if chosen_model_name == "Linear Regression" else model_xgb

        horizon = st.selectbox("📅 Forecast horizon", [7, 14, 30, 60, 90],
                               format_func=lambda x: f"{x} days")

    with c2:
        last_date = pd.to_datetime(df[dc]).max()
        start_date = st.date_input(
            "🗓 Forecast start date",
            value=last_date.date(),
            min_value=last_date.date(),
        )
        future_promo = st.radio("🎁 Promotion active during forecast?",
                                [0, 1], format_func=lambda x: "Yes" if x else "No",
                                horizontal=True)

    # ── Group filter ───────────────────────────────────────────────────────────
    store_c = cfg.get("store_col")
    item_c  = cfg.get("item_col")
    store_filter = item_filter = None

    if store_c and store_c in df.columns:
        stores = df[store_c].unique().tolist()
        store_filter = st.selectbox(f"🏪 Select {store_c}", stores)
    if item_c and item_c in df.columns:
        items = df[item_c].unique().tolist()
        item_filter = st.selectbox(f"📦 Select {item_c}", items)

    if st.button("🔮 Generate Forecast", type="primary", use_container_width=True):
        forecast_dates = make_forecast_dates(
            pd.Timestamp(start_date), horizon=horizon
        )
        forecast_config = {
            **cfg,
            "feature_names": st.session_state.feature_names,
            "future_promo":  future_promo,
            "store_filter":  store_filter,
            "item_filter":   item_filter,
        }

        with st.spinner(f"Generating {horizon}-day forecast with {chosen_model_name}…"):
            try:
                forecast_df = generate_forecast(
                    chosen_model, df, forecast_dates, forecast_config
                )
            except Exception as e:
                st.error(f"❌ Forecasting error: {e}")
                st.stop()

        st.session_state["last_forecast"] = forecast_df
        st.session_state["last_forecast_config"] = forecast_config

        # ── Results ────────────────────────────────────────────────────────────
        st.markdown("---")
        f1, f2, f3 = st.columns(3)
        f1.metric("Total Forecast Sales", f"{forecast_df['Predicted_Sales'].sum():,.0f}")
        f2.metric("Avg Daily Sales", f"{forecast_df['Predicted_Sales'].mean():.1f}")
        f3.metric("Forecast Horizon", f"{horizon} days")

        # Chart
        forecast_history = df
        if store_c and store_filter is not None:
            forecast_history = forecast_history[forecast_history[store_c] == store_filter]
        if item_c and item_filter is not None:
            forecast_history = forecast_history[forecast_history[item_c] == item_filter]
        render_chart(plot_forecast(forecast_history, forecast_df, dc, sc, tail_days=120))

        # Table
        st.dataframe(forecast_df.rename(columns={dc: "Date"}), use_container_width=True)

        # Download
        csv_bytes = forecast_df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download Forecast CSV",
            data=csv_bytes,
            file_name="sales_forecast.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Reports":
    render_section_heading(
        "Reports & Exports",
        "Read the project report and download available analysis artifacts.",
    )

    report_path = ROOT / "reports" / "project_report.md"
    if report_path.exists():
        with st.expander("Project report", expanded=False):
            st.markdown(report_path.read_text(encoding="utf-8"))
        st.download_button(
            "Download project report",
            data=report_path.read_bytes(),
            file_name=report_path.name,
            mime="text/markdown",
        )
    else:
        st.info("No Markdown project report is available in the reports folder.")

    document_path = ROOT / "reports" / "Sales_Forecasting_Project_Report_Final.docx"
    if document_path.exists():
        st.download_button(
            "Download final project report (DOCX)",
            data=document_path.read_bytes(),
            file_name=document_path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    render_section_heading("Saved analysis artifacts", "Existing files from the reports folder.")
    artifact_names = ("historical_sales.csv", "model_performance.csv", "sales_forecast.csv")
    available_artifacts = [
        ROOT / "reports" / name for name in artifact_names
        if (ROOT / "reports" / name).exists()
    ]
    if available_artifacts:
        columns = st.columns(min(3, len(available_artifacts)))
        for index, artifact in enumerate(available_artifacts):
            with columns[index % len(columns)]:
                st.download_button(
                    f"Download {artifact.name}",
                    data=artifact.read_bytes(),
                    file_name=artifact.name,
                    mime="text/csv",
                    key=f"download_report_{artifact.stem}",
                    use_container_width=True,
                )
    else:
        st.info("No saved CSV analysis artifacts are available.")

    current_forecast = st.session_state.get("last_forecast")
    if current_forecast is not None and not current_forecast.empty:
        st.markdown("---")
        render_section_heading("Current session forecast", "Generated from the active model and dataset.")
        st.dataframe(current_forecast, use_container_width=True)
        st.download_button(
            "Download current session forecast",
            data=current_forecast.to_csv(index=False).encode("utf-8"),
            file_name="salescast_forecast.csv",
            mime="text/csv",
            key="download_current_forecast",
        )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ═════════════════════════════════════════════════════════════════════════════
elif page == "About Project":
    render_section_heading("About the Project", "Sales forecasting methods, assumptions, and limitations.")

    tabs = st.tabs(["📐 Regression", "📊 Linear Regression", "🌳 XGBoost",
                    "🔧 Feature Engineering", "📏 RMSE", "⚠️ Limitations"])

    with tabs[0]:
        st.markdown("""
        ## What Is Regression?
        Regression is a type of **supervised machine learning** that predicts a
        **continuous numeric value** (like units sold) from input features.

        | Problem Type | Output | Example |
        |---|---|---|
        | **Regression** | Number | "Store A will sell 240 units next Monday" |
        | Classification | Category | "Sales will be HIGH / LOW" |

        Sales forecasting is a regression problem because we want the exact
        predicted quantity, not just a category.
        """)

    with tabs[1]:
        st.markdown("""
        ## Linear Regression
        Linear Regression fits a straight-line relationship between input features
        and the target:

        > **Sales = w₁×Lag1 + w₂×Month + w₃×Promo + … + b**

        - **w₁, w₂, …** are learned weights (coefficients)
        - **b** is the bias (intercept)
        - Very fast to train and easy to interpret
        - Assumes a linear relationship — may underfit complex patterns
        - We apply **StandardScaler** before fitting for numerical stability
        """)

    with tabs[2]:
        st.markdown("""
        ## XGBoost Regressor
        XGBoost (eXtreme Gradient Boosting) builds an **ensemble of decision trees**,
        where each new tree corrects the errors of the previous ones.

        **Key differences from Linear Regression:**
        | | Linear Regression | XGBoost |
        |---|---|---|
        | Model type | Single equation | 100–500 trees |
        | Captures non-linearity | ❌ No | ✅ Yes |
        | Training speed | Very fast | Moderate |
        | Interpretability | High | Medium (SHAP) |
        | Often wins on tabular data | — | ✅ Yes |

        XGBoost is one of the most widely used algorithms in Kaggle competitions.
        """)

    with tabs[3]:
        st.markdown("""
        ## Feature Engineering
        Raw data (a date and a sales number) is not enough for ML models.
        We transform it into informative **features**:

        | Feature type | Examples | Why it helps |
        |---|---|---|
        | **Calendar** | Month, day-of-week, quarter | Captures seasonality |
        | **Lag features** | Sales 7 days ago, 14 days ago | Autocorrelation |
        | **Rolling averages** | 7-day mean, 28-day mean | Trend smoothing |
        | **Promo flag** | 0/1 promotion indicator | Demand lift |
        | **Price** | Discount %, actual price | Price elasticity |

        ⚠️ **No data leakage**: all lag/rolling features use only past values —
        never the current or future day's sales.
        """)

    with tabs[4]:
        st.markdown(r"""
        ## RMSE — Root Mean Squared Error

        $$\text{RMSE} = \sqrt{ \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2 }$$

        - **yᵢ** = actual sales on day i
        - **ŷᵢ** = predicted sales on day i
        - **n** = number of test days

        RMSE is in the **same units as sales** (e.g. units sold).
        An RMSE of 15 means the model is off by about 15 units on average.

        **Lower RMSE = better model.**

        We also report **MAE** (Mean Absolute Error):

        $$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$

        MAE is less sensitive to large errors than RMSE.
        """)

    with tabs[5]:
        st.markdown("""
        ## Known Limitations

        1. **Synthetic dataset** — The built-in sample is artificially generated.
           Replace it with real Kaggle data for meaningful insights.
        2. **No external regressors** — Economic indicators, competitor pricing,
           and weather are not included.
        3. **Large datasets are sampled** — For speed, training uses up to 150 k rows.
        4. **Multi-step forecast error compounds** — Each step uses the previous
           predicted value; errors accumulate over longer horizons.
        5. **No hyperparameter tuning** — GridSearch/Optuna would improve RMSE further.
        6. **No uncertainty intervals** — Forecasts are point estimates, not ranges.
        7. **Assumes stationarity** — Sudden structural breaks (COVID, new stores)
           are not detected automatically.
        """)
