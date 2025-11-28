from typing import Dict, Any

import numpy as np
import pandas as pd


def _filter_by_intent(df: pd.DataFrame, intent: Dict[str, Any]) -> pd.DataFrame:
    filtered = df.copy()

    areas = intent.get("areas") or []
    if areas:
        filtered = filtered[filtered["Area"].isin(areas)]

    years = intent.get("years") or []
    last_n = intent.get("last_n_years") or 0

    if years:
        filtered = filtered[filtered["Year"].isin(years)]

    if last_n and not years:
        max_year = filtered["Year"].max()
        min_year = max_year - last_n + 1
        filtered = filtered[(filtered["Year"] >= min_year) & (filtered["Year"] <= max_year)]

    return filtered


def _trend_direction(values):
    values = list(values)
    if len(values) < 2:
        return "flat"
    if values[-1] > values[0] * 1.03:
        return "up"
    if values[-1] < values[0] * 0.97:
        return "down"
    return "flat"


def _compute_growth_pct(first: float, last: float) -> float:
    if first <= 0:
        return 0.0
    return (last - first) / first * 100.0


def analyze_intent(df: pd.DataFrame, intent: Dict[str, Any]) -> Dict[str, Any]:
    filtered = _filter_by_intent(df, intent)

    if filtered.empty:
        return {
            "filtered_df": filtered,
            "charts": [],
            "table": {"columns": [], "rows": []},
            "insights": {
                "areas": intent.get("areas", []),
                "years": [],
                "price_trend_direction": {},
                "demand_trend_direction": {},
                "price_growth_pct": {},
            },
        }

    areas = sorted(filtered["Area"].unique().tolist())
    years = sorted(filtered["Year"].dropna().unique().tolist())

    group = (
        filtered.groupby(["Area", "Year"])
        .agg({"Price": "mean", "Demand": "mean"})
        .reset_index()
        .sort_values(["Area", "Year"])
    )

    price_trend_direction = {}
    demand_trend_direction = {}
    price_growth_pct = {}

    price_chart_series = []
    demand_chart_series = []

    for area in areas:
        area_data = group[group["Area"] == area].sort_values("Year")
        prices = area_data["Price"].tolist()
        demands = area_data["Demand"].tolist()
        yrs = area_data["Year"].tolist()

        if not yrs:
            continue

        price_trend_direction[area] = _trend_direction(prices)
        demand_trend_direction[area] = _trend_direction(demands)

        if len(prices) >= 2:
            price_growth_pct[area] = _compute_growth_pct(prices[0], prices[-1])
        else:
            price_growth_pct[area] = 0.0

        price_chart_series.append(
            {
                "name": area,
                "data": [
                    {"Year": int(y), "Price": float(p)} for y, p in zip(yrs, prices)
                ],
            }
        )

        demand_chart_series.append(
            {
                "name": area,
                "data": [
                    {"Year": int(y), "Demand": float(d)} for y, d in zip(yrs, demands)
                ],
            }
        )

    charts = [
        {
            "id": "price_trend",
            "title": "Price Trend by Year",
            "type": "line",
            "xKey": "Year",
            "yKeys": ["Price"],
            "series": price_chart_series,
        },
        {
            "id": "demand_trend",
            "title": "Demand Trend by Year",
            "type": "line",
            "xKey": "Year",
            "yKeys": ["Demand"],
            "series": demand_chart_series,
        },
    ]

    table_columns = ["Year", "Area", "Price", "Demand", "Size"]
    table_rows = []

    filtered_sorted = filtered.sort_values(["Area", "Year"])

    for _, row in filtered_sorted.iterrows():
        table_rows.append(
            {
                "Year": int(row["Year"]),
                "Area": str(row["Area"]),
                "Price": float(row["Price"]) if not np.isnan(row["Price"]) else None,
                "Demand": float(row["Demand"]) if not np.isnan(row["Demand"]) else None,
                "Size": float(row["Size"]) if not np.isnan(row["Size"]) else None,
            }
        )

    insights = {
        "areas": areas,
        "years": years,
        "price_trend_direction": price_trend_direction,
        "demand_trend_direction": demand_trend_direction,
        "price_growth_pct": price_growth_pct,
    }

    return {
        "filtered_df": filtered_sorted,
        "charts": charts,
        "table": {"columns": table_columns, "rows": table_rows},
        "insights": insights,
    }
