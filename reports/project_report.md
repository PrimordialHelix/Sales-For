# Project Report

## AI-Based Sales Forecasting Using Machine Learning

---

**Project Number:** 42  
**Section:** 315 B  
**Submitted by:** [Student Name — fill in]  
**UID:** [Student UID — fill in]  
**Faculty Guide:** [Faculty Name — fill in]  
**Institution:** [College Name — fill in]  
**Department:** Computer Science & Engineering  
**Submission Date:** [Date — fill in]

---

## Abstract

Sales forecasting is a critical business function that enables organizations to estimate future demand, optimize inventory, and plan resources efficiently. This project presents an AI-based sales forecasting system built with Python and Streamlit that applies two supervised machine learning algorithms — Linear Regression and XGBoost Regressor — to historical retail sales data. The system performs automated data validation, date-based feature engineering (including lag and rolling-window features), chronological train-test splitting to prevent data leakage, and recursive multi-step future forecasting. Model performance is evaluated using Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE). An interactive web dashboard provides data exploration, model training, evaluation, and downloadable forecasts. The application is designed to be understandable, demonstrable, and extensible for academic and real-world use cases.

---

## 1. Introduction

Forecasting future sales accurately is one of the most impactful applications of machine learning in business. Retailers use sales predictions to make decisions about stock replenishment, staffing, pricing, and promotional campaigns. Traditional statistical approaches such as moving averages and ARIMA models have long been used but struggle with complex, multi-dimensional datasets. Machine learning methods — particularly ensemble models — have demonstrated superior performance on large-scale retail datasets.

This project implements a complete, end-to-end sales forecasting pipeline using two commonly studied algorithms:

1. **Linear Regression** — a simple, interpretable model suitable as a baseline.
2. **XGBoost Regressor** — a powerful gradient-boosted tree ensemble that typically outperforms linear models on tabular data.

The application is built with Streamlit, providing an interactive interface suitable for both academic demonstration and practical use.

---

## 2. Problem Statement

**Problem Type:** Regression  
**Input:** Historical daily sales records including date, store/item identifiers, promotional flags, and price information.  
**Output:** Predicted future sales values for a user-specified horizon (7, 14, 30, 60, or 90 days).  
**Challenge:** Time-series forecasting requires careful feature engineering to avoid data leakage (using future information to predict the past), and chronological evaluation to ensure model results generalize to unseen future periods.

---

## 3. Objectives

1. Develop a machine learning pipeline that processes raw sales CSV data into a model-ready feature matrix.
2. Engineer calendar, lag, and rolling-window features that capture seasonality and autocorrelation without data leakage.
3. Train and compare Linear Regression and XGBoost Regressor on a chronological train-test split.
4. Evaluate both models using RMSE and MAE.
5. Implement recursive multi-step forecasting for future dates.
6. Provide a clean, interactive Streamlit dashboard for the complete workflow.
7. Produce downloadable forecast results in CSV format.

---

## 4. Dataset Description

### 4.1 Demonstration Dataset

The application ships with a **synthetic retail dataset** generated for demonstration purposes. It simulates 839,600 daily sales records across 20 stores and 20 products from January 2021 to September 2026.

> ⚠️ This is **NOT** a real Kaggle dataset. It is artificially generated to contain realistic patterns (seasonality, promotional lift, price elasticity) for model training and evaluation.

**Data Dictionary:**

| Column | Data Type | Description |
|---|---|---|
| Date | Date | Daily transaction date (YYYY-MM-DD) |
| Store | String | Store identifier (S01–S20) |
| Item | String | Product identifier (I001–I020) |
| Category | String | Product category (Grocery, Beverages, Personal Care, etc.) |
| Sales | Integer | Daily units sold — **prediction target** |
| Promo | Binary | 1 = promotion active, 0 = no promotion |
| Discount_Pct | Float | Percentage discount applied |
| Base_Price_INR | Float | Original price (Indian Rupees) |
| Price_INR | Float | Actual selling price after discount |
| Revenue_INR | Float | Total revenue = Sales × Price_INR |
| IsHoliday | Binary | 1 = public holiday |
| Holiday_Name | String | Name of the holiday (if applicable) |
| IsWeekend | Binary | 1 = Saturday or Sunday |
| Year | Integer | Calendar year (derived) |
| Month | Integer | Calendar month (derived) |
| DayOfWeek | Integer | Day of week 0=Mon … 6=Sun (derived) |

### 4.2 Real Kaggle Datasets (for replacement)

