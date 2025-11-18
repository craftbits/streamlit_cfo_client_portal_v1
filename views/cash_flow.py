"""
Cash Flow page.

Displays the cash position and flows over time. Users can select a
range of periods and a scenario to view opening balance, net cash from
operating, investing and financing activities, and closing balance. A
chart visualises the cash movement. A simplified 13‑week outlook is
also provided by extrapolating from monthly data.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from data_access import load_cashflow_items, list_periods
from config import available_scenarios
from layout import build_metric_row, table_download_link


def render() -> None:
    st.title("Cash Flow")
    st.write(
        "Review your cash inflows and outflows. This page summarises cash "
        "activity by category and projects a simplified near‑term outlook."
    )
    periods = list_periods()
    start_period = st.selectbox("Start Period", periods, index=0)
    end_period = st.selectbox("End Period", periods, index=len(periods) - 1)
    start_idx = periods.index(start_period)
    end_idx = periods.index(end_period)
    selected_periods = periods[start_idx : end_idx + 1]
    scenario = st.selectbox("Scenario", available_scenarios(), index=0)
    cf = load_cashflow_items()
    cf = cf[cf["scenario"].str.casefold() == scenario.casefold()]
    cf = cf[cf["period"].isin(selected_periods)]
    # Compute summary by period
    summary = (
        cf.groupby(["period", "item_type"]).agg(total=("amount", "sum")).reset_index()
    )
    # Pivot to wide format
    pivot = summary.pivot(index="period", columns="item_type", values="total").fillna(0)
    # Compute net cash flows and closing balance
    pivot["Net Cash Flow"] = (
        pivot.get("Operating", 0)
        + pivot.get("Investing", 0)
        + pivot.get("Financing", 0)
        + pivot.get("Owner Draw", 0)
    )
    # Opening cash is recorded separately; compute closing by cumulative sum
    pivot["Opening Cash"] = pivot.get("Opening Cash", 0)
    pivot["Closing Cash"] = pivot["Opening Cash"] + pivot["Net Cash Flow"].cumsum()
    pivot = pivot.reset_index()
    st.subheader("Cash Flow Summary")
    st.dataframe(pivot)
    # Display metrics for last selected period
    last_row = pivot.loc[pivot["period"] == selected_periods[-1]].iloc[0]
    metrics = {
        "Opening Cash": last_row.get("Opening Cash", 0),
        "Net Cash Flow": last_row.get("Net Cash Flow", 0),
        "Closing Cash": last_row.get("Closing Cash", 0),
    }
    build_metric_row(metrics.items(), columns=3)
    # Chart cash position
    st.line_chart(pivot.set_index("period")[["Opening Cash", "Closing Cash"]])
    # Simplified 13‑week projection: take monthly net cash / 4 to estimate weekly
    st.subheader("Simplified 13‑Week Outlook")
    if len(pivot) > 0:
        monthly_net = pivot["Net Cash Flow"].iloc[-1]
        weekly_net = monthly_net / 4.0
        weeks = [f"Week {i+1}" for i in range(13)]
        cumulative = [metrics["Closing Cash"] + weekly_net * (i + 1) for i in range(13)]
        outlook_df = pd.DataFrame({"Week": weeks, "Projected Cash": cumulative})
        st.line_chart(outlook_df.set_index("Week"))
        st.dataframe(outlook_df)
    table_download_link(pivot, f"cashflow_{start_period}_to_{end_period}.csv")
