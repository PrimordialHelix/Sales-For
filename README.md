# AI-Based Sales Forecasting Using Machine Learning

A Streamlit dashboard for exploring historical sales, comparing machine-learning regression models, and generating future sales forecasts.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Machine Learning](https://img.shields.io/badge/ML-Regression-7C3AED)
![Status](https://img.shields.io/badge/Project-Academic%20Demo-10B981)

## Overview

Sales forecasting estimates future demand from historical sales patterns and relevant business information. Forecasts can help with inventory planning, staffing, promotion planning, and demand management.

This project provides an interactive application for examining sales data, training and evaluating regression models, and exporting forecasts. It compares **Linear Regression** with **XGBoost Regressor** where XGBoost is available and successfully trained. The application reports evaluation metrics from the current run rather than relying on hardcoded results.

> **Dataset note:** The included `data/sample_sales.csv` is synthetically generated for demonstration. It is not a real business dataset and is not from Kaggle.

## Features

- Load the built-in sample dataset or upload a compatible CSV.
- Validate columns and inspect missing values, duplicates, date ranges, and summary statistics.
- Explore sales trends, distributions, seasonal patterns, promotion effects, and other supported data views.
- Create time-based features such as calendar features, lagged sales, and rolling statistics where supported by the pipeline.
- Train and compare Linear Regression and XGBoost models where available.
- Evaluate models using RMSE, MAE, and R-squared when those metrics can be calculated.
- Generate forecasts for supported horizons and export forecast results to CSV.
- Explore charts and reports through a Streamlit interface.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Application and model logic |
| Streamlit | Interactive dashboard |
| Pandas | Data loading and transformation |
| NumPy | Numerical operations |
| Scikit-learn | Preprocessing and Linear Regression |
| XGBoost | Gradient-boosted regression model, when installed and available |
| Plotly | Interactive charts |
| Matplotlib | Static charts where used |
| Joblib | Saving and loading trained models |
| Pytest | Automated tests |
| streamlit-lottie / st-vizzu | Optional dashboard animation and animated analytics, if enabled in the installed version |

## Project Structure

```text
sales-forecasting/
├── app.py                         # Main Streamlit application
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
├── requirements.bat               # Windows dependency setup helper
├── run.bat                        # Windows launch helper
├── data/
│   └── sample_sales.csv            # Synthetic demonstration dataset
├── models/                        # Generated model files (created during training)
├── src/
│   ├── __init__.py
│   ├── data_processing.py          # CSV loading, validation, and splitting
│   ├── feature_engineering.py      # Calendar, lag, and rolling features
│   ├── animated_analytics.py       # Monthly aggregation for animated charts
│   ├── model_training.py           # Model training and evaluation
│   ├── forecasting.py              # Multi-step forecasting
│   ├── visualization.py            # Chart helpers
│   └── styles.py                   # SALESCAST theme and visual styling
├── assets/                         # Local SVG and animation assets, if present
├── tests/                          # Automated tests
└── reports/                        # Generated reports and report documentation
```

> The tree describes the expected organization. Some files or optional modules may differ by project version; consult the actual workspace if a listed file is absent.

## Dataset

### Included demonstration data

The sample dataset is designed to demonstrate sales forecasting with generated retail-like patterns. It does not describe a real store or business.

| Column | Description |
|---|---|
| `Date` | Date associated with the observation |
| `Store` | Store identifier |
| `Item` | Product identifier |
| `Category` | Product category, where present |
| `Sales` | Units sold; the forecasting target |
| `Promo` | Promotion indicator (`1` = active, `0` = inactive) |
| `Discount_Pct` | Discount percentage, where present |
| `Base_Price_INR` | Base price in Indian rupees, where present |
| `Price_INR` | Actual selling price, where present |
| `Revenue_INR` | Revenue value, where present |
| `IsHoliday` | Holiday indicator, where present |
| `IsWeekend` | Weekend indicator, where present |

The application may accept other datasets if the required date and sales columns can be mapped. Optional columns, such as store or promotion, are only used when supported by the selected data and implementation.

### Using a real dataset

You can download an appropriate dataset from Kaggle, subject to its terms of use:

- [Rossmann Store Sales](https://www.kaggle.com/competitions/rossmann-store-sales/data)
- [Store Item Demand Forecasting Challenge](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data)

For Rossmann data, common columns include `Date`, `Sales`, `Store`, and `Promo`. For the Store Item Demand dataset, common columns include `date`, `store`, `item`, and `sales`.

Upload the CSV in the application's dataset page and map the correct columns. Do not describe results from the synthetic sample as real-world business performance.

## Installation on Windows

### 1. Check Python

Open PowerShell or Command Prompt:

```powershell
py --version
```

Python 3.11 or later is recommended.

### 2. Open the project folder

```powershell
cd "D:\NewProject\sales-forecasting"
```

### 3. Install dependencies

If the project setup helper is present, run:

```powershell
.\requirements.bat
```

Alternatively, create and activate a virtual environment manually:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents activation, you can run the environment's Python executable directly instead of changing execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Running the Application

If the Windows launcher exists, run:

```powershell
.\run.bat
```

Or start Streamlit manually:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard normally opens at <http://localhost:8501>.

## Using the App

1. **Dashboard:** Review dataset readiness, supported summary metrics, and historical-versus-forecast charts when available.
2. **Data Explorer:** Load the sample dataset or upload a CSV, map the date and sales columns, validate the data, and inspect summaries.
3. **Analytics:** Explore sales trends, distributions, seasonal patterns, promotion effects, group comparisons, and correlations where supported by the selected dataset.
4. **Model Performance:** Train the supported models and inspect the actual RMSE, MAE, R-squared, prediction comparisons, or feature importance that the application computes.
5. **Forecast Studio:** Select a trained model and a supported forecast horizon, generate a forecast, inspect the results, and download a CSV.
6. **Reports:** View or download reports and output files produced by the current project version.
7. **About Project:** Review the methodology, evaluation metrics, and limitations.

Page names and controls may vary slightly by version. Use the options actually shown in the running application.

## Model Evaluation

The project can compare the following models:

| Model | Description |
|---|---|
| Linear Regression | Interpretable baseline that models a linear relationship between input features and sales. |
| XGBoost Regressor | Gradient-boosted decision trees for capturing more complex relationships, when XGBoost is installed and the model trains successfully. |

Common evaluation metrics are:

- **RMSE (Root Mean Squared Error):** Penalizes larger prediction errors more strongly. Lower is generally better.
- **MAE (Mean Absolute Error):** Average absolute difference between predicted and actual sales. Lower is generally better.
- **R-squared:** Describes how much test-target variation is explained by the model under the metric's assumptions. Its interpretation depends on the evaluation data; it can be negative.

Use the values generated by the current execution of the application. Results depend on the dataset, feature engineering, chronological split, and model configuration. Do not assume that one model will always outperform the other.

## Running Tests

From the project root, run:

```powershell
py -m pytest tests/ -v
```

Review the output to confirm which tests passed or failed. Test counts can change as the project evolves; the README does not guarantee a particular result before the tests are executed.

## Known Limitations

- The included sample data is synthetic and does not represent an actual business.
- Forecast quality depends on data coverage, quality, and relevance.
- Recursive multi-step forecasting can accumulate errors across longer horizons.
- Forecasts may be point estimates without uncertainty intervals, depending on the implementation.
- Hyperparameter tuning may be limited or absent.
- Calendar features may not capture every weekly, holiday, or business-specific pattern.
- Training may sample large datasets to keep execution practical; check the application's configuration and logs.

## Troubleshooting

| Problem | Suggested fix |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Install dependencies with `pip install -r requirements.txt` in the project's Python environment. |
| XGBoost is unavailable | Install it with `pip install xgboost`, then verify it is listed in `requirements.txt`. |
| Browser shows an old or blank page | Refresh the browser; if needed, stop and restart Streamlit. |
| Port 8501 is already in use | Start Streamlit with `--server.port 8502`. |
| Not enough history for forecasting | Select a group with more history or provide more historical rows; lag features require sufficient prior observations. |
| CSV upload fails | Check encoding, headers, date parsing, sales values, and the selected column mappings. |
| Training is slow | Check whether the application supports sampling large datasets or reducing model complexity. |

## Suggested Project Presentation

A presentation may cover:

1. Problem statement and motivation.
2. Project objectives.
3. Dataset and its limitations.
4. Data preprocessing and validation.
5. Feature engineering.
6. Linear Regression methodology.
7. XGBoost methodology.
8. Evaluation metrics: RMSE, MAE, and R-squared.
9. Actual results from the running application.
10. Live dashboard demonstration.
11. Applications and limitations.
12. Conclusion and future improvements.
13. References.

Useful viva questions to prepare:

- What is RMSE, and why is it useful for forecasting?
- Why is a chronological train/test split appropriate for time-dependent data?
- What is a lag feature? How can it cause data leakage?
- How does XGBoost differ from a single decision tree?
- Why can recursive forecasts become less reliable at longer horizons?
- How could the project be improved with real business data?

## References

- [Scikit-learn Documentation](https://scikit-learn.org/stable/documentation.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python Documentation](https://plotly.com/python/)
- [Rossmann Store Sales Dataset](https://www.kaggle.com/competitions/rossmann-store-sales/data)
- [Store Item Demand Forecasting Dataset](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data)

---

*Built with Python, Streamlit, and machine learning for educational demonstration.*
