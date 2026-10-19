"""
app.py  — AI-Based Sales Forecasting Using Machine Learning
============================================================
Streamlit dashboard for Project #42, Section 315 B.

Run:  py -m streamlit run app.py
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

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
from src.visualization import (
    plot_actual_vs_predicted, plot_avg_by_period, plot_correlation_heatmap,
    plot_feature_importance, plot_forecast, plot_group_comparison,
    plot_model_comparison, plot_promo_comparison, plot_sales_distribution,
    plot_sales_over_time,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Sales Forecasting | Project #42",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  .main { background: #0e1117; }

  .kpi-card {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    border: 1px solid #2d3561;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(76,155,232,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(76,155,232,0.18);
  }
  .kpi-value { font-size: 2rem; font-weight: 700; color: #4C9BE8; }
  .kpi-label { font-size: 0.85rem; color: #8892a0; margin-top: 4px; }

  .section-header {
    font-size: 1.4rem; font-weight: 600;
    color: #e2e8f0;
    border-left: 4px solid #4C9BE8;
    padding-left: 12px;
    margin: 24px 0 16px;
  }
  .badge-best {
    background: linear-gradient(90deg,#4C9BE8,#7EC8A0);
    color: white; font-size: 0.75rem; font-weight: 600;
    padding: 2px 10px; border-radius: 20px;
  }
  .info-box {
    background: #1a2744; border-left: 4px solid #4C9BE8;
    border-radius: 8px; padding: 16px; margin: 12px 0;
    color: #c8d3e0;
  }
  .warn-box {
    background: #2a1a00; border-left: 4px solid #F4845F;
    border-radius: 8px; padding: 16px; margin: 12px 0;
    color: #e0c8b0;
  }
</style>
""", unsafe_allow_html=True)

