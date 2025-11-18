"""
Data access helpers for the CFO portal.

This module encapsulates all interactions with the underlying CSV
datasets. It provides convenience functions to load each table into a
Pandas DataFrame, as well as higher level helpers to compute key
metrics and aggregated views needed by the Streamlit pages. Keeping
data loading in a single place simplifies future changes (e.g. swapping
to a database or API) and improves testability.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

import pandas as pd
import streamlit as st

from config import (
    get_data_path,
    CHART_OF_ACCOUNTS_FILE,
    GL_TRANSACTIONS_FILE,
    BUDGET_FILE,
    CASHFLOW_FILE,
    OP_KPI_FILE,
    MODEL_ASSUMPTIONS_FILE,
    DATA_DIR,
)
ASSUMPTIONS_PATH = DATA_DIR / "assumptions_register.csv"

MODEL_DRIVER_KEYS = [
    "market_households",
    "household_penetration_y1",
    "household_penetration_y2",
    "household_penetration_y3",
    "visits_per_household_week",
    "avg_basket_size_y1",
    "gross_margin_target",
    "shrink_pct_sales",
    "vendor_rebates_pct_sales",
    "store_payroll_pct_sales",
    "payroll_burden_pct_wages",
    "marketing_pct_sales",
    "repairs_maintenance_pct_sales",
    "inventory_days_on_hand",
    "ap_days_payable",
    "construction_loan_commitment",
    "construction_rate_annual",
    "permanent_loan_rate",
    "bridge_loan_rate",
    "dscr_min_target",
    "inflation_general",
    "inflation_wages",
    "inflation_food_cost",
    "discount_rate_npv",
    "cash_runway_target_months",
]

CASE_TO_COLUMN = {
    "Conservative": "low_case",
    "Likely": "base_value",
    "Aggressive": "high_case",
}


@st.cache_data(show_spinner=False)
def load_assumptions_register() -> pd.DataFrame:
    """Load the full assumptions register from CSV."""
    return pd.read_csv(ASSUMPTIONS_PATH)


def save_assumptions_register(df: pd.DataFrame) -> None:
    """Persist updated assumptions and clear the cache for other sessions."""
    df.to_csv(ASSUMPTIONS_PATH, index=False)
    load_assumptions_register.clear()


def get_model_assumptions(case: str = "Likely") -> dict[str, float]:
    """Return the driver dict consumed by the financial model."""
    df = load_assumptions_register()
    column = CASE_TO_COLUMN.get(case, "base_value")
    drivers = df[df["item_key"].isin(MODEL_DRIVER_KEYS)].copy()
    return {
        row["item_key"]: float(row[column])
        for _, row in drivers.iterrows()
        if pd.notna(row[column])
    }




@lru_cache(maxsize=None)
def load_chart_of_accounts() -> pd.DataFrame:
    """Load the chart of accounts CSV into a DataFrame.

    Returns
    -------
    pandas.DataFrame
        DataFrame of accounts keyed by ``account_number``.
    """
    path = get_data_path(CHART_OF_ACCOUNTS_FILE)
    df = pd.read_csv(path, dtype={"account_number": str, "account_id": str})
    return df


@lru_cache(maxsize=None)
def load_gl_transactions() -> pd.DataFrame:
    """Load the general ledger transactions from CSV.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing transaction records.
    """
    path = get_data_path(GL_TRANSACTIONS_FILE)
    df = pd.read_csv(path, parse_dates=["txn_date"])
    df["account_number"] = df["account_number"].astype(str)
    return df


@lru_cache(maxsize=None)
def load_budget() -> pd.DataFrame:
    """Load the budget file into a DataFrame."""
    path = get_data_path(BUDGET_FILE)
    df = pd.read_csv(path, dtype={"account_number": str})
    return df


@lru_cache(maxsize=None)
def load_cashflow_items() -> pd.DataFrame:
    """Load the cashflow items into a DataFrame."""
    path = get_data_path(CASHFLOW_FILE)
    df = pd.read_csv(path, parse_dates=["date"])
    return df


@lru_cache(maxsize=None)
def load_operational_kpis() -> pd.DataFrame:
    """Load operational KPIs from CSV."""
    path = get_data_path(OP_KPI_FILE)
    df = pd.read_csv(path)
    return df


@lru_cache(maxsize=None)
def load_model_assumptions() -> pd.DataFrame:
    """Load model assumptions from CSV."""
    path = get_data_path(MODEL_ASSUMPTIONS_FILE)
    return pd.read_csv(path)


def get_transactions_by_period(
    period: Optional[str] = None,
    scenario: Optional[str] = None,
) -> pd.DataFrame:
    """Filter GL transactions by period and scenario.

    Parameters
    ----------
    period : str, optional
        Period in YYYY-MM format. If None, includes all periods.
    scenario : str, optional
        Scenario filter (e.g. "Actual", "Budget", "Forecast"). If None,
        includes all scenarios.

    Returns
    -------
    pandas.DataFrame
        Filtered DataFrame of transactions.
    """
    df = load_gl_transactions().copy()
    if period is not None:
        df = df[df["period"] == period]
    if scenario is not None:
        df = df[df["scenario"].str.casefold() == scenario.casefold()]
    return df


def aggregate_income_statement(
    scenario: str = "Actual",
    periods: list[str] | None = None,
    group_by: Literal["pl_group", "analysis_group", "account_number"] = "pl_group",
) -> pd.DataFrame:
    """Create an aggregated income statement for the given scenario.

    This function groups transactions by the specified column (default
    ``pl_group``) and sums the amounts across the selected periods. It
    returns a DataFrame ready to be displayed as a P&L table.

    Parameters
    ----------
    scenario : str
        Which scenario to pull (Actual, Budget, Forecast). Defaults to Actual.
    periods : list[str], optional
        List of periods (YYYY-MM) to include. If None, uses all available
        periods.
    group_by : str
        Column to group by. Typical values are ``pl_group``, ``analysis_group``
        or ``account_number``.

    Returns
    -------
    pandas.DataFrame
        Grouped DataFrame with columns ``group_name`` and ``amount``.
    """
    txn_df = load_gl_transactions()
    coa = load_chart_of_accounts()
    # Filter scenario and periods
    mask = txn_df["scenario"].str.casefold() == scenario.casefold()
    if periods:
        mask &= txn_df["period"].isin(periods)
    filtered = txn_df[mask]
    # Merge with accounts to get grouping metadata
    merged = filtered.merge(coa[["account_number", group_by]], on="account_number", how="left")
    # Summarize amounts
    result = merged.groupby(group_by)["amount"].sum().reset_index()
    result.rename(columns={group_by: "group_name", "amount": "amount"}, inplace=True)
    # Sort by amount descending
    result.sort_values("amount", ascending=False, inplace=True)
    return result


def compute_key_metrics(period: str, scenario: str = "Actual") -> dict[str, float]:
    """Compute the critical metrics for a single period and scenario.

    Returns a dictionary with revenue, gross profit, net profit and cash
    flow. Revenue is the sum of all revenue accounts; gross profit is
    revenue minus cost of goods sold; net profit includes operating
    expenses; cash flow is derived from cashflow_items.

    Parameters
    ----------
    period : str
        Period in YYYY-MM format to compute metrics for.
    scenario : str
        Scenario (Actual/Budget/Forecast). Defaults to Actual.

    Returns
    -------
    dict
        Dictionary keyed by metric name with floating point amounts.
    """
    txns = get_transactions_by_period(period=period, scenario=scenario)
    coa = load_chart_of_accounts()
    # Merge to attach pl_group
    merged = txns.merge(coa[["account_number", "pl_group"]], on="account_number", how="left")
    # Revenue accounts have positive amounts; COGS negative (already negative in data).
    revenue = merged.loc[merged["pl_group"].str.contains("Sales", na=False), "amount"].sum()
    cogs = merged.loc[merged["pl_group"].str.contains("COGS", na=False), "amount"].sum()
    gross_profit = revenue + cogs  # cogs is negative
    # Net profit: sum all amounts (already includes revenue, cogs and expenses)
    net_profit = merged["amount"].sum()
    # Cash flow: sum cashflow items for the period
    cf_df = load_cashflow_items()
    cf_period = cf_df[(cf_df["period"] == period) & (cf_df["scenario"].str.casefold() == scenario.casefold())]
    cash_flow = cf_period["amount"].sum()
    return {
        "Revenue": revenue,
        "Gross Profit": gross_profit,
        "Net Profit": net_profit,
        "Cash Flow": cash_flow,
    }


def list_periods() -> list[str]:
    """Return a sorted list of available periods in the transactions data."""
    txns = load_gl_transactions()
    return sorted(txns["period"].unique())


def list_ratio_metrics() -> dict[str, str]:
    """Return definitions of standard financial ratios.

    The values returned can be used to populate a dropdown with human
    friendly names. Calculation logic resides in another helper.
    """
    return {
        "Gross Margin": "gross_margin",
        "Net Margin": "net_margin",
        "Current Ratio": "current_ratio",
        "Quick Ratio": "quick_ratio",
        "Debt to Equity": "debt_to_equity",
    }


def compute_ratios(period: str, scenario: str = "Actual") -> dict[str, float]:
    """Compute financial ratios for the given period and scenario.

    Ratios are derived from account balances aggregated from the GL and
    cashflow data. This simplified implementation treats all assets as
    current assets and liabilities as current liabilities for the
    purpose of the current and quick ratios. In a real‑world
    implementation you would distinguish between current and long
    accounts based on the chart of accounts metadata.
    """
    txns = get_transactions_by_period(period=period, scenario=scenario)
    coa = load_chart_of_accounts()
    merged = txns.merge(coa[["account_number", "account_type", "pl_group"]], on="account_number", how="left")
    # Compute totals by account type
    totals = merged.groupby("account_type")["amount"].sum().to_dict()
    assets = totals.get("Asset", 0)
    liabilities = totals.get("Liability", 0)
    equity = totals.get("Equity", 0)
    # Sales & COGS for margins
    revenue = merged.loc[merged["pl_group"].str.contains("Sales", na=False), "amount"].sum()
    cogs = merged.loc[merged["pl_group"].str.contains("COGS", na=False), "amount"].sum()
    net_profit = merged["amount"].sum()
    # Quick ratio uses cash and receivables only. For simplicity we'll
    # approximate cash as the cashflow opening balance for the period plus
    # cumulative cash inflows; receivables not modelled so it's same as assets.
    cf_df = load_cashflow_items()
    cf_period = cf_df[(cf_df["period"] == period) & (cf_df["scenario"].str.casefold() == scenario.casefold())]
    cash_balance = cf_period.loc[cf_period["item_type"] == "Opening Cash", "amount"].sum()
    # Calculate ratios
    ratios: dict[str, float] = {}
    ratios["gross_margin"] = (revenue + cogs) / revenue if revenue else 0
    ratios["net_margin"] = net_profit / revenue if revenue else 0
    ratios["current_ratio"] = (assets) / abs(liabilities) if liabilities else 0
    ratios["quick_ratio"] = cash_balance / abs(liabilities) if liabilities else 0
    ratios["debt_to_equity"] = abs(liabilities) / equity if equity else 0
    return ratios
