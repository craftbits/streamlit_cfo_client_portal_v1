"""
Comparison page.

Allows users to compare actual results against budget or forecast for a
selected period range. The page aggregates amounts by PL group and
computes variances. Results are shown in a table and simple bar chart
to visualise differences.
"""
from __future__ import annotations

import streamlit as st

from data_access import aggregate_income_statement, list_periods
from layout import table_download_link


def render() -> None:
    st.title("Actual vs Budget/Forecast Comparison")
    st.write(
        "Select a date range and comparison scenario to see how your "
        "actual performance stacks up against plan."
    )
    periods = list_periods()
    start_period = st.selectbox("Start Period", periods, index=0)
    end_period = st.selectbox("End Period", periods, index=len(periods) - 1)
    start_idx = periods.index(start_period)
    end_idx = periods.index(end_period)
    selected_periods = periods[start_idx : end_idx + 1]
    comparison_scenario = st.selectbox("Comparison Scenario", ["Budget", "Forecast"], index=0)
    # Aggregate actual and comparison
    actual_df = aggregate_income_statement(scenario="Actual", periods=selected_periods, group_by="pl_group")
    comp_df = aggregate_income_statement(scenario=comparison_scenario, periods=selected_periods, group_by="pl_group")
    # Merge to align groups
    merged = actual_df.merge(comp_df, on="group_name", how="outer", suffixes=("_actual", f"_{comparison_scenario.lower()}"))
    merged.fillna(0, inplace=True)
    merged["variance"] = merged["amount_actual"] - merged[f"amount_{comparison_scenario.lower()}"]
    st.subheader("Variance Report")
    st.dataframe(merged)
    # Bar chart of variances
    st.bar_chart(merged.set_index("group_name")[["amount_actual", f"amount_{comparison_scenario.lower()}"]])
    # Download
    table_download_link(merged, f"comparison_{start_period}_to_{end_period}.csv")