For a real-world project, the following Kaggle datasets are compatible:

- **Rossmann Store Sales**: https://www.kaggle.com/competitions/rossmann-store-sales
- **Store Item Demand Forecasting**: https://www.kaggle.com/competitions/demand-forecasting-kernels-only

---

## 5. Proposed Methodology and System Architecture

```
Raw CSV
   │
   ▼
Data Loading & Validation
(load_csv, validate_and_prepare)
   │
   ▼
Feature Engineering
(Calendar → Lag → Rolling → Promo → Encode)
   │
   ▼
Chronological Split (80% train / 20% test)
   │
   ├──► Linear Regression Pipeline
   │         (Imputer → Scaler → LinearRegression)
   │
   └──► XGBoost Pipeline
             (Imputer → XGBRegressor)
   │
   ▼
Evaluation (RMSE, MAE on test set)
   │
   ▼
Recursive Multi-Step Forecasting
(lag features filled from prior predictions)
   │
   ▼
Interactive Streamlit Dashboard
(EDA charts, training UI, forecast chart, CSV download)
```

---

## 6. Data Preprocessing and Feature Engineering

### 6.1 Preprocessing Steps

1. **Date parsing**: Convert date strings to `datetime` objects; drop unparseable rows.
2. **Sales coercion**: Convert sales to numeric; drop non-numeric rows.
3. **Duplicate removal**: Drop exact duplicate records.
4. **Chronological sorting**: Sort by (store, item, date) before any feature generation.
5. **Missing-value handling**: Remaining NaNs in features are filled with column medians by the `SimpleImputer` inside each model pipeline.

### 6.2 Feature Engineering

**Calendar Features** (extracted from the date):
- Year, Month, Day, Day of Week, Day of Year, Week of Year, Quarter
- Is Month Start, Is Month End

**Lag Features** (past sales values, shift-based — zero leakage):
- Lag 1 (yesterday), Lag 7 (one week ago), Lag 14 (two weeks ago), Lag 28 (four weeks ago)
- Within-group lags for multi-store/item datasets

**Rolling Mean Features** (past-only rolling window — shift by 1 before rolling):
- 7-day rolling mean, 14-day rolling mean, 28-day rolling mean

**Promotional Features**:
- Binary promo flag (0/1)
- Discount percentage (numeric)

**Categorical Encoding**:
- One-hot encoding of Store and Item identifiers

### 6.3 No-Leakage Guarantee

All lag features use `.shift(lag)` and rolling features use `.shift(1).rolling(window)`. This ensures that at row *i*, only information from rows 0 to *i-1* is visible to the model. The test set is the chronological tail of the dataset — no shuffling is applied.

---

## 7. Machine Learning Algorithms

### 7.1 Linear Regression

**Equation:**

$$\hat{y} = w_1 x_1 + w_2 x_2 + \cdots + w_n x_n + b$$

where $w_i$ are learned weights and $b$ is the bias term.

**Pipeline:**
1. `SimpleImputer(strategy='median')` — fills any remaining NaNs
2. `StandardScaler()` — normalizes features to zero mean, unit variance
3. `LinearRegression()` — ordinary least squares fit

**Strengths:** Fast, interpretable, good baseline  
**Weaknesses:** Cannot capture non-linear relationships; sensitive to outliers

### 7.2 XGBoost Regressor

XGBoost builds an ensemble of decision trees iteratively. Each tree corrects the residual errors of the previous ensemble:

$$F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x)$$

where $\eta$ is the learning rate and $h_m$ is the new tree.

**Hyperparameters used:**
- `n_estimators`: 200 (number of trees)
- `max_depth`: 5 (tree depth)
- `learning_rate`: 0.05
- `subsample`: 0.8 (row sampling per tree)
- `colsample_bytree`: 0.8 (feature sampling per tree)

**Pipeline:**
1. `SimpleImputer(strategy='median')` — fills NaNs
2. `XGBRegressor(...)` — gradient-boosted tree ensemble

**Strengths:** Handles non-linearity, interactions, and missing values; usually outperforms LR  
**Weaknesses:** Slower to train; less interpretable; can overfit without regularization

---

## 8. Evaluation Metrics

### 8.1 RMSE — Root Mean Squared Error

$$\text{RMSE} = \sqrt{ \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2 }$$

- Penalizes large errors more heavily (squaring amplifies outliers)
- In the same units as the target (sales units)
- **Lower is better**

### 8.2 MAE — Mean Absolute Error

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$

