"""
model_training.py
-----------------
Trains Linear Regression and XGBoost Regressor on a prepared feature
matrix and evaluates with RMSE and MAE.

Public API
----------
train_linear_regression(X_train, y_train)  → fitted pipeline
train_xgboost(X_train, y_train)            → fitted pipeline (or None + msg)
evaluate_model(model, X_test, y_test)      → {"rmse": ..., "mae": ...}
save_model(model, path)                    → None
load_model(path)                           → model
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


# ── Linear Regression ─────────────────────────────────────────────────────────

def train_linear_regression(X_train, y_train) -> Pipeline:
    """
    Returns a fitted sklearn Pipeline:
        SimpleImputer (median) → StandardScaler → LinearRegression

    Imputation guards against rare NaNs that slip through feature engineering.
    Scaling is important for linear regression stability.
    """
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("model",   LinearRegression()),
    ])
    pipe.fit(X_train, y_train)
    return pipe


# ── XGBoost ───────────────────────────────────────────────────────────────────

def train_xgboost(
    X_train, y_train,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    colsample_bytree: float = 0.8,
    random_state: int = 42,
) -> Tuple[Optional[Pipeline], Optional[str]]:
    """
    Returns (fitted_pipeline, None) on success.
    Returns (None, error_message) if XGBoost is not installed.
    """
    try:
        from xgboost import XGBRegressor
    except ImportError:
        return None, (
            "XGBoost is not installed. Run:  pip install xgboost  "
            "and restart the application."
        )

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            n_jobs=-1,
            verbosity=0,
        )),
    ])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe.fit(X_train, y_train)
    return pipe, None


# ── Evaluation ────────────────────────────────────────────────────────────────

def evaluate_model(model, X_test, y_test) -> Dict[str, float]:
    """
    Compute RMSE and MAE for a fitted model.

    Returns {"rmse": float, "mae": float}.
    """
    preds = model.predict(X_test)
    preds = np.clip(preds, 0, None)          # sales cannot be negative
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mae  = float(mean_absolute_error(y_test, preds))
    return {"rmse": rmse, "mae": mae}


def get_predictions(model, X_test) -> np.ndarray:
    """Return clipped non-negative predictions."""
    preds = model.predict(X_test)
    return np.clip(preds, 0, None)


# ── Persistence ───────────────────────────────────────────────────────────────

def save_model(model, path: str | Path) -> None:
    """Serialise a fitted model to disk with joblib."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: str | Path):
    """Load a joblib-serialised model from disk."""
    return joblib.load(path)


# ── Feature importance helper ─────────────────────────────────────────────────

def get_feature_importance(model, feature_names) -> Optional[dict]:
    """
    Extract feature importances from XGBoost or LinearRegression coefficients.
    Returns {feature_name: importance} or None if not available.
    """
    try:
        # XGBoost pipeline: last step is the XGBRegressor
        estimator = model.named_steps.get("model")
        if estimator is None:
            return None

        if hasattr(estimator, "feature_importances_"):
            imps = estimator.feature_importances_
            return dict(zip(feature_names, imps))
        elif hasattr(estimator, "coef_"):
            coefs = np.abs(estimator.coef_)
            return dict(zip(feature_names, coefs))
    except Exception:
        pass
    return None