# ── Session-state initialisation ──────────────────────────────────────────────
for key, default in {
    "df": None, "clean_df": None, "config": {},
    "model_lr": None, "model_xgb": None,
    "metrics": {}, "feature_names": [],
    "X_test": None, "y_test": None,
    "test_dates": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Sales Forecasting")
    st.markdown("**Project #42 · Section 315 B**")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📂 Dataset", "🔍 EDA", "🤖 Model Training", "🔮 Forecast", "📚 About"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Dataset Status**")
    if st.session_state.df is not None:
        n = len(st.session_state.df)
        st.success(f"✅ Loaded · {n:,} rows")
    else:
        st.warning("⚠️ No dataset loaded")

    st.markdown("**Model Status**")
    lr_ok  = st.session_state.model_lr is not None
    xgb_ok = st.session_state.model_xgb is not None
    st.write(f"{'✅' if lr_ok  else '❌'} Linear Regression")
    st.write(f"{'✅' if xgb_ok else '❌'} XGBoost")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.markdown("""
    <div style='text-align:center; padding: 32px 0 16px;'>
      <h1 style='font-size:2.6rem; font-weight:700; background:linear-gradient(90deg,#4C9BE8,#7EC8A0);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
        AI-Based Sales Forecasting
      </h1>
      <p style='color:#8892a0; font-size:1.1rem;'>
        Using Machine Learning · Project #42 · Section 315 B
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI cards ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    df = st.session_state.clean_df
    metrics = st.session_state.metrics

    with c1:
        val = f"{df[st.session_state.config.get('sales_col','Sales')].sum():,.0f}" if df is not None else "—"
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">Total Historical Sales</div></div>', unsafe_allow_html=True)
    with c2:
        val = f"{df[st.session_state.config.get('sales_col','Sales')].mean():.1f}" if df is not None else "—"
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">Average Daily Sales</div></div>', unsafe_allow_html=True)
    with c3:
        if metrics:
            best = min(metrics, key=lambda m: metrics[m]["rmse"])
        else:
            best = "—"
        st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="font-size:1.2rem;">{best}</div><div class="kpi-label">Best Model (RMSE)</div></div>', unsafe_allow_html=True)
    with c4:
        if metrics:
            best_rmse = min(m["rmse"] for m in metrics.values())
            val = f"{best_rmse:.2f}"
        else:
            val = "—"
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">Best RMSE</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Intro ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="section-header">🎯 Objective</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
        This application predicts future product sales using historical data,
        promotions, and seasonal patterns. It helps businesses estimate demand
        and plan inventory more efficiently.<br><br>
        Two ML models are compared:
        <ul>
          <li><b>Linear Regression</b> – fast, interpretable baseline</li>
          <li><b>XGBoost Regressor</b> – powerful gradient-boosted trees</li>
        </ul>
        Primary metric: <b>RMSE</b> (Root Mean Squared Error) — lower is better.
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">⚙️ How It Works</div>', unsafe_allow_html=True)
        steps = [
            ("1️⃣", "Upload Dataset", "Load your sales CSV or use the built-in sample data."),
            ("2️⃣", "Explore Data", "Visualise trends, seasonality, and promotional effects."),
            ("3️⃣", "Train Models", "Both models train on historical data; test RMSE is compared."),
            ("4️⃣", "Forecast", "The chosen model predicts sales for the next N days."),
        ]
        for icon, title, desc in steps:
            st.markdown(f"**{icon} {title}** — {desc}")

    with col2:
        st.markdown('<div class="section-header">🚀 Quick Start</div>', unsafe_allow_html=True)
        if st.button("📂 Load Sample Dataset", use_container_width=True, type="primary"):
            st.session_state.page_override = "📂 Dataset"
            st.rerun()

        st.markdown("---")
        st.markdown("**Dataset:**")
        st.code("data/sample_sales.csv", language="text")
        st.markdown("**Launch:**")
        st.code("py -m streamlit run app.py", language="bash")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: DATASET
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📂 Dataset":
    st.markdown('<div class="section-header">📂 Dataset Management</div>', unsafe_allow_html=True)

    col_upload, col_sample = st.columns(2)

    with col_upload:
        st.markdown("#### Upload your CSV")
        uploaded = st.file_uploader("Choose a CSV file", type="csv",
                                    help="Supported columns: Date, Sales, Store, Item, Promo, …")
        if uploaded:
            df_raw, err = load_csv(uploaded)
            if err:
                st.error(err)
            else:
                st.session_state.df = df_raw
                st.success(f"✅ Uploaded: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")

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
                    st.session_state.df = df_raw
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
        st.markdown('<div class="section-header">🗂 Column Configuration</div>', unsafe_allow_html=True)

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

        # ── Data preview ──────────────────────────────────────────────────────
        if st.session_state.clean_df is not None:
            st.markdown("---")
            st.markdown('<div class="section-header">👁️ Data Preview</div>', unsafe_allow_html=True)
            clean = st.session_state.clean_df
            cfg   = st.session_state.config

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Rows",    f"{len(clean):,}")
            m2.metric("Columns", len(clean.columns))
            m3.metric("Date Range",
                      f"{clean[cfg['date_col']].min().date()} – {clean[cfg['date_col']].max().date()}")
            m4.metric("Sales Range",
                      f"{clean[cfg['sales_col']].min():.0f} – {clean[cfg['sales_col']].max():.0f}")

            st.dataframe(clean.head(50), use_container_width=True)

            miss = missing_value_summary(clean)
            if not miss.empty:
                st.warning("⚠️ Missing values detected:")
                st.dataframe(miss, use_container_width=True)
            else:
                st.success("✅ No missing values after cleaning.")

            with st.expander("📊 Data Types"):
                st.dataframe(clean.dtypes.rename("dtype"), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: EDA
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔍 EDA":
    st.markdown('<div class="section-header">🔍 Exploratory Data Analysis</div>', unsafe_allow_html=True)

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

    # ── Sales over time ────────────────────────────────────────────────────────
    st.markdown("#### 📈 Sales Over Time")
    group_for_time = st.selectbox("Group by", ["(none)"] + [c for c in [stc, ic] if c])
    group_time = None if group_for_time == "(none)" else group_for_time
    fig = plot_sales_over_time(eda_df, dc, sc,
                               store_col=group_time if group_time == stc else None,
                               item_col=group_time  if group_time == ic  else None)
    st.plotly_chart(fig, use_container_width=True)

    # ── Distribution & averages ────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_sales_distribution(eda_df, sc), use_container_width=True)
    with c2:
        period = st.radio("Average sales by", ["month", "dayofweek"], horizontal=True)
        st.plotly_chart(plot_avg_by_period(eda_df, dc, sc, period=period), use_container_width=True)

    # ── Promo comparison ───────────────────────────────────────────────────────
    if pc and pc in eda_df.columns:
        st.markdown("#### 🎁 Promotion Effect")
        st.plotly_chart(plot_promo_comparison(eda_df, sc, pc), use_container_width=True)
    else:
        st.info("ℹ️ No promotion column selected — promotion comparison chart skipped.")

    # ── Group comparison ───────────────────────────────────────────────────────
    group_opts = [c for c in [stc, ic, "Category"] if c and c in eda_df.columns]
    if group_opts:
        st.markdown("#### 🏪 Sales by Group")
        selected_group = st.selectbox("Group by column", group_opts)
        st.plotly_chart(plot_group_comparison(eda_df, selected_group, sc), use_container_width=True)

    # ── Correlation heatmap ────────────────────────────────────────────────────
    st.markdown("#### 🔗 Correlation Heatmap")
    num_cols = eda_df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        st.plotly_chart(plot_correlation_heatmap(eda_df, num_cols[:12]), use_container_width=True)
    else:
        st.info("ℹ️ Not enough numeric columns for a correlation heatmap.")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: MODEL TRAINING
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🤖 Model Training":
    from src.model_training import (
        evaluate_model, get_feature_importance, get_predictions, save_model,
        train_linear_regression, train_xgboost,
    )

    st.markdown('<div class="section-header">🤖 Model Training & Evaluation</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="section-header">📊 Evaluation Results</div>', unsafe_allow_html=True)

        best = min(metrics, key=lambda m: metrics[m]["rmse"])
        cols_m = st.columns(len(metrics))
        for i, (name, m) in enumerate(metrics.items()):
            with cols_m[i]:
                badge = " 🏆 Best" if name == best else ""
                st.metric(f"{name}{badge}", f"RMSE: {m['rmse']:.3f}", f"MAE: {m['mae']:.3f}")

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
            st.plotly_chart(plot_model_comparison(metrics), use_container_width=True)

        # Actual vs predicted chart
        if st.session_state.X_test is not None:
            X_test = st.session_state.X_test
            y_test = st.session_state.y_test
            test_dates = st.session_state.test_dates

            pred_lr  = get_predictions(st.session_state.model_lr, X_test) if st.session_state.model_lr  else None
            pred_xgb = get_predictions(st.session_state.model_xgb, X_test) if st.session_state.model_xgb else None

            fig_avp = plot_actual_vs_predicted(
                test_dates, y_test.values, pred_lr, pred_xgb,
                date_col=st.session_state.config["date_col"],
            )
            st.plotly_chart(fig_avp, use_container_width=True)

        # Feature importance
        fi_model = st.session_state.model_xgb or st.session_state.model_lr
        if fi_model:
            imp = get_feature_importance(fi_model, st.session_state.feature_names)
            if imp:
                with st.expander("🔬 Feature Importance"):
                    st.plotly_chart(plot_feature_importance(imp), use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: FORECAST
# ═════════════════════════════════════════════════════════════════════════════
elif page == "🔮 Forecast":
    st.markdown('<div class="section-header">🔮 Future Sales Forecast</div>', unsafe_allow_html=True)

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
    <div class="info-box">
    📌 <b>How forecasting works:</b> Future predictions are generated step-by-step.
    Each day's predicted sales become the lag features for the next day.
    No actual future sales values are used — this is a true out-of-sample forecast.
    Forecasts are estimates; accuracy depends on historical data quality and
    assumptions about future promotions.
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
        st.plotly_chart(
            plot_forecast(df, forecast_df, dc, sc, tail_days=120),
            use_container_width=True
        )

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
# PAGE: ABOUT
# ═════════════════════════════════════════════════════════════════════════════
elif page == "📚 About":
    st.markdown('<div class="section-header">📚 About the Models & Methods</div>', unsafe_allow_html=True)

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
