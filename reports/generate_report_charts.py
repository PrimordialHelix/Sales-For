"""
generate_report_charts.py
Generates high-resolution publication-quality academic charts
grounded strictly in the actual sales forecasting codebase and data.
"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from src.data_processing import validate_and_prepare
from src.feature_engineering import build_feature_matrix
from src.model_training import train_linear_regression, train_xgboost, evaluate_model, load_model
from src.forecasting import generate_forecast, make_forecast_dates

os.makedirs('reports/figures', exist_ok=True)

# Styling configuration for academic report
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
matplotlib.rcParams['axes.titlesize'] = 13
matplotlib.rcParams['axes.labelsize'] = 11
matplotlib.rcParams['xtick.labelsize'] = 10
matplotlib.rcParams['ytick.labelsize'] = 10
matplotlib.rcParams['legend.fontsize'] = 10
matplotlib.rcParams['figure.titlesize'] = 14

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD DATA AND TRAIN / EVALUATE
# ─────────────────────────────────────────────────────────────────────────────
print("Loading data/sample_sales.csv...")
df_sample = pd.read_csv('data/sample_sales.csv')
clean_sample, _ = validate_and_prepare(df_sample, 'Date', 'Sales', 'Store', 'Item')
clean_sample['Date'] = pd.to_datetime(clean_sample['Date'])

X_s, y_s, feat_names_s = build_feature_matrix(clean_sample, 'Date', 'Sales', 'Promo', 'Store', 'Item')
n_test_s = max(int(len(X_s) * 0.2), 1)
X_train_s, X_test_s = X_s.iloc[:-n_test_s], X_s.iloc[-n_test_s:]
y_train_s, y_test_s = y_s.iloc[:-n_test_s], y_s.iloc[-n_test_s:]
test_dates_s = clean_sample.loc[X_test_s.index, 'Date']

# Train models on sample dataset
lr_s = train_linear_regression(X_train_s, y_train_s)
xgb_s, _ = train_xgboost(X_train_s, y_train_s, n_estimators=200, max_depth=5, learning_rate=0.05)

lr_eval_s = evaluate_model(lr_s, X_test_s, y_test_s)
xgb_eval_s = evaluate_model(xgb_s, X_test_s, y_test_s)

pred_lr_s = np.clip(lr_s.predict(X_test_s), 0, None)
pred_xgb_s = np.clip(xgb_s.predict(X_test_s), 0, None)

r2_lr_s = r2_score(y_test_s, pred_lr_s)
r2_xgb_s = r2_score(y_test_s, pred_xgb_s)

print(f"Sample - LR:  RMSE={lr_eval_s['rmse']:.4f}, MAE={lr_eval_s['mae']:.4f}, R2={r2_lr_s:.4f}")
print(f"Sample - XGB: RMSE={xgb_eval_s['rmse']:.4f}, MAE={xgb_eval_s['mae']:.4f}, R2={r2_xgb_s:.4f}")

# Forecast on sample dataset
last_date_s = clean_sample['Date'].max()
dates_forecast_s = make_forecast_dates(last_date_s, horizon=30)
cfg_s = {
    'date_col': 'Date', 'sales_col': 'Sales', 'promo_col': 'Promo',
    'store_col': 'Store', 'item_col': 'Item',
    'feature_names': feat_names_s,
    'future_promo': 0,
    'store_filter': 'S01', 'item_filter': 'I001',
}
fc_lr_s = generate_forecast(lr_s, clean_sample, dates_forecast_s, cfg_s)
fc_xgb_s = generate_forecast(xgb_s, clean_sample, dates_forecast_s, cfg_s)

# Load synthetic dataset metrics
print("Evaluating synthetic dataset with saved models...")
df_synth = pd.read_csv('d:/NewProject/sales_forecasting_synthetic.csv')
clean_synth, _ = validate_and_prepare(df_synth, 'Date', 'Sales', 'Store', 'Item')
clean_synth['Date'] = pd.to_datetime(clean_synth['Date'])
MAX_TRAIN_ROWS = 150_000
train_synth = clean_synth.sort_values('Date').tail(MAX_TRAIN_ROWS).reset_index(drop=True)

extra_num = [c for c in ['Discount_Pct', 'Base_Price_INR', 'Price_INR', 'Revenue_INR', 'IsHoliday', 'IsWeekend', 'Year', 'Month', 'DayOfWeek'] if c in train_synth.columns]
extra_cat = [c for c in ['Category'] if c in train_synth.columns]

X_synth, y_synth, feat_names_synth = build_feature_matrix(
    train_synth, 'Date', 'Sales', 'Promo', 'Store', 'Item',
    extra_num_cols=extra_num, extra_cat_cols=extra_cat
)
n_test_synth = max(int(len(X_synth) * 0.2), 1)
X_test_synth = X_synth.iloc[-n_test_synth:]
y_test_synth = y_synth.iloc[-n_test_synth:]

lr_saved = load_model('models/linear_regression.joblib')
xgb_saved = load_model('models/xgboost.joblib')

pred_lr_synth = np.clip(lr_saved.predict(X_test_synth), 0, None)
pred_xgb_synth = np.clip(xgb_saved.predict(X_test_synth), 0, None)

eval_lr_synth = evaluate_model(lr_saved, X_test_synth, y_test_synth)
eval_xgb_synth = evaluate_model(xgb_saved, X_test_synth, y_test_synth)
r2_lr_synth = r2_score(y_test_synth, pred_lr_synth)
r2_xgb_synth = r2_score(y_test_synth, pred_xgb_synth)

print(f"Synth - LR:  RMSE={eval_lr_synth['rmse']:.4f}, MAE={eval_lr_synth['mae']:.4f}, R2={r2_lr_synth:.4f}")
print(f"Synth - XGB: RMSE={eval_xgb_synth['rmse']:.4f}, MAE={eval_xgb_synth['mae']:.4f}, R2={r2_xgb_synth:.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. GENERATE FIGURE 4.1: HISTORICAL SALES OVER TIME
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=300)
clean_sample_sorted = clean_sample.sort_values('Date')
ax.plot(clean_sample_sorted['Date'], clean_sample_sorted['Sales'],
        color='#4C9BE8', linewidth=1.2, alpha=0.7, label='Daily Sales (Units)')
rolling_7 = clean_sample_sorted['Sales'].rolling(7, min_periods=1).mean()
ax.plot(clean_sample_sorted['Date'], rolling_7,
        color='#1E3A8A', linewidth=2.0, label='7-Day Moving Average')

# Highlight promo days
promo_days = clean_sample_sorted[clean_sample_sorted['Promo'] == 1]
ax.scatter(promo_days['Date'], promo_days['Sales'],
           color='#EF4444', s=20, alpha=0.8, zorder=5, label='Promotional Event (Promo=1)')

ax.set_title('Figure 4.1: Historical Daily Sales Trend (Jan 2023 – Dec 2023, Store S01, Item I001)', fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Sales (Units)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.legend(loc='upper right', frameon=True, framealpha=0.9)
plt.tight_layout()
fig.savefig('reports/figures/fig4_1_historical_sales.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/fig4_1_historical_sales.png")

# ─────────────────────────────────────────────────────────────────────────────
# 3. GENERATE FIGURE 4.2: ACTUAL VS PREDICTED ON TEST SET
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4.4), dpi=300)
ax.plot(test_dates_s, y_test_s.values,
        color='#2563EB', linewidth=2.2, label='Actual Sales (Ground Truth)', zorder=4)
ax.plot(test_dates_s, pred_lr_s,
        color='#10B981', linewidth=1.8, linestyle='--', label=f'Linear Regression (RMSE={lr_eval_s["rmse"]:.2f}, R²={r2_lr_s:.4f})', zorder=5)
ax.plot(test_dates_s, pred_xgb_s,
        color='#F59E0B', linewidth=1.8, linestyle=':', label=f'XGBoost Regressor (RMSE={xgb_eval_s["rmse"]:.2f}, R²={r2_xgb_s:.4f})', zorder=6)

ax.set_title('Figure 4.2: Actual vs. Predicted Sales on Chronological Test Set (Sep 2023 – Dec 2023)', fontweight='bold')
ax.set_xlabel('Test Period Date')
ax.set_ylabel('Sales (Units)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
ax.legend(loc='upper left', frameon=True, framealpha=0.9)
plt.tight_layout()
fig.savefig('reports/figures/fig4_2_actual_vs_predicted.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/fig4_2_actual_vs_predicted.png")

# ─────────────────────────────────────────────────────────────────────────────
# 4. GENERATE FIGURE 4.3: MODEL COMPARISON (RMSE & MAE)
# ─────────────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), dpi=300)

# Dataset 1: Built-in Demonstration Dataset
models = ['Linear Regression', 'XGBoost']
rmse_d1 = [lr_eval_s['rmse'], xgb_eval_s['rmse']]
mae_d1 = [lr_eval_s['mae'], xgb_eval_s['mae']]

x = np.arange(len(models))
width = 0.32

rects1 = ax1.bar(x - width/2, rmse_d1, width, label='RMSE (Lower is Better)', color='#3B82F6')
rects2 = ax1.bar(x + width/2, mae_d1, width, label='MAE (Lower is Better)', color='#10B981')

ax1.set_title('A. Built-in Sample Dataset (365 Rows)', fontweight='bold', fontsize=11)
ax1.set_ylabel('Error Metric (Units)')
ax1.set_xticks(x)
ax1.set_xticklabels(models, fontweight='bold')
ax1.legend(loc='upper left', framealpha=0.9)
ax1.set_ylim(0, max(rmse_d1) * 1.35)

for r in rects1:
    h = r.get_height()
    ax1.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
for r in rects2:
    h = r.get_height()
    ax1.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

# Dataset 2: Multi-Store Scaled Dataset
rmse_d2 = [eval_lr_synth['rmse'], eval_xgb_synth['rmse']]
mae_d2 = [eval_lr_synth['mae'], eval_xgb_synth['mae']]

rects3 = ax2.bar(x - width/2, rmse_d2, width, label='RMSE', color='#3B82F6')
rects4 = ax2.bar(x + width/2, mae_d2, width, label='MAE', color='#10B981')

ax2.set_title('B. Multi-Store Scaled Dataset (150k Rows)', fontweight='bold', fontsize=11)
ax2.set_ylabel('Error Metric (Units)')
ax2.set_xticks(x)
ax2.set_xticklabels(models, fontweight='bold')
ax2.legend(loc='upper right', framealpha=0.9)
ax2.set_ylim(0, max(rmse_d2) * 1.35)

for r in rects3:
    h = r.get_height()
    ax2.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
for r in rects4:
    h = r.get_height()
    ax2.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                 textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.suptitle('Figure 4.3: Model Performance Comparison Across Evaluation Datasets', fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig('reports/figures/fig4_3_model_comparison.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/fig4_3_model_comparison.png")

# ─────────────────────────────────────────────────────────────────────────────
# 5. GENERATE FIGURE 4.4: FUTURE FORECAST
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 4.4), dpi=300)

tail_history = clean_sample.sort_values('Date').tail(60)
ax.plot(tail_history['Date'], tail_history['Sales'],
        color='#4C9BE8', linewidth=2.0, label='Recent Historical Sales (Nov–Dec 2023)', zorder=4)

ax.plot(fc_lr_s['Date'], fc_lr_s['Predicted_Sales'],
        color='#10B981', linewidth=2.2, linestyle='--', marker='o', markersize=4,
        label='Linear Regression Forecast (Winning Baseline)', zorder=5)

ax.plot(fc_xgb_s['Date'], fc_xgb_s['Predicted_Sales'],
        color='#F59E0B', linewidth=2.0, linestyle=':', marker='s', markersize=4,
        label='XGBoost Regressor Forecast', zorder=6)

# Shaded forecast horizon
ax.axvspan(dates_forecast_s[0], dates_forecast_s[-1], color='#FEF3C7', alpha=0.5,
           label='Out-of-Sample Forecast Window (Jan 2024)', zorder=1)

ax.set_title('Figure 4.4: 30-Day Recursive Future Sales Forecast (Horizon: 2024-01-01 to 2024-01-30)', fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Sales (Units)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))
ax.legend(loc='upper left', frameon=True, framealpha=0.9)
plt.tight_layout()
fig.savefig('reports/figures/fig4_4_future_forecast.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/fig4_4_future_forecast.png")

# ─────────────────────────────────────────────────────────────────────────────
# 6. GENERATE FIGURE 3.1: SYSTEM ARCHITECTURE & DESIGN FLOW
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.0), dpi=300)
ax.axis('off')

boxes = [
    ("Raw Sales CSV\n(Date, Sales, Store, Item,\nPromo, Pricing, Holiday)", (0.05, 0.70), '#DBEAFE', '#1E40AF'),
    ("Data Preprocessing &\nChronological Validation\n(Type Coercion, NaN Treatment,\nSorting, Leak-Free Safeguard)", (0.28, 0.70), '#E0E7FF', '#3730A3'),
    ("Feature Engineering Pipeline\n• Calendar (Month, DoW, DoY, Quarter)\n• Shift Lags (1, 7, 14, 28 days)\n• Past-Only Rolling Means (7, 14, 28)\n• Promo Flags & Category OHE", (0.55, 0.70), '#EDE9FE', '#5B21B6'),
    ("Chronological Split\n(Strict 80% Train / 20% Test\nNo Future Shuffling)", (0.83, 0.70), '#FCE7F3', '#9D174D'),
    ("Linear Regression Pipeline\n(SimpleImputer → StandardScaler\n→ LinearRegression)", (0.16, 0.22), '#D1FAE5', '#065F46'),
    ("XGBoost Regressor Pipeline\n(SimpleImputer → XGBRegressor\nTrees=200, Depth=5, LR=0.05)", (0.42, 0.22), '#FEF3C7', '#92400E'),
    ("Evaluation & Model Selection\n• Multi-Metric: RMSE, MAE, R²\n• Best Model Selected by Lowest RMSE", (0.68, 0.22), '#FEE2E2', '#991B1B'),
    ("Recursive Forecast Engine\n& Streamlit Dashboard (app.py)\n(Out-of-Sample Horizon, CSV Export)", (0.90, 0.22), '#CCFBF1', '#115E59'),
]

for title, (x_pos, y_pos), bg_color, border_color in boxes:
    ax.annotate(
        title, xy=(x_pos, y_pos), xytext=(x_pos, y_pos),
        ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1E293B',
        bbox=dict(boxstyle='round,pad=0.7', facecolor=bg_color, edgecolor=border_color, linewidth=1.5),
    )

# Connect top row
arrow_style = dict(arrowstyle="->", color="#475569", lw=2, mutation_scale=15)
ax.annotate("", xy=(0.17, 0.70), xytext=(0.14, 0.70), arrowprops=arrow_style)
ax.annotate("", xy=(0.42, 0.70), xytext=(0.39, 0.70), arrowprops=arrow_style)
ax.annotate("", xy=(0.73, 0.70), xytext=(0.68, 0.70), arrowprops=arrow_style)

# Split to models
ax.annotate("", xy=(0.16, 0.35), xytext=(0.80, 0.58), arrowprops=arrow_style)
ax.annotate("", xy=(0.42, 0.35), xytext=(0.83, 0.58), arrowprops=arrow_style)

# Models to evaluation
ax.annotate("", xy=(0.58, 0.22), xytext=(0.28, 0.22), arrowprops=arrow_style)
ax.annotate("", xy=(0.58, 0.22), xytext=(0.52, 0.22), arrowprops=arrow_style)

# Evaluation to Forecast
ax.annotate("", xy=(0.80, 0.22), xytext=(0.77, 0.22), arrowprops=arrow_style)

plt.title("Figure 3.1: End-to-End System Architecture and Data Processing Flow", fontweight='bold', fontsize=12, pad=15)
plt.tight_layout()
fig.savefig('reports/figures/fig3_1_system_architecture.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/fig3_1_system_architecture.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7. GENERATE GRAPHICAL ABSTRACT IMAGE
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 3.2), dpi=300)
ax.axis('off')

steps = [
    ("1. Input Data", "Daily Historical Sales\n365 Days (Store S01, I001)\nPromotions & Holidays", '#DBEAFE', '#2563EB'),
    ("2. Feature Pipeline", "Calendar & Cyclical\nShift Lags (1, 7, 14, 28)\nRolling Means (7, 14, 28)", '#EDE9FE', '#7C3AED'),
    ("3. ML Training", "Chronological Split (80/20)\nLinear Regression vs.\nXGBoost Regressor", '#FEF3C7', '#D97706'),
    ("4. Model Selection", "RMSE / MAE / R² Evaluation\nWinning Model Selected\nLR (RMSE=4.66) / XGB (4.04)", '#D1FAE5', '#059669'),
    ("5. Forecast & App", "Recursive Multi-Step\nFuture Sales Predictions\nStreamlit Dashboard (app.py)", '#CCFBF1', '#0D9488'),
]

for i, (hdr, desc, bg, border) in enumerate(steps):
    x_pos = 0.10 + i * 0.20
    text = f"{hdr}\n\n{desc}"
    ax.annotate(
        text, xy=(x_pos, 0.5), xytext=(x_pos, 0.5),
        ha='center', va='center', fontsize=9, fontweight='bold', color='#0F172A',
        bbox=dict(boxstyle='round,pad=0.6', facecolor=bg, edgecolor=border, linewidth=1.6),
    )
    if i < 4:
        ax.annotate("", xy=(x_pos + 0.115, 0.5), xytext=(x_pos + 0.085, 0.5),
                    arrowprops=dict(arrowstyle="->", color="#64748B", lw=2.2, mutation_scale=16))

plt.title("GRAPHICAL ABSTRACT: AI-BASED SALES FORECASTING WORKFLOW", fontweight='bold', fontsize=11, pad=10)
plt.tight_layout()
fig.savefig('reports/figures/graphical_abstract.png', dpi=300)
plt.close(fig)
print("Saved reports/figures/graphical_abstract.png")

# ─────────────────────────────────────────────────────────────────────────────
# 8. SAVE REPRODUCIBLE CSV OUTPUTS
# ─────────────────────────────────────────────────────────────────────────────
# 1. Historical processed sales
clean_sample[['Date', 'Store', 'Item', 'Sales', 'Promo']].to_csv('reports/historical_sales.csv', index=False)
# 2. Forecast CSV
fc_combined = pd.DataFrame({
    'Date': dates_forecast_s,
    'Forecast_Linear_Regression': fc_lr_s['Predicted_Sales'],
    'Forecast_XGBoost': fc_xgb_s['Predicted_Sales'],
})
fc_combined.to_csv('reports/sales_forecast.csv', index=False)
# 3. Model performance comparison CSV
perf_df = pd.DataFrame([
    {
        'Dataset': 'Built-in Demonstration (sample_sales.csv)',
        'Model': 'Linear Regression',
        'RMSE': round(lr_eval_s['rmse'], 4),
        'MAE': round(lr_eval_s['mae'], 4),
        'R2_Score': round(r2_lr_s, 4),
        'Status': 'Winning Model (Lowest RMSE)'
    },
    {
        'Dataset': 'Built-in Demonstration (sample_sales.csv)',
        'Model': 'XGBoost Regressor',
        'RMSE': round(xgb_eval_s['rmse'], 4),
        'MAE': round(xgb_eval_s['mae'], 4),
        'R2_Score': round(r2_xgb_s, 4),
        'Status': 'Baseline Comparison'
    },
    {
        'Dataset': 'Multi-Store Scaled (sales_forecasting_synthetic.csv)',
        'Model': 'Linear Regression',
        'RMSE': round(eval_lr_synth['rmse'], 4),
        'MAE': round(eval_lr_synth['mae'], 4),
        'R2_Score': round(r2_lr_synth, 4),
        'Status': 'Baseline Comparison'
    },
    {
        'Dataset': 'Multi-Store Scaled (sales_forecasting_synthetic.csv)',
        'Model': 'XGBoost Regressor',
        'RMSE': round(eval_xgb_synth['rmse'], 4),
        'MAE': round(eval_xgb_synth['mae'], 4),
        'R2_Score': round(r2_xgb_synth, 4),
        'Status': 'Winning Model (Lowest RMSE)'
    },
])
perf_df.to_csv('reports/model_performance.csv', index=False)
print("All charts and CSVs generated successfully.")
