"""
Financial Model page.

This version mirrors the executive portal layout and adds richer modeling tools:
* stress-tested assumptions
* adjustable projection horizon, capex, and financing inputs
* runway and safety-buffer diagnostics
* comparison scenarios with exportable data
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from data_access import load_model_assumptions
from layout import format_currency, metric_card, page_header, table_download_link


STRESS_CASES = {
    "Base": {"growth": 1.0, "margin": 1.0, "opex": 1.0, "label": "Balanced outlook"},
    "Upside": {"growth": 1.2, "margin": 1.05, "opex": 0.92, "label": "Optimistic demand"},
    "Downside": {"growth": 0.7, "margin": 0.9, "opex": 1.12, "label": "Conservative stress"},
}


@dataclass
class ScenarioInputs:
    label: str
    scenario_type: str
    stress_case: str
    start_revenue: float
    initial_cash: float
    revenue_growth: float
    gross_margin: float
    opex_ratio: float
    capex_ratio: float
    owner_draw: float
    financing_injection: float


def collect_scenario_inputs(title: str, key_prefix: str, defaults: dict) -> ScenarioInputs:
    st.markdown(f"#### {title}")
    scenario_type = st.selectbox(
        "Business approach",
        ["Acquire Existing Business", "Start from Scratch"],
        key=f"{key_prefix}_scenario",
    )
    stress_case = st.radio(
        "Stress case",
        list(STRESS_CASES.keys()),
        horizontal=True,
        key=f"{key_prefix}_stress",
        help="Quickly apply optimistic or conservative adjustments to the inputs below.",
    )

    default_start = 80000.0 if scenario_type == "Acquire Existing Business" else 30000.0
    col_a, col_b = st.columns(2)
    with col_a:
        start_revenue = st.number_input(
            "Initial Monthly Revenue",
            min_value=10000.0,
            value=default_start,
            step=5000.0,
            key=f"{key_prefix}_start_rev",
        )
        initial_cash = st.number_input(
            "Initial Cash on Hand",
            min_value=0.0,
            value=200000.0,
            step=25000.0,
            key=f"{key_prefix}_cash",
        )
        owner_draw = st.number_input(
            "Monthly Owner Draw",
            min_value=0.0,
            value=float(defaults["owner_draw"]),
            step=1000.0,
            key=f"{key_prefix}_owner_draw",
        )
    with col_b:
        financing_injection = st.number_input(
            "Upfront Financing Injection",
            min_value=0.0,
            value=0.0,
            step=25000.0,
            key=f"{key_prefix}_financing",
            help="Optional one-time capital added at the start of the projection.",
        )

    slider_col1, slider_col2 = st.columns(2)
    with slider_col1:
        revenue_growth = st.slider(
            "Annual Revenue Growth Rate",
            min_value=0.0,
            max_value=0.8,
            value=float(defaults["growth"]),
            step=0.01,
            key=f"{key_prefix}_growth",
        )
        gross_margin = st.slider(
            "Gross Margin",
            min_value=0.1,
            max_value=0.9,
            value=float(defaults["margin"]),
            step=0.01,
            key=f"{key_prefix}_margin",
        )
    with slider_col2:
        opex_ratio = st.slider(
            "Operating Expenses (% of revenue)",
            min_value=0.1,
            max_value=0.9,
            value=float(defaults["opex"]),
            step=0.01,
            key=f"{key_prefix}_opex",
        )
        capex_ratio = st.slider(
            "Capex (% of revenue)",
            min_value=0.0,
            max_value=0.2,
            value=float(defaults["capex"]),
            step=0.005,
            key=f"{key_prefix}_capex",
        )

    label = f"{scenario_type} ({stress_case})"
    return ScenarioInputs(
        label=label,
        scenario_type=scenario_type,
        stress_case=stress_case,
        start_revenue=start_revenue,
        initial_cash=initial_cash,
        revenue_growth=revenue_growth,
        gross_margin=gross_margin,
        opex_ratio=opex_ratio,
        capex_ratio=capex_ratio,
        owner_draw=owner_draw,
        financing_injection=financing_injection,
    )


def format_metric_value(value: float | None, kind: str) -> str:
    if kind == "currency":
        return format_currency(value or 0.0, precision=0)
    if kind == "months":
        if value is None:
            return "—"
        return "∞" if math.isinf(value) else f"{value:.1f} mo"
    if kind == "months-with-na":
        if value is None:
            return "Not reached"
        return f"{value:.1f} mo"
    return f"{value:.2f}"


def run_projection(
    inputs: ScenarioInputs,
    projection_months: int,
    cash_safety_months: float,
) -> dict:
    preset = STRESS_CASES[inputs.stress_case]
    growth = min(inputs.revenue_growth * preset["growth"], 0.9)
    gross_margin = max(min(inputs.gross_margin * preset["margin"], 0.95), 0.05)
    opex_ratio = max(min(inputs.opex_ratio * preset["opex"], 0.95), 0.05)

    months = pd.date_range(
        start=pd.to_datetime("2026-01-01"),
        periods=projection_months,
        freq="MS",
    )
    df = pd.DataFrame({"month": months})
    monthly_growth = (1 + growth) ** (1 / 12) - 1
    df["Revenue"] = inputs.start_revenue * (1 + monthly_growth) ** np.arange(projection_months)
    df["COGS"] = -df["Revenue"] * (1 - gross_margin)
    df["Operating Expenses"] = -df["Revenue"] * opex_ratio
    df["Capex"] = -df["Revenue"] * inputs.capex_ratio
    df["Owner Draw"] = -inputs.owner_draw
    df["Financing"] = 0.0
    df.loc[df.index[0], "Financing"] = inputs.financing_injection
    df["EBITDA"] = df["Revenue"] + df["COGS"] + df["Operating Expenses"]
    df["Net Cash Flow"] = df["EBITDA"] + df["Capex"] + df["Owner Draw"] + df["Financing"]
    df["Cumulative Cash"] = inputs.initial_cash + df["Net Cash Flow"].cumsum()
    df["EBITDA Delta"] = df["EBITDA"].diff().fillna(0.0)
    df["Scenario"] = inputs.label

    min_cash = df["Cumulative Cash"].min()
    final_cash = df["Cumulative Cash"].iloc[-1]
    annual_recurring_revenue = df["Revenue"].iloc[-1] * 12
    avg_monthly_burn = df["Net Cash Flow"].mean()

    below_zero = df[df["Cumulative Cash"] < 0]
    if below_zero.empty:
        runway_months = float("inf")
        runway_label = "Beyond projection horizon"
        buffer_months = float("inf")
    else:
        runway_index = below_zero.index[0] + 1
        runway_months = float(runway_index)
        runway_label = below_zero.iloc[0]["month"].strftime("%Y-%m")
        buffer_months = runway_months - cash_safety_months

    payback_df = df[df["Cumulative Cash"] >= inputs.initial_cash]
    payback_months = None
    if not payback_df.empty:
        payback_months = float(payback_df.index[0] + 1)

    cash_shortfall = abs(min_cash) if min_cash < 0 else 0.0
    safety_buffer = buffer_months if not math.isinf(buffer_months) else float("inf")

    metrics = [
        ("Final Cash Balance", final_cash, "currency", "End of horizon"),
        ("Minimum Cash", min_cash, "currency", "Lowest point"),
        ("Annual Recurring Revenue", annual_recurring_revenue, "currency", "Year-end ARR"),
        ("Avg Monthly Burn", avg_monthly_burn, "currency", "/month"),
        ("Runway", runway_months, "months", f"Runs dry: {runway_label}"),
        ("Safety Buffer", safety_buffer, "months", f"Target: {cash_safety_months:.1f} mo"),
        ("Payback Period", payback_months, "months-with-na", "When cumulative cash exceeds starting cash"),
    ]

    warning_msg = ""
    if cash_shortfall > 0:
        warning_msg = (
            f"Runway falls short of the {cash_safety_months:.1f}-month target. "
            f"Raise or save approximately {format_currency(cash_shortfall, precision=0)} "
            f"to stay above zero cash."
        )

    return {
        "data": df,
        "metrics": metrics,
        "scenario_label": inputs.label,
        "warning": warning_msg,
        "cash_shortfall": cash_shortfall,
        "runway_months": runway_months,
    }


def display_metrics(result: dict, title: str) -> None:
    st.markdown(f"### {title}")
    cols = st.columns(3)
    for idx, (label, value, kind, note) in enumerate(result["metrics"]):
        with cols[idx % 3]:
            metric_card(label, format_metric_value(value, kind), note)

    if result["warning"]:
        st.warning(result["warning"])


def scenario_export_dataframe(results: list[pd.DataFrame]) -> pd.DataFrame:
    export_df = pd.concat(results, ignore_index=True)
    export_df["month"] = export_df["month"].dt.strftime("%Y-%m")
    return export_df


def render() -> None:
    assumptions_df = load_model_assumptions().set_index("assumption_key")
    defaults = {
        "growth": float(assumptions_df.loc["revenue_growth_rate_yoy", "base_value"]),
        "margin": float(assumptions_df.loc["gross_margin_target", "base_value"]),
        "opex": float(assumptions_df.loc["opex_as_percent_revenue", "base_value"]),
        "capex": float(assumptions_df.loc["capex_as_percent_revenue", "base_value"]),
        "owner_draw": float(assumptions_df.loc["owner_draw_monthly", "base_value"]),
    }
    cash_safety_months = float(assumptions_df.loc["cash_safety_months", "base_value"])

    page_header(
        "Financial Model & Scenario Planning",
        "Model cash runway and profitability with adjustable assumptions, stress cases, "
        "and optional scenario comparisons.",
        icon="📈",
    )
    st.caption("Baseline assumptions pulled from `data/model_assumptions.csv`. Adjust and compare scenarios below.")

    projection_months = st.slider(
        "Projection Horizon (months)",
        min_value=12,
        max_value=60,
        step=6,
        value=36,
    )

    primary_inputs = collect_scenario_inputs("Primary Scenario", "primary", defaults)
    primary_result = run_projection(primary_inputs, projection_months, cash_safety_months)

    comparison_result = None
    with st.expander("Add Comparison Scenario", expanded=False):
        enable_comparison = st.checkbox("Enable comparison scenario", value=False)
        if enable_comparison:
            comparison_inputs = collect_scenario_inputs("Comparison Scenario", "comparison", defaults)
            comparison_result = run_projection(comparison_inputs, projection_months, cash_safety_months)

    display_metrics(primary_result, primary_inputs.label)
    if comparison_result:
        display_metrics(comparison_result, comparison_result["scenario_label"])

    st.subheader("Cash Runway")
    cash_dfs = [primary_result["data"][["month", "Cumulative Cash", "Scenario"]]]
    if comparison_result:
        cash_dfs.append(comparison_result["data"][["month", "Cumulative Cash", "Scenario"]])
    cash_chart_df = pd.concat(cash_dfs, ignore_index=True)
    cash_chart = (
        alt.Chart(cash_chart_df)
        .mark_line(interpolate="monotone", strokeWidth=3)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("Cumulative Cash:Q", title="Cumulative Cash"),
            color=alt.Color("Scenario:N", title="Scenario"),
        )
    )
    st.altair_chart(cash_chart, use_container_width=True)

    st.subheader("Revenue & Cost Mix")
    comp_df = primary_result["data"][["month", "Revenue", "COGS", "Operating Expenses", "Capex", "Owner Draw"]].copy()
    comp_long = comp_df.melt("month", var_name="Component", value_name="Amount")
    area_chart = (
        alt.Chart(comp_long)
        .mark_area(opacity=0.6)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("Amount:Q", title="Monthly Amount"),
            color=alt.Color("Component:N", title="Component"),
        )
    )
    st.altair_chart(area_chart, use_container_width=True)

    st.subheader("Projection Table")
    display_df = primary_result["data"].copy()
    display_df["month"] = display_df["month"].dt.strftime("%Y-%m")
    table_cols = [
        "month",
        "Revenue",
        "COGS",
        "Operating Expenses",
        "Capex",
        "Owner Draw",
        "Financing",
        "EBITDA",
        "EBITDA Delta",
        "Net Cash Flow",
        "Cumulative Cash",
    ]
    st.dataframe(
        display_df[table_cols],
        use_container_width=True,
        height=420,
    )

    st.subheader("Download Scenarios")
    export_frames = [primary_result["data"]]
    if comparison_result:
        export_frames.append(comparison_result["data"])
    export_df = scenario_export_dataframe(export_frames)
    table_download_link(export_df, "financial_model_scenarios.csv")
