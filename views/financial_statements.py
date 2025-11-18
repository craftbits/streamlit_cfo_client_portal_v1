"""
Financial Statements page.

Users can view an income statement (profit & loss) aggregated over a
selected range of periods and scenario. The report can be printed or
exported as CSV. Future versions may include balance sheet and cash
flow statements as well.
"""
from __future__ import annotations

import streamlit as st

from data_access import aggregate_income_statement, list_periods
from config import available_scenarios
from layout import table_download_link


def render() -> None:
    st.title("Financial Statements")
    st.write(
        "Generate and review your income statement over a custom date "
        "range. Select the periods and scenario below to update the report."
    )
    # Period selection (multi select for from and to)
    periods = list_periods()
    period_options = [p for p in periods]
    # Use date range selection via two selectboxes
    start_period = st.selectbox("Start Period", period_options, index=0)
    end_period = st.selectbox("End Period", period_options, index=len(period_options) - 1)
    # Determine selected slice
    start_idx = period_options.index(start_period)
    end_idx = period_options.index(end_period)
    selected_periods = period_options[start_idx : end_idx + 1]
    scenario = st.selectbox("Scenario", available_scenarios(), index=0)
    # Grouping options: show by pl_group or account_number
    group_by = st.selectbox("Group By", options=["pl_group", "analysis_group", "account_number"], index=0)
    # Generate income statement
    statement = aggregate_income_statement(scenario=scenario, periods=selected_periods, group_by=group_by)
    # Display table
    st.subheader("Income Statement")
    st.dataframe(statement)
    # Chart representation of revenue and expenses (if group_by is pl_group or analysis_group)
    if group_by != "account_number":
        st.bar_chart(statement.set_index("group_name"))
    # Download button
    st.markdown("### Export")
    table_download_link(statement, f"income_statement_{scenario}_{start_period}_to_{end_period}.csv")
    st.caption("Report grouping based on selected grouping key. Amounts are aggregated sums across the selected periods.")
