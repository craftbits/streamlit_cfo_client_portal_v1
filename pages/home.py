"""
Home page of the CFO portal.

This page provides a high level overview of the business with key
financial metrics and trends. Users can select a period and scenario
to view the critical KPIs for that period. A small table of recent
transactions and charts helps set the context.
"""
from __future__ import annotations

import streamlit as st

from data_access import compute_key_metrics, list_periods, load_gl_transactions
from config import available_scenarios
from layout import build_metric_row


def render() -> None:
    st.title("Home Dashboard")
    st.write(
        "Welcome to the Supermarket CFO portal. This dashboard provides "
        "a snapshot of your financial health. Select a period and scenario "
        "below to explore the numbers."
    )
    # Sidebar selections but accessible here as well
    periods = list_periods()
    default_period = periods[-1] if periods else None
    period = st.selectbox("Select Period (YYYY-MM)", periods, index=len(periods) - 1)
    scenarios = available_scenarios()
    scenario = st.selectbox("Select Scenario", scenarios, index=scenarios.index("Actual"))
    # Compute metrics for selected period
    metrics = compute_key_metrics(period, scenario)
    # Display metrics in a row
    build_metric_row(metrics.items())
    # Trend chart for revenue and net profit across all periods
    st.subheader("Trends")
    txn_df = load_gl_transactions()
    # Filter for selected scenario
    txn_df = txn_df[txn_df["scenario"].str.casefold() == scenario.casefold()]
    # Summaries by period
    period_summary = (
        txn_df.groupby(["period"]).agg(total_revenue=("amount", lambda x: x[x > 0].sum()),
                                         net_profit=("amount", "sum"))
    ).reset_index()
    period_summary.sort_values("period", inplace=True)
    # Plot line chart
    chart_data = period_summary.set_index("period")
    st.line_chart(chart_data)
    # Show recent transactions for context
    st.subheader("Recent Transactions")
    recent_txns = txn_df.sort_values("txn_date", ascending=False).head(10)
    st.dataframe(recent_txns[["txn_date", "account_number", "description", "amount"]])
