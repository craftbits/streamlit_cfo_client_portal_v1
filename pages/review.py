"""
Review page.

This view allows users to focus on particular reporting groups from the
chart of accounts, such as controllable vs non‑controllable expenses or
other high‑level groupings defined in the ``analysis_group`` field.
Users can select a group and see the aggregated amounts for the
selected periods and scenario.
"""
from __future__ import annotations

import streamlit as st

from data_access import aggregate_income_statement, list_periods
from config import available_scenarios
from layout import table_download_link


def render() -> None:
    st.title("Review by Reporting Group")
    st.write(
        "Select a reporting group (analysis_group) to review its "
        "performance over time. This allows you to compare different "
        "cost classifications or other groupings of accounts."
    )
    periods = list_periods()
    start_period = st.selectbox("Start Period", periods, index=0)
    end_period = st.selectbox("End Period", periods, index=len(periods) - 1)
    start_idx = periods.index(start_period)
    end_idx = periods.index(end_period)
    selected_periods = periods[start_idx : end_idx + 1]
    scenario = st.selectbox("Scenario", available_scenarios(), index=0)
    # Choose grouping field: analysis_group or pl_group
    group_by = st.selectbox("Reporting Group", ["analysis_group", "pl_group"], index=0)
    statement = aggregate_income_statement(scenario=scenario, periods=selected_periods, group_by=group_by)
    st.subheader("Summary by Group")
    st.dataframe(statement)
    st.bar_chart(statement.set_index("group_name"))
    table_download_link(statement, f"review_{group_by}_{scenario}_{start_period}_to_{end_period}.csv")
