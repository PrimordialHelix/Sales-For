import pandas as pd
import pytest

from src.animated_analytics import prepare_animated_sales_data


def test_monthly_sales_aggregation_is_sorted_and_sums_rows():
    sales = pd.DataFrame(
        {
            "Date": ["2024-02-02", "2024-01-02", "2024-02-03"],
            "Sales": [3, 2, 4],
        }
    )

    result = prepare_animated_sales_data(sales, "Date", "Sales")

    assert result.to_dict("records") == [
        {"Month": "2024-01", "Sales": 2},
        {"Month": "2024-02", "Sales": 7},
    ]


def test_grouped_monthly_sales_limits_groups_and_combines_the_rest():
    sales = pd.DataFrame(
        {
            "Date": ["2024-01-01"] * 4 + ["2024-02-01"] * 4,
            "Sales": [10, 8, 2, 1, 5, 3, 2, 1],
            "Store": ["A", "B", "C", "D", "A", "B", "C", "D"],
        }
    )

    result = prepare_animated_sales_data(
        sales, "Date", "Sales", group_col="Store", max_groups=2
    )

    assert set(result["Group"]) == {"A", "B", "Other groups"}
    assert result.loc[
        (result["Month"] == "2024-01") & (result["Group"] == "Other groups"),
        "Sales",
    ].item() == 3


def test_invalid_columns_raise_a_clear_error():
    with pytest.raises(ValueError, match="Columns not found"):
        prepare_animated_sales_data(pd.DataFrame(), "Date", "Sales")