- Treats all errors equally
- More robust to outliers than RMSE
- **Lower is better**

### 8.3 Why Chronological Split?

A random train-test split would allow the model to "see the future" during training (e.g., training on data from 2024 while testing on 2023). This would give optimistic RMSE scores that do not reflect real-world performance. A **chronological split** keeps the test set strictly in the future relative to the training period.

---

## 9. Implementation Details

### 9.1 Module Structure

| Module | Responsibility |
|---|---|
| `src/data_processing.py` | CSV loading, column validation, cleaning, splitting |
| `src/feature_engineering.py` | Calendar, lag, rolling features; feature matrix construction |
| `src/model_training.py` | Pipeline training, evaluation, save/load |
| `src/forecasting.py` | Recursive multi-step future forecasting |
| `src/visualization.py` | Plotly chart factory (all charts) |
| `app.py` | Streamlit dashboard (5 pages) |

### 9.2 Recursive Forecasting Algorithm

```
history_buffer = list of all past sales values

for each forecast date d in [d₁, d₂, ..., d_H]:
    build feature row for d using:
        - calendar features (computed from d)
        - lag features (from history_buffer)
        - rolling mean features (from history_buffer)
        - promo flag (user-supplied)
    predict ŷ_d = model.predict(feature_row)
    append ŷ_d to history_buffer  ← feeds the next step
    record (d, ŷ_d)
```

No actual future sales values are used — only predicted values from prior steps.

---

## 10. Results

> ⚠️ **Placeholder Section** — Results below must be filled in after running actual experiments.

| Model | RMSE (Test Set) | MAE (Test Set) |
|---|---|---|
| Linear Regression | `[Run app to get value]` | `[Run app to get value]` |
| XGBoost | `[Run app to get value]` | `[Run app to get value]` |

**Best model:** `[Fill in after training]`

**Observations:** `[Fill in after reviewing actual vs predicted chart]`

**Sample forecast (14 days):** `[Screenshot from app]`

---

## 11. Applications

1. **Retail & E-commerce** — Stock replenishment, markdown pricing
2. **Supply Chain** — Production planning, warehouse capacity
3. **Food & Beverages** — Perishable inventory management
4. **Healthcare** — Pharmaceutical demand forecasting
5. **Manufacturing** — Raw material procurement
6. **Finance** — Revenue projection, budget planning

---

## 12. Limitations

1. The built-in dataset is **synthetic** — findings may not generalize to real data.
2. Multi-step forecast errors **compound** with horizon length.
3. The model has **no external regressors** (economic indicators, weather, competitor actions).
4. **No uncertainty quantification** — forecasts are point estimates without confidence intervals.
5. Assumes sales patterns are **stationary** — does not auto-detect structural breaks.
6. Training uses a **recent sample** of large datasets for speed (adjustable).

---

## 13. Future Scope

1. Integrate real-time data feeds via APIs (e.g., ERP systems, e-commerce platforms)
2. Add ARIMA/Prophet as comparison baselines
3. Implement Bayesian prediction intervals for uncertainty quantification
4. Include hyperparameter tuning with Optuna or GridSearchCV
5. Add SHAP explainability for XGBoost feature attribution
6. Extend to hierarchical forecasting (total → category → store → item)
7. Deploy on cloud (Streamlit Cloud, AWS, or Azure)

---

## 14. Conclusion

This project successfully implements a complete AI-based sales forecasting system that:

- Accepts and validates real or synthetic retail sales data
- Automatically engineers 15+ time-series features with zero data leakage
- Trains and compares Linear Regression and XGBoost with RMSE/MAE evaluation
- Generates recursive multi-step future forecasts
- Provides an intuitive Streamlit dashboard for all workflow steps

The system demonstrates that machine learning — particularly XGBoost — can effectively capture seasonal and promotional patterns in sales data, enabling businesses to make data-driven inventory and planning decisions.

---

## 15. References

1. Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *ACM SIGKDD*, 785–794.
2. Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *JMLR*, 12, 2825–2830.
3. Streamlit Documentation. https://docs.streamlit.io
4. Plotly Python Library. https://plotly.com/python/
5. Kaggle — Rossmann Store Sales. https://www.kaggle.com/competitions/rossmann-store-sales
6. Kaggle — Store Item Demand Forecasting. https://www.kaggle.com/competitions/demand-forecasting-kernels-only
7. Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts.

---

*This report is submitted in partial fulfilment of the requirements for the AI/ML Lab project.*
