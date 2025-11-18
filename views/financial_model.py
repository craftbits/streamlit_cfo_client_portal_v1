"""
Financial Model page.

This page provides an interactive model to project the business's
performance over the next 36 months. Users can choose between
different strategic options (e.g. acquiring an existing business vs
building from scratch) and adjust high‑level assumptions such as
revenue growth, gross margin and operating expense ratio. The model
calculates revenue, cost of goods sold, operating expenses, profit
before interest and a simplified cash runway.

The intent is to give decision makers a tool to compare scenarios and
understand how different assumptions impact cash needs, burn rate and
time to profitability.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np

from data_access import load_model_assumptions
from layout import build_metric_row, table_download_link


def render() -> None:
    st.title("Financial Model & Scenario Planning")
    st.write(
        "Model your future performance with adjustable assumptions. Select a "
        "scenario and tweak the inputs to see how revenue growth, gross margin "
        "and operating expenses influence your cash runway and profitability."
    )
    # Scenario options
    scenario_option = st.selectbox(
        "Select Scenario",
        ["Acquire Existing Business", "Start from Scratch"],
    )
    # Load baseline assumptions
    assumptions_df = load_model_assumptions()
    base_growth = assumptions_df.loc[assumptions_df["assumption_key"] == "revenue_growth_rate_yoy", "base_value"].values[0]
    base_margin = assumptions_df.loc[assumptions_df["assumption_key"] == "gross_margin_target", "base_value"].values[0]
    base_opex = assumptions_df.loc[assumptions_df["assumption_key"] == "opex_as_percent_revenue", "base_value"].values[0]
    cash_safety_months = assumptions_df.loc[assumptions_df["assumption_key"] == "cash_safety_months", "base_value"].values[0]
    # User adjustable inputs
    st.subheader("Assumptions")
    revenue_growth = st.slider("Annual Revenue Growth Rate (%)", min_value=0.0, max_value=0.50, value=float(base_growth), step=0.01)
    gross_margin = st.slider("Gross Margin (%)", min_value=0.0, max_value=1.0, value=float(base_margin), step=0.01)
    opex_ratio = st.slider("Operating Expenses (% of revenue)", min_value=0.1, max_value=0.7, value=float(base_opex), step=0.01)
    initial_cash = st.number_input("Initial Cash on Hand", value=200000.0, min_value=0.0, step=10000.0)
    # Starting revenue depends on scenario
    if scenario_option == "Acquire Existing Business":
        start_revenue = st.number_input("Initial Monthly Revenue (Acquire)", value=80000.0, step=5000.0)
    else:
        start_revenue = st.number_input("Initial Monthly Revenue (Start-up)", value=30000.0, step=5000.0)
    projection_months = 36
    monthly_growth = (1 + revenue_growth) ** (1 / 12) - 1
    # Create projection DataFrame
    months = pd.date_range(start=pd.to_datetime("2026-01-01"), periods=projection_months, freq="MS")
    df = pd.DataFrame({"month": months})
    df["Revenue"] = start_revenue * (1 + monthly_growth) ** np.arange(projection_months)
    df["COGS"] = -df["Revenue"] * (1 - gross_margin)
    df["Operating Expenses"] = -df["Revenue"] * opex_ratio
    df["EBITDA"] = df["Revenue"] + df["COGS"] + df["Operating Expenses"]
    # Assume no additional financing or capex for simplicity
    df["Net Cash Flow"] = df["EBITDA"]
    # Cumulative cash
    df["Cumulative Cash"] = initial_cash + df["Net Cash Flow"].cumsum()
    # Determine when cash balance turns negative
    negative_months = df[df["Cumulative Cash"] < 0]
    if not negative_months.empty:
        runway_end = negative_months.iloc[0]["month"]
        months_remaining = (runway_end - df.iloc[0]["month"]) / np.timedelta64(1, "M")
    else:
        runway_end = None
        months_remaining = None
    # Display metrics
    st.subheader("Key Outputs")
    last_cash = df.iloc[-1]["Cumulative Cash"]
    metrics = {
        "Final Cash Balance": last_cash,
        "Minimum Cash Balance": df["Cumulative Cash"].min(),
        "Months Until Cash Runs Out": months_remaining if months_remaining is not None else projection_months,
    }
    build_metric_row(metrics.items(), columns=3)
    # Show table and chart
    st.subheader("Projection Table")
    display_df = df.copy()
    display_df["month"] = display_df["month"].dt.strftime("%Y-%m")
    st.dataframe(display_df[["month", "Revenue", "COGS", "Operating Expenses", "EBITDA", "Net Cash Flow", "Cumulative Cash"]])
    st.subheader("Cumulative Cash Chart")
    st.line_chart(display_df.set_index("month")["Cumulative Cash"])
    # Download
    table_download_link(display_df, f"financial_model_{scenario_option.replace(' ', '_').lower()}.csv")
