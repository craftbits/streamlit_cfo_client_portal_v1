"""
Ratio Analysis page.

Calculate and visualise important financial ratios over time. Users
select a date range and scenario, then the page computes metrics
including gross margin, net margin, current ratio, quick ratio and
debt‑to‑equity. A table summarises ratios by period and a line
chart illustrates their trends.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from data_access import list_periods, compute_ratios, list_ratio_metrics
from config import available_scenarios
from layout import table_download_link


def render() -> None:
    st.title("Ratio Analysis")
    st.write(
        "Review key financial ratios to gauge the health of the business. "
        "Select a period range and scenario to compute the ratios."
    )
    periods = list_periods()
    start_period = st.selectbox("Start Period", periods, index=0)
    end_period = st.selectbox("End Period", periods, index=len(periods) - 1)
    start_idx = periods.index(start_period)
    end_idx = periods.index(end_period)
    selected_periods = periods[start_idx : end_idx + 1]
    scenario = st.selectbox("Scenario", available_scenarios(), index=0)
    ratio_defs = list_ratio_metrics()
    # Compute ratios for each period
    ratio_rows = []
    for period in selected_periods:
        ratios = compute_ratios(period, scenario)
        row = {"period": period}
        for name, key in ratio_defs.items():
            row[name] = ratios.get(key, 0)
        ratio_rows.append(row)
    ratio_df = pd.DataFrame(ratio_rows)
    st.subheader("Ratios Table")
    st.dataframe(ratio_df)
    # Chart: user selects ratio to plot
    selected_ratio_name = st.selectbox("Select Ratio to Plot", list(ratio_defs.keys()), index=0)
    st.line_chart(ratio_df.set_index("period")[[selected_ratio_name]])
    table_download_link(ratio_df, f"ratios_{start_period}_to_{end_period}.csv")
