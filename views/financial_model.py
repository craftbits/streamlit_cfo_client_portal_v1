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
from datetime import date

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from data_access import get_model_assumptions, load_model_assumptions
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
    initial_cash: float
    revenue_growth: float
    gross_margin: float
    opex_ratio: float
    capex_ratio: float
    owner_draw: float
    equity_injection: float
    construction_start: date
    construction_duration_months: int
    family_basket_value: float
    families_per_month: float
    loan_amount: float
    loan_rate: float
    loan_term_years: int


SCENARIO_OPTIONS = ["Acquire Existing Business", "Start from Scratch"]


def collect_scenario_inputs(
    title: str,
    key_prefix: str,
    defaults: dict,
    model_start_date: date,
    default_scenario_type: str,
    register_defaults: dict[str, float] | None = None,
) -> ScenarioInputs:
    st.markdown(f"#### {title}")
    scenario_index = (
        SCENARIO_OPTIONS.index(default_scenario_type)
        if default_scenario_type in SCENARIO_OPTIONS
        else 0
    )
    scenario_type = st.selectbox(
        "Business approach",
        SCENARIO_OPTIONS,
        index=scenario_index,
        key=f"{key_prefix}_scenario",
    )
    stress_case = st.radio(
        "Stress case",
        list(STRESS_CASES.keys()),
        horizontal=True,
        key=f"{key_prefix}_stress",
        help="Quickly apply optimistic or conservative adjustments to the inputs below.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        construction_start = st.date_input(
            "Construction Start",
            value=model_start_date,
            key=f"{key_prefix}_construction_start",
        )
        construction_duration = st.number_input(
            "Construction Duration (months)",
            min_value=1,
            max_value=48,
            value=12 if scenario_type == "Start from Scratch" else 6,
            key=f"{key_prefix}_construction_duration",
        )
        initial_cash = st.number_input(
            "Initial Cash on Hand",
            min_value=0.0,
            value=200000.0,
            step=25000.0,
            key=f"{key_prefix}_cash",
        )
    register_defaults = register_defaults or {}
    with col_b:
        basket_default = register_defaults.get("family_basket_value", 450.0)
        family_basket_value = st.number_input(
            "Family Basket Value (monthly)",
            min_value=100.0,
            value=float(basket_default),
            step=25.0,
            key=f"{key_prefix}_basket",
        )
        families_default = register_defaults.get("families_per_month")
        if not families_default or families_default <= 0:
            families_default = 250.0 if scenario_type == "Acquire Existing Business" else 120.0
        families_per_month = st.number_input(
            "New Families Added per Month",
            min_value=10.0,
            value=float(families_default),
            step=10.0,
            key=f"{key_prefix}_families",
        )

    owner_draw = st.number_input(
        "Monthly Owner Draw",
        min_value=0.0,
        value=float(defaults["owner_draw"]),
        step=1000.0,
        key=f"{key_prefix}_owner_draw",
    )
    equity_default = register_defaults.get("equity_injection", 100000.0)
    equity_injection = st.number_input(
        "Equity Injection (upfront)",
        min_value=0.0,
        value=float(equity_default),
        step=25000.0,
        key=f"{key_prefix}_equity",
        help="Optional one-time equity contribution at model start.",
    )

    st.markdown("###### Operating assumptions")
    slider_col1, slider_col2, slider_col3 = st.columns(3)
    with slider_col1:
        revenue_growth = st.slider(
            "Annual Revenue Growth Rate",
            min_value=0.0,
            max_value=0.8,
            value=float(defaults["growth"]),
            step=0.01,
            key=f"{key_prefix}_growth",
        )
    with slider_col2:
        gross_margin = st.slider(
            "Gross Margin",
            min_value=0.1,
            max_value=0.9,
            value=float(defaults["margin"]),
            step=0.01,
            key=f"{key_prefix}_margin",
        )
    with slider_col3:
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

    st.markdown("###### Debt assumptions")
    debt_col1, debt_col2, debt_col3 = st.columns(3)
    with debt_col1:
        loan_amount_default = register_defaults.get("loan_amount")
        if loan_amount_default is None or loan_amount_default <= 0:
            loan_amount_default = 1500000.0 if scenario_type == "Acquire Existing Business" else 1000000.0
        loan_amount = st.number_input(
            "Construction Loan Amount",
            min_value=0.0,
            value=float(loan_amount_default),
            step=50000.0,
            key=f"{key_prefix}_loan_amount",
        )
    with debt_col2:
        loan_rate_default = register_defaults.get("loan_rate", 0.08)
        loan_rate = st.slider(
            "Loan Rate (annual %)",
            min_value=0.0,
            max_value=0.18,
            value=float(loan_rate_default),
            step=0.005,
            format="%.3f",
            key=f"{key_prefix}_loan_rate",
        )
    with debt_col3:
        loan_term_years = st.number_input(
            "Loan Term (years)",
            min_value=1,
            max_value=20,
            value=10,
            step=1,
            key=f"{key_prefix}_loan_term",
        )

    label = f"{scenario_type} ({stress_case})"
    return ScenarioInputs(
        label=label,
        scenario_type=scenario_type,
        stress_case=stress_case,
        initial_cash=initial_cash,
        revenue_growth=revenue_growth,
        gross_margin=gross_margin,
        opex_ratio=opex_ratio,
        capex_ratio=capex_ratio,
        owner_draw=owner_draw,
        equity_injection=equity_injection,
        construction_start=construction_start,
        construction_duration_months=int(construction_duration),
        family_basket_value=family_basket_value,
        families_per_month=families_per_month,
        loan_amount=loan_amount,
        loan_rate=loan_rate,
        loan_term_years=int(loan_term_years),
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


def _months_between(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def run_projection(
    inputs: ScenarioInputs,
    projection_months: int,
    cash_safety_months: float,
    model_start: pd.Timestamp,
) -> dict:
    preset = STRESS_CASES[inputs.stress_case]
    growth = min(inputs.revenue_growth * preset["growth"], 0.9)
    gross_margin = max(min(inputs.gross_margin * preset["margin"], 0.95), 0.05)
    opex_ratio = max(min(inputs.opex_ratio * preset["opex"], 0.95), 0.05)

    months = pd.date_range(
        start=model_start,
        periods=projection_months,
        freq="MS",
    )
    df = pd.DataFrame({"month": months})
    monthly_growth = (1 + growth) ** (1 / 12) - 1

    construction_start = pd.Timestamp(inputs.construction_start).replace(day=1)
    launch_offset = max(
        0,
        _months_between(model_start, construction_start) + inputs.construction_duration_months,
    )
    families = np.zeros(projection_months)
    basket_series = np.zeros(projection_months)
    post_launch_idx = np.arange(projection_months) - launch_offset
    active_mask = post_launch_idx >= 0
    families[active_mask] = inputs.families_per_month * (post_launch_idx[active_mask] + 1)
    basket_series[active_mask] = inputs.family_basket_value * (1 + monthly_growth) ** post_launch_idx[active_mask]

    df["Families Active"] = families
    df["Revenue"] = families * basket_series
    df["COGS"] = -df["Revenue"] * (1 - gross_margin)
    df["Operating Expenses"] = -df["Revenue"] * opex_ratio
    df["Capex"] = -df["Revenue"] * inputs.capex_ratio
    df["Owner Draw"] = -inputs.owner_draw
    df["Financing"] = 0.0
    df.loc[df.index[0], "Financing"] += inputs.equity_injection
    loan_draw_idx = min(max(_months_between(model_start, construction_start), 0), projection_months - 1)
    if inputs.loan_amount > 0:
        df.loc[loan_draw_idx, "Financing"] += inputs.loan_amount

    loan_rate_monthly = inputs.loan_rate / 12 if inputs.loan_rate else 0.0
    term_months = max(1, inputs.loan_term_years * 12)
    if inputs.loan_amount > 0:
        if loan_rate_monthly == 0:
            amort_payment = inputs.loan_amount / term_months
        else:
            amort_payment = inputs.loan_amount * loan_rate_monthly / (1 - (1 + loan_rate_monthly) ** (-term_months))
        interest_only_payment = inputs.loan_amount * loan_rate_monthly
        debt_service = np.where(
            np.arange(projection_months) < launch_offset,
            interest_only_payment,
            amort_payment,
        )
    else:
        debt_service = np.zeros(projection_months)
    df["Debt Service"] = -debt_service

    df["EBITDA"] = df["Revenue"] + df["COGS"] + df["Operating Expenses"]
    df["Net Cash Flow"] = (
        df["EBITDA"] + df["Capex"] + df["Owner Draw"] + df["Financing"] + df["Debt Service"]
    )
    df["Cumulative Cash"] = inputs.initial_cash + df["Net Cash Flow"].cumsum()
    df["EBITDA Delta"] = df["EBITDA"].diff().fillna(0.0)
    df["Scenario"] = inputs.label

    min_cash = df["Cumulative Cash"].min()
    final_cash = df["Cumulative Cash"].iloc[-1]
    annual_recurring_revenue = df["Revenue"].iloc[-1] * 12
    avg_monthly_burn = df["Net Cash Flow"].mean()
    avg_debt_service = df["Debt Service"].mean()

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
        ("Avg Debt Service", avg_debt_service, "currency", "/month"),
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

    st.sidebar.markdown("### Model Controls")
    scenario_focus = st.sidebar.selectbox(
        "Scenario",
        ["Build New", "Buy Existing"],
        key="model_scenario",
    )
    case = st.sidebar.radio(
        "Case",
        ["Conservative", "Likely", "Aggressive"],
        index=1,
        key="model_case",
    )
    st.session_state["assumption_case"] = case

    assumption_drivers = get_model_assumptions(case=case)
    if assumption_drivers.get("inflation_general") is not None:
        defaults["growth"] = float(assumption_drivers["inflation_general"])
    if assumption_drivers.get("gross_margin_target") is not None:
        defaults["margin"] = float(assumption_drivers["gross_margin_target"])
    if assumption_drivers.get("store_payroll_pct_sales") is not None:
        defaults["opex"] = float(assumption_drivers["store_payroll_pct_sales"])
    if assumption_drivers.get("repairs_maintenance_pct_sales") is not None:
        defaults["capex"] = float(assumption_drivers["repairs_maintenance_pct_sales"])

    register_defaults: dict[str, float] = {}
    if assumption_drivers.get("avg_basket_size_y1") is not None:
        register_defaults["family_basket_value"] = float(assumption_drivers["avg_basket_size_y1"])
    households = assumption_drivers.get("market_households")
    penetration_y1 = assumption_drivers.get("household_penetration_y1")
    if households and penetration_y1:
        register_defaults["families_per_month"] = float(households) * float(penetration_y1) / 12
    if assumption_drivers.get("construction_loan_commitment") is not None:
        register_defaults["loan_amount"] = float(assumption_drivers["construction_loan_commitment"])
        register_defaults["equity_injection"] = float(assumption_drivers["construction_loan_commitment"]) * 0.1
    if assumption_drivers.get("construction_rate_annual") is not None:
        register_defaults["loan_rate"] = float(assumption_drivers["construction_rate_annual"])

    default_scenario_type = (
        "Start from Scratch" if scenario_focus == "Build New" else "Acquire Existing Business"
    )

    page_header(
        "Financial Model & Scenario Planning",
        "Model cash runway and profitability with adjustable assumptions, stress cases, "
        "and optional scenario comparisons.",
        icon="📈",
    )
    st.caption("Baseline assumptions pulled from `data/model_assumptions.csv`. Adjust and compare scenarios below.")

    model_start_date = st.date_input(
        "Model Start Month",
        value=date(2026, 1, 1),
        help="Financial projections begin on this month.",
    )
    model_start = pd.Timestamp(model_start_date).replace(day=1)

    projection_months = st.slider(
        "Projection Horizon (months)",
        min_value=12,
        max_value=60,
        step=6,
        value=36,
    )

    primary_inputs = collect_scenario_inputs(
        "Primary Scenario",
        "primary",
        defaults,
        model_start_date,
        default_scenario_type,
        register_defaults,
    )
    primary_result = run_projection(primary_inputs, projection_months, cash_safety_months, model_start)

    comparison_result = None
    with st.expander("Add Comparison Scenario", expanded=False):
        enable_comparison = st.checkbox("Enable comparison scenario", value=False)
        if enable_comparison:
            comparison_inputs = collect_scenario_inputs(
                "Comparison Scenario",
                "comparison",
                defaults,
                model_start_date,
                default_scenario_type,
                register_defaults,
            )
            comparison_result = run_projection(
                comparison_inputs,
                projection_months,
                cash_safety_months,
                model_start,
            )

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
    comp_df = primary_result["data"][
        ["month", "Revenue", "COGS", "Operating Expenses", "Capex", "Owner Draw", "Debt Service"]
    ].copy()
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
        "Families Active",
        "Revenue",
        "COGS",
        "Operating Expenses",
        "Capex",
        "Owner Draw",
        "Financing",
        "Debt Service",
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
