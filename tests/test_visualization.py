"""Tests for the interactive dashboard chart factories."""

import pandas as pd

from src.visualization import FORECAST_COLOR, plot_forecast


def test_forecast_chart_separates_history_and_forecast():
    history = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=3, freq="D"),
        "Sales": [10, 12, 11],
    })
    forecast = pd.DataFrame({
        "Date": pd.date_range("2024-01-04", periods=2, freq="D"),
        "Predicted_Sales": [13, 14],
    })

    figure = plot_forecast(history, forecast, "Date", "Sales")

    assert figure.data[0].name == "Historical Sales"
    assert figure.data[0].line.color == "#2DD4BF"
    assert figure.data[0].line.dash in (None, "solid")
    assert figure.data[1].name == "Forecast"
    assert figure.data[1].line.color == FORECAST_COLOR
    assert figure.data[1].line.dash == "dash"
    assert "Forecast sales" in figure.data[1].hovertemplate
    assert len(figure.layout.shapes) == 2
    assert figure.layout.shapes[0].line.dash == "dot"
