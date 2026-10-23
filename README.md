# AI-Based Sales Forecasting Using Machine Learning

> **Project #42 · Section 315 B**  
> B.Tech CSE — Artificial Intelligence & Machine Learning Lab

---

## Table of Contents

1. [Introduction](#introduction)
2. [Objectives](#objectives)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Dataset](#dataset)
6. [Installation (Windows)](#installation-windows)
7. [Running the Application](#running-the-application)
8. [Using the App](#using-the-app)
9. [Loading a Real Kaggle Dataset](#loading-a-real-kaggle-dataset)
10. [Running Tests](#running-tests)
11. [Known Limitations](#known-limitations)
12. [Troubleshooting](#troubleshooting)
13. [For the Class Presentation (PPT)](#for-the-class-presentation-ppt)

---

## Introduction

This project builds an **AI-powered sales forecasting application** that predicts future product sales using historical data, seasonal patterns, and promotional information.

Two machine learning algorithms are compared:

| Algorithm | Type | Strength |
|---|---|---|
| **Linear Regression** | Parametric | Fast, interpretable |
| **XGBoost Regressor** | Ensemble (boosted trees) | Handles complex patterns |

The primary evaluation metric is **RMSE** (Root Mean Squared Error). Lower RMSE = better predictions.

---

## Objectives

- Analyse historical sales data to uncover trends and seasonality
- Engineer time-based features (lag, rolling averages, calendar features)
- Train and compare Linear Regression vs XGBoost
- Provide an interactive web dashboard for training, evaluation, and forecasting
- Generate downloadable future sales predictions (CSV)

---

## Technology Stack

| Library | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| Streamlit | ≥1.28 | Web dashboard |
| streamlit-lottie | 0.0.5 | Local dashboard chart animation |
| st-vizzu | 0.1 | Animated Analytics charts |
| ipyvizzu | 0.18.0 | Animated chart engine used by st-vizzu |
| Pandas | ≥2.0 | Data manipulation |
| NumPy | ≥1.24 | Numerical computation |
| Scikit-learn | ≥1.3 | Linear Regression, preprocessing |
| XGBoost | ≥2.0 | XGBoost Regressor |
| Plotly | ≥5.15 | Interactive charts |
| Matplotlib | ≥3.7 | Static charts |
| Joblib | ≥1.3 | Model save/load |
| Pytest | ≥7.4 | Unit testing |

---

## Project Structure

```
sales-forecasting/
├── app.py                         ← Main Streamlit application
├── requirements.txt               ← Python dependencies
├── README.md                      ← This file
├── .gitignore
├── data/
│   └── sample_sales.csv           ← Synthetic demonstration dataset
├── models/
│   ├── linear_regression.joblib   ← Saved after training
│   └── xgboost.joblib             ← Saved after training
├── src/
│   ├── __init__.py
│   ├── data_processing.py         ← CSV loading, validation, splitting
│   ├── feature_engineering.py     ← Calendar, lag, rolling features
│   ├── animated_analytics.py      ← Monthly sales aggregation for Vizzu
│   ├── model_training.py          ← Train LR & XGB, evaluate RMSE/MAE
│   ├── forecasting.py             ← Recursive multi-step forecasting
│   ├── visualization.py           ← Plotly chart factory
│   └── styles.py                  ← SALESCAST dark theme and visual effects
├── assets/
│   ├── salescast-mark.svg         ← Animated SALESCAST chart mark
│   ├── salescast-wordmark.svg     ← SALESCAST logo and tagline
│   └── salescast-lottie.json      ← Local one-shot chart animation
├── tests/
│   ├── test_data_processing.py
│   ├── test_feature_engineering.py
│   └── test_forecasting.py
└── reports/
    └── project_report.md          ← Formal academic report
```

---

## Dataset

### Built-in Synthetic Dataset (`data/sample_sales.csv`)

> ⚠️ **This is artificially generated data** for demonstration purposes.  
> It is **NOT** from Kaggle. The data simulates realistic retail patterns  
> (trends, seasonality, promotions) but does not represent any real business.

**Columns used from the full synthetic dataset:**

| Column | Type | Description |
|---|---|---|
| Date | Date | Daily date (YYYY-MM-DD) |
| Store | String | Store identifier (S01–S20) |
| Item | String | Product identifier (I001–I020) |
| Category | String | Product category |
| Sales | Integer | Units sold — **prediction target** |
| Promo | Binary | 1 = promotion active, 0 = no promotion |
| Discount_Pct | Float | Discount percentage |
| Base_Price_INR | Float | Base price in Indian Rupees |
| Price_INR | Float | Actual selling price |
| Revenue_INR | Float | Revenue = Sales × Price_INR |
| IsHoliday | Binary | 1 = holiday |
| IsWeekend | Binary | 1 = Saturday or Sunday |

---

## Installation (Windows)

### Step 1 — Check Python

Open PowerShell or Command Prompt and verify Python is installed:

```powershell
py --version
```

You should see `Python 3.11.x` or higher. If not, download from [python.org](https://www.python.org/downloads/).

### Step 2 — Navigate to the project folder

```powershell
cd d:\NewProject\sales-forecasting
```

### Step 3 — Install dependencies (once)

Double-click `requirements.bat`. It creates a project virtual environment and
installs the required libraries. This can take a few minutes the first time.
Run it again only if you need to repair the environment or after changing
`requirements.txt`.

### Step 4 — Dataset

The built-in sample dataset is included at `data/sample_sales.csv`; no copy is
needed. To use a different dataset, upload its CSV in the app or replace the
sample file with your own:

```powershell
copy ..\sales_forecasting_synthetic.csv data\sample_sales.csv
```

You can also upload a CSV directly in the app.

---

## Running the Application

On Windows, double-click `run.bat` to start the dashboard after running
`requirements.bat` once. The launcher does not reinstall packages.

To start it manually from an activated project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The browser will open automatically at **http://localhost:8501**

---

## Using the App

The redesigned **SALESCAST — Intelligent Sales Analytics** interface keeps the
existing Streamlit forecasting pipeline and adds a dark, responsive analytics
workspace. Its cards, navigation, and restrained grid/neon effects are built
with CSS. The dashboard uses `streamlit-lottie` with a bundled animation file;
it does not fetch animation data from an external service.

### Dashboard
- Review data/model readiness and KPIs computed from the validated dataset,
  held-out evaluation, and any forecast generated in the current session.
- Compare historical sales with the real forecast when one is available.

### Data Explorer
- Load the included sample or upload a CSV, choose the date and target columns,
  and click **Validate & Apply**.
- Inspect the validated data, source missing values, duplicate rows, date
  range, numerical summaries, and search-filtered preview.

### Analytics
- Explore an animated monthly sales trend, distribution, seasonal patterns,
  promotion effects, group comparisons, and numeric correlations when the
  selected data supports those views. The animated chart can be colored by
  store, item, or category. The wrapper loads Vizzu's JavaScript runtime from
  jsDelivr; sales aggregation runs locally, and ipyvizzu usage analytics are
  disabled.

### Model Performance
- Click **Train Both Models** to train Linear Regression and XGBoost using the
  current chronological train/test split.
- Compare actual computed RMSE, MAE, and R-squared, inspect predictions, and
  review available feature importance.

### Forecast Studio
- Select a trained model, one of the supported horizons (7/14/30/60/90 days),
  and promotion/group settings.
- Generate the recursive model forecast, inspect its chart and table, and
  download the result as CSV.

### Reports
- Read or download the project report and download saved report CSVs.
- A forecast generated in the active session is separately available for
  display and download.

### About Project
- Review explanations of the regression models, feature engineering,
  evaluation metric, and known limitations.

---

## Loading a Real Kaggle Dataset

The built-in dataset is synthetic. For a real-world demonstration:

### Option A — Rossmann Store Sales (Kaggle)
1. Create a free account at [kaggle.com](https://www.kaggle.com)
2. Download from: `https://www.kaggle.com/competitions/rossmann-store-sales/data`
3. Use `train.csv` — it has columns `Date`, `Sales`, `Store`, `Promo`, `StateHoliday`
4. Copy it to `data/` and upload it in the app's Dataset page
5. Select: Date = `Date`, Sales = `Sales`, Store = `Store`, Promo = `Promo`

### Option B — Store Item Demand Forecasting (Kaggle)
1. Download from: `https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data`
2. Use `train.csv` — columns: `date`, `store`, `item`, `sales`
3. Upload in the app; select Date = `date`, Sales = `sales`

### Note on column names
The app auto-detects common column names. If detection is wrong, use the dropdown menus on the Dataset page to manually select the correct columns.

---

## Running Tests

```powershell
py -m pytest tests/ -v
```

Expected output: all tests pass (22+ test cases covering data loading, feature engineering, no-leakage guarantees, chronological splitting, RMSE calculation, and forecasting).

---

## Known Limitations

1. **Synthetic data only** (built-in sample) — does not represent a real business.
2. **Training is sampled** for large datasets (≤150,000 most recent rows by default) for speed.
3. **Multi-step forecast error compounds** — errors grow for longer horizons.
4. **No confidence intervals** — forecasts are point estimates only.
5. **No automated hyperparameter tuning** — XGBoost uses fixed defaults.
6. **Seasonality assumed to be yearly** — weekly/monthly patterns from calendar features.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `py -m pip install -r requirements.txt` |
| `XGBoost not found` | Run `py -m pip install xgboost` |
| App page shows blank white screen | Hard-refresh browser (Ctrl+Shift+R) |
| Training is very slow | Enable "Use sample" checkbox (150k rows instead of full dataset) |
| `Forecast error: not enough history` | Need at least 30 rows in the selected store/item group |
| CSV upload fails | Ensure file is UTF-8 encoded; remove special characters from column names |

---

## For the Class Presentation (PPT)

### Recommended slide structure (12–15 slides):

| # | Slide Title | Content |
|---|---|---|
| 1 | Title Slide | Project name, #42, Section 315 B, your name, date |
| 2 | Problem Statement | Why sales forecasting matters; business impact |
| 3 | Objective | What the app does; bullet list |
| 4 | Dataset | Columns, row count, source (synthetic + how to replace with Kaggle) |
| 5 | Methodology Overview | Flow: Data → Features → Train → Evaluate → Forecast |
| 6 | Feature Engineering | Calendar, lag, rolling features; explain "no leakage" |
| 7 | Linear Regression | Equation, diagram, pros/cons |
| 8 | XGBoost | Ensemble of trees, how it beats LR on tabular data |
| 9 | Evaluation Metrics | RMSE formula, MAE, why RMSE matters |
| 10 | Results | Screenshot of RMSE comparison from the app |
| 11 | Live Demo | Open the browser, run through the workflow |
| 12 | Applications | Retail, e-commerce, supply chain, manufacturing |
| 13 | Limitations & Future Work | Bullet list |
| 14 | Conclusion | 3-line summary |
| 15 | References | Kaggle, scikit-learn docs, XGBoost paper |

### Viva questions to prepare:
- "What is RMSE and why is it used?"
- "Why do you use a chronological split instead of random?"
- "What is a lag feature? Does it cause data leakage?"
- "How does XGBoost differ from a decision tree?"
- "What would you do to improve the model?"
- "What are the limitations of your application?"

### Live demo steps (practice this!):
1. Open terminal → `py -m streamlit run app.py`
2. Go to Dataset → Load Sample Dataset → Validate
3. Go to EDA → show Sales Over Time chart
4. Go to Model Training → Train Both Models → show RMSE
5. Go to Forecast → 14-day forecast → Download CSV

---

*Built with ❤️ using Python, Streamlit, and Machine Learning*  
*Project #42 · Section 315 B · B.Tech CSE*
#   S a l e s - F o r  
 #   S a l e s - F o r  
 #   S a l e s - F o r  
 