"""
generate_data.py
------------------

This helper script creates a suite of CSV files that underpin the
Supermarket CFO portal.  The goal of this script is to produce a
comprehensive chart of accounts as well as a handful of realistic
transactional datasets for demonstration purposes.  Running this
script will populate the ``data/`` directory inside the project with
fresh CSV files every time.

Datasets created:

* ``chart_of_accounts.csv`` — A detailed chart of accounts for a
  mid‑sized supermarket.  Account numbers follow a logical
  numbering scheme (assets in the 1000s, liabilities in the 2000s,
  equity in the 3000s, revenue in the 4000s, COGS in the 5000s,
  operating expenses in the 6000s, and other/non‑operating items in
  the 7000/8000 range).  Each account is annotated with its
  ``account_type``, ``pl_group``, ``report_class`` and other
  attributes used by the portal for grouping and ratio analysis.

* ``gl_transactions.csv`` — A sample general ledger covering the
  first eight months of 2025.  Transactions are generated for each
  revenue and COGS account with simple seasonality assumptions and
  a handful of operating expense line items.  The GL includes
  fields for transaction date, period, scenario (always ``Actual``
  in the sample), account numbers and amounts.

* ``budget_monthly.csv`` — A corresponding budget that assumes
  modest growth relative to the actuals.  The budget is expressed
  at the account/month level and can be compared against actuals.

* ``cashflow_items.csv`` — Opening cash balances and a few cash
  inflow/outflow events for each month.  This data supports the
  cash runway view on the portal.

* ``operational_kpis.csv`` — Simplified operational metrics such as
  headcount and customer counts.  These demonstrate how the portal
  can display non‑financial KPIs alongside the financials.

* ``model_assumptions.csv`` — A handful of baseline assumptions used
  for scenario modelling.  These values can be edited by users via
  CSV or via the portal UI.

To regenerate the data, simply run this script with Python:

```
python generate_data.py
```

This script is idempotent — it overwrites the output files on every
run.
"""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def make_chart_of_accounts() -> pd.DataFrame:
    """Return a DataFrame defining the supermarket chart of accounts."""
    # Define each account as a tuple for clarity.  Fields:
    # (account_number, account_name, account_type, debit_credit_normal,
    #  pl_group, report_class, ratio_group, analysis_group,
    #  external_group, parent_account_id, level, is_summary,
    #  is_cash_flow, is_revenue_driver, display_order)
    accounts = [
        # Assets
        (1000, "Cash and Cash Equivalents", "Asset", "Debit", "Balance", "Current Assets",
         "", "Liquidity", "Assets", None, 1, 0, 1, 0, 10),
        (1010, "Petty Cash", "Asset", "Debit", "Balance", "Current Assets",
         "", "Liquidity", "Assets", 1000, 2, 0, 0, 0, 20),
        (1020, "Checking Account", "Asset", "Debit", "Balance", "Current Assets",
         "", "Liquidity", "Assets", 1000, 2, 0, 1, 0, 30),
        (1030, "Savings Account", "Asset", "Debit", "Balance", "Current Assets",
         "", "Liquidity", "Assets", 1000, 2, 0, 1, 0, 40),
        (1100, "Accounts Receivable", "Asset", "Debit", "Balance", "Current Assets",
         "", "Working capital", "Assets", None, 1, 0, 0, 0, 50),
        # Inventory broken down by department
        (1210, "Inventory – Produce", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 60),
        (1220, "Inventory – Meat & Seafood", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 70),
        (1230, "Inventory – Dairy & Eggs", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 80),
        (1240, "Inventory – Bakery", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 90),
        (1250, "Inventory – Deli & Prepared", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 100),
        (1260, "Inventory – Frozen Foods", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 110),
        (1270, "Inventory – Beverages & Snacks", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 120),
        (1280, "Inventory – Non‑Food", "Asset", "Debit", "Balance", "Inventory",
         "", "Inventory", "Assets", None, 1, 0, 0, 0, 130),
        (1300, "Prepaid Expenses", "Asset", "Debit", "Balance", "Current Assets",
         "", "Working capital", "Assets", None, 1, 0, 0, 0, 140),
        (1400, "Store Supplies", "Asset", "Debit", "Balance", "Current Assets",
         "", "Working capital", "Assets", None, 1, 0, 0, 0, 150),
        # Fixed assets
        (1510, "Land", "Asset", "Debit", "Balance", "Fixed Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 160),
        (1520, "Buildings & Leasehold Improvements", "Asset", "Debit", "Balance", "Fixed Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 170),
        (1530, "Furniture & Fixtures", "Asset", "Debit", "Balance", "Fixed Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 180),
        (1540, "Equipment & Machinery", "Asset", "Debit", "Balance", "Fixed Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 190),
        (1550, "Vehicles", "Asset", "Debit", "Balance", "Fixed Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 200),
        (1600, "Accumulated Depreciation", "Asset", "Credit", "Balance", "Contra Assets",
         "", "Long term", "Assets", None, 1, 0, 0, 0, 210),
        (1700, "Security Deposits", "Asset", "Debit", "Balance", "Other Assets",
         "", "Other", "Assets", None, 1, 0, 0, 0, 220),
        (1800, "Other Assets", "Asset", "Debit", "Balance", "Other Assets",
         "", "Other", "Assets", None, 1, 0, 0, 0, 230),

        # Liabilities
        (2000, "Accounts Payable", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Working capital", "Liabilities", None, 1, 0, 0, 0, 240),
        (2010, "Supplier Payables", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Working capital", "Liabilities", 2000, 2, 0, 0, 0, 250),
        (2020, "Accrued Expenses", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Working capital", "Liabilities", None, 1, 0, 0, 0, 260),
        (2030, "Payroll Liabilities", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Working capital", "Liabilities", None, 1, 0, 0, 0, 270),
        (2040, "Sales Tax Payable", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Working capital", "Liabilities", None, 1, 0, 0, 0, 280),
        (2050, "Gift Card & Loyalty Liability", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Other", "Liabilities", None, 1, 0, 0, 0, 290),
        (2060, "Customer Deposits", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Other", "Liabilities", None, 1, 0, 0, 0, 300),
        (2100, "Short‑Term Loans", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Financing", "Liabilities", None, 1, 0, 0, 0, 310),
        (2200, "Current Portion of Long‑Term Debt", "Liability", "Credit", "Balance", "Current Liabilities",
         "", "Financing", "Liabilities", None, 1, 0, 0, 0, 320),
        (2300, "Long‑Term Loans", "Liability", "Credit", "Balance", "Long‑Term Liabilities",
         "", "Financing", "Liabilities", None, 1, 0, 0, 0, 330),
        (2310, "Lease Liability", "Liability", "Credit", "Balance", "Long‑Term Liabilities",
         "", "Financing", "Liabilities", None, 1, 0, 0, 0, 340),
        (2400, "Deferred Revenue", "Liability", "Credit", "Balance", "Long‑Term Liabilities",
         "", "Other", "Liabilities", None, 1, 0, 0, 0, 350),
        (2500, "Other Liabilities", "Liability", "Credit", "Balance", "Other Liabilities",
         "", "Other", "Liabilities", None, 1, 0, 0, 0, 360),

        # Equity
        (3000, "Owner Capital", "Equity", "Credit", "Balance", "Equity",
         "", "", "Equity", None, 1, 0, 0, 0, 370),
        (3100, "Retained Earnings", "Equity", "Credit", "Balance", "Equity",
         "", "", "Equity", None, 1, 0, 0, 0, 380),
        (3200, "Shareholder Capital", "Equity", "Credit", "Balance", "Equity",
         "", "", "Equity", None, 1, 0, 0, 0, 390),
        (3300, "Owner Distributions", "Equity", "Debit", "Balance", "Equity",
         "", "", "Equity", None, 1, 0, 0, 0, 400),

        # Revenue accounts
        (4000, "Sales – Produce", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Produce", "Income", None, 1, 0, 0, 1, 410),
        (4010, "Sales – Meat & Seafood", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Meat & Seafood", "Income", None, 1, 0, 0, 1, 420),
        (4020, "Sales – Dairy & Eggs", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Dairy & Eggs", "Income", None, 1, 0, 0, 1, 430),
        (4030, "Sales – Bakery", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Bakery", "Income", None, 1, 0, 0, 1, 440),
        (4040, "Sales – Deli & Prepared", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Deli", "Income", None, 1, 0, 0, 1, 450),
        (4050, "Sales – Frozen Foods", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Frozen", "Income", None, 1, 0, 0, 1, 460),
        (4060, "Sales – Beverages & Snacks", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Beverages & Snacks", "Income", None, 1, 0, 0, 1, 470),
        (4070, "Sales – Non‑Food", "Revenue", "Credit", "Revenue", "Store Operations",
         "Revenue", "Non‑Food", "Income", None, 1, 0, 0, 1, 480),
        (4080, "Sales Returns & Allowances", "Revenue", "Debit", "Revenue", "Contra Revenue",
         "Revenue", "Returns", "Income", None, 1, 0, 0, 0, 490),
        (4100, "Service Income", "Revenue", "Credit", "Other Income", "Other",
         "Operating margin", "Services", "Income", None, 1, 0, 0, 0, 500),
        (4110, "Vendor Rebates & Discounts", "Revenue", "Credit", "Other Income", "Other",
         "Operating margin", "Rebates", "Income", None, 1, 0, 0, 0, 510),
        (4120, "Rental/Space Income", "Revenue", "Credit", "Other Income", "Other",
         "Operating margin", "Rental", "Income", None, 1, 0, 0, 0, 520),
        (4130, "Lottery Commissions", "Revenue", "Credit", "Other Income", "Other",
         "Operating margin", "Other", "Income", None, 1, 0, 0, 0, 530),
        (4140, "Other Operating Income", "Revenue", "Credit", "Other Income", "Other",
         "Operating margin", "Other", "Income", None, 1, 0, 0, 0, 540),

        # Cost of goods sold
        (5000, "COGS – Produce", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Produce", "COGS", None, 1, 0, 0, 0, 550),
        (5010, "COGS – Meat & Seafood", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Meat & Seafood", "COGS", None, 1, 0, 0, 0, 560),
        (5020, "COGS – Dairy & Eggs", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Dairy & Eggs", "COGS", None, 1, 0, 0, 0, 570),
        (5030, "COGS – Bakery", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Bakery", "COGS", None, 1, 0, 0, 0, 580),
        (5040, "COGS – Deli & Prepared", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Deli", "COGS", None, 1, 0, 0, 0, 590),
        (5050, "COGS – Frozen Foods", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Frozen", "COGS", None, 1, 0, 0, 0, 600),
        (5060, "COGS – Beverages & Snacks", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Beverages & Snacks", "COGS", None, 1, 0, 0, 0, 610),
        (5070, "COGS – Non‑Food", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Non‑Food", "COGS", None, 1, 0, 0, 0, 620),
        (5090, "Freight & Shipping (Inbound)", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Logistics", "COGS", None, 1, 0, 0, 0, 630),
        (5110, "Inventory Shrink/Spoilage", "COGS", "Debit", "COGS", "Direct Costs",
         "Gross margin", "Losses", "COGS", None, 1, 0, 0, 0, 640),

        # Operating Expenses – Sales & Marketing
        (6100, "Advertising & Marketing", "Expense", "Debit", "OpEx", "Sales & Marketing",
         "Operating margin", "Marketing", "Sales & Marketing", None, 1, 0, 0, 0, 650),
        (6110, "Promotions & Loyalty Programs", "Expense", "Debit", "OpEx", "Sales & Marketing",
         "Operating margin", "Marketing", "Sales & Marketing", None, 1, 0, 0, 0, 660),
        (6120, "Merchant & Card Fees", "Expense", "Debit", "OpEx", "Sales & Marketing",
         "Operating margin", "Finance", "Sales & Marketing", None, 1, 0, 0, 0, 670),

        # Operating Expenses – Payroll
        (6200, "Salaries & Wages", "Expense", "Debit", "OpEx", "Payroll",
         "Operating margin", "Payroll", "HR", None, 1, 0, 0, 0, 680),
        (6210, "Payroll Taxes", "Expense", "Debit", "OpEx", "Payroll",
         "Operating margin", "Payroll", "HR", None, 1, 0, 0, 0, 690),
        (6220, "Employee Benefits", "Expense", "Debit", "OpEx", "Payroll",
         "Operating margin", "Payroll", "HR", None, 1, 0, 0, 0, 700),
        (6230, "Bonuses & Incentives", "Expense", "Debit", "OpEx", "Payroll",
         "Operating margin", "Payroll", "HR", None, 1, 0, 0, 0, 710),
        (6240, "Contractor & Temp Labor", "Expense", "Debit", "OpEx", "Payroll",
         "Operating margin", "Payroll", "HR", None, 1, 0, 0, 0, 720),

        # Operating Expenses – Occupancy & Facilities
        (6300, "Rent Expense", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 730),
        (6310, "Utilities", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 740),
        (6320, "Repairs & Maintenance", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 750),
        (6330, "Property Taxes", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 760),
        (6340, "Insurance", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Finance", "Facilities", None, 1, 0, 0, 0, 770),
        (6350, "Cleaning & Janitorial", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 780),
        (6360, "Security", "Expense", "Debit", "OpEx", "Facilities",
         "Operating margin", "Facilities", "Facilities", None, 1, 0, 0, 0, 790),

        # Operating Expenses – Operations & G&A
        (6400, "Supplies (Office & Store)", "Expense", "Debit", "OpEx", "Operations",
         "Operating margin", "Operations", "Operations", None, 1, 0, 0, 0, 800),
        (6410, "Packaging & Bags", "Expense", "Debit", "OpEx", "Operations",
         "Operating margin", "Operations", "Operations", None, 1, 0, 0, 0, 810),
        (6420, "Small Equipment & Tools", "Expense", "Debit", "OpEx", "Operations",
         "Operating margin", "Operations", "Operations", None, 1, 0, 0, 0, 820),
        (6430, "POS & Payment Processing Fees", "Expense", "Debit", "OpEx", "Operations",
         "Operating margin", "Finance", "Operations", None, 1, 0, 0, 0, 830),
        (6440, "Banking & Financial Services", "Expense", "Debit", "OpEx", "Finance",
         "Operating margin", "Finance", "Operations", None, 1, 0, 0, 0, 840),
        (6450, "Professional Fees", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Advisory", "Operations", None, 1, 0, 0, 0, 850),
        (6460, "Licenses & Permits", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Compliance", "Operations", None, 1, 0, 0, 0, 860),
        (6470, "Dues & Subscriptions", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Compliance", "Operations", None, 1, 0, 0, 0, 870),
        (6480, "Telephone & Internet", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "IT", "Operations", None, 1, 0, 0, 0, 880),
        (6490, "Travel & Entertainment", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "HR", "Operations", None, 1, 0, 0, 0, 890),
        (6500, "Training & Development", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "HR", "Operations", None, 1, 0, 0, 0, 900),
        (6510, "Bad Debt Expense", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Finance", "Operations", None, 1, 0, 0, 0, 910),
        (6520, "IT & Software", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "IT", "Operations", None, 1, 0, 0, 0, 920),
        (6530, "Depreciation & Amortization", "Expense", "Debit", "OpEx", "Non‑cash",
         "EBITDA", "Finance", "Operations", None, 1, 0, 0, 0, 930),
        (6540, "Uniforms", "Expense", "Debit", "OpEx", "Operations",
         "Operating margin", "HR", "Operations", None, 1, 0, 0, 0, 940),
        (6550, "Donations & Charitable", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Community", "Operations", None, 1, 0, 0, 0, 950),
        (6560, "Miscellaneous Expense", "Expense", "Debit", "OpEx", "G&A",
         "Operating margin", "Other", "Operations", None, 1, 0, 0, 0, 960),

        # Other expenses / non‑operating items
        (7000, "Interest Expense", "Expense", "Debit", "Other Expenses", "Finance",
         "Below‑the‑line", "Finance", "Other", None, 1, 0, 0, 0, 970),
        (7010, "Penalties & Fines", "Expense", "Debit", "Other Expenses", "Other",
         "Below‑the‑line", "Other", "Other", None, 1, 0, 0, 0, 980),
        (7020, "Loss on Sale of Assets", "Expense", "Debit", "Other Expenses", "Other",
         "Below‑the‑line", "Other", "Other", None, 1, 0, 0, 0, 990),
        (7040, "Income Tax Expense", "Expense", "Debit", "Other Expenses", "Finance",
         "Below‑the‑line", "Finance", "Other", None, 1, 0, 0, 0, 1000),
        (8000, "Other Non‑Operating Income", "Revenue", "Credit", "Other Income", "Other",
         "Below‑the‑line", "Other", "Other", None, 1, 0, 0, 0, 1010),
    ]
    columns = [
        "account_number",
        "account_name",
        "account_type",
        "debit_credit_normal",
        "pl_group",
        "report_class",
        "ratio_group",
        "analysis_group",
        "external_group",
        "parent_account_id",
        "level",
        "is_summary",
        "is_cash_flow",
        "is_revenue_driver",
        "display_order",
    ]
    df = pd.DataFrame(accounts, columns=columns)
    # assign account_id equal to account_number for simplicity
    df.insert(0, "account_id", df["account_number"])
    return df


def make_gl_transactions(coa: pd.DataFrame) -> pd.DataFrame:
    """Generate a simple GL for Jan–Aug 2025 based on the COA."""
    np.random.seed(42)
    months = pd.date_range("2025-01-01", "2025-08-01", freq="MS")
    records = []
    txn_counter = 1

    # Baseline sales per category in USD for January; will grow modestly each month
    base_sales = {
        4000: 50_000,  # Produce
        4010: 70_000,  # Meat & Seafood
        4020: 40_000,  # Dairy
        4030: 30_000,  # Bakery
        4040: 25_000,  # Deli & Prepared
        4050: 35_000,  # Frozen Foods
        4060: 45_000,  # Beverages & Snacks
        4070: 15_000,  # Non‑Food
    }
    gross_margin_rate = 0.33  # 33% gross profit margin

    for month in months:
        period = month.strftime("%Y-%m")
        # Determine growth factor: modest 2% month over month
        month_index = (month.month - months[0].month)
        growth_factor = 1 + 0.02 * month_index

        # Revenue transactions
        for acct_num, base_val in base_sales.items():
            amount = base_val * growth_factor
            txn_id = f"TXN-{period}-{txn_counter:03d}"
            records.append({
                "txn_id": txn_id,
                "txn_date": (month + pd.Timedelta(days=4)).strftime("%Y-%m-%d"),
                "period": period,
                "scenario": "Actual",
                "account_number": acct_num,
                "account_id": acct_num,
                "department": "Main",
                "location": "Headquarters",
                "description": f"Sales – {coa.loc[coa['account_number']==acct_num, 'account_name'].values[0]}",
                "amount": round(amount, 2),
                "source": "POS",
            })
            txn_counter += 1

            # Corresponding COGS transaction for each revenue line
            cogs_map = {
                4000: 5000,
                4010: 5010,
                4020: 5020,
                4030: 5030,
                4040: 5040,
                4050: 5050,
                4060: 5060,
                4070: 5070,
            }
            cogs_acct_num = cogs_map.get(acct_num)
            if cogs_acct_num:
                cogs_amount = -(amount * (1 - gross_margin_rate))  # negative for cost (debit) relative to revenue credit
                txn_id = f"TXN-{period}-{txn_counter:03d}"
                records.append({
                    "txn_id": txn_id,
                    "txn_date": (month + pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
                    "period": period,
                    "scenario": "Actual",
                    "account_number": cogs_acct_num,
                    "account_id": cogs_acct_num,
                    "department": "Main",
                    "location": "Headquarters",
                    "description": f"COGS – {coa.loc[coa['account_number']==cogs_acct_num, 'account_name'].values[0]}",
                    "amount": round(cogs_amount, 2),
                    "source": "Inventory",
                })
                txn_counter += 1

        # Operating expenses – simplified set per month
        # Payroll
        payroll_amount = 100_000 * growth_factor
        for acct_num in [6200, 6210, 6220]:
            txn_id = f"TXN-{period}-{txn_counter:03d}"
            records.append({
                "txn_id": txn_id,
                "txn_date": (month + pd.Timedelta(days=25)).strftime("%Y-%m-%d"),
                "period": period,
                "scenario": "Actual",
                "account_number": acct_num,
                "account_id": acct_num,
                "department": "Main",
                "location": "Headquarters",
                "description": coa.loc[coa['account_number']==acct_num, 'account_name'].values[0],
                "amount": round(-payroll_amount / 3, 2),
                "source": "Payroll",
            })
            txn_counter += 1

        # Rent – fixed amount 16,335/month; from October 2025 increases but our sample ends in Aug
        rent = 16_335
        txn_id = f"TXN-{period}-{txn_counter:03d}"
        records.append({
            "txn_id": txn_id,
            "txn_date": (month + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "account_number": 6300,
            "account_id": 6300,
            "department": "Main",
            "location": "Headquarters",
            "description": "Rent Expense",
            "amount": -rent,
            "source": "Manual",
        })
        txn_counter += 1

        # Utilities – 10k baseline
        utilities = 10_000 * growth_factor
        txn_id = f"TXN-{period}-{txn_counter:03d}"
        records.append({
            "txn_id": txn_id,
            "txn_date": (month + pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "account_number": 6310,
            "account_id": 6310,
            "department": "Main",
            "location": "Headquarters",
            "description": "Utilities",
            "amount": round(-utilities, 2),
            "source": "Utility",
        })
        txn_counter += 1

        # Advertising & marketing – 5k baseline
        marketing = 5_000 * growth_factor
        txn_id = f"TXN-{period}-{txn_counter:03d}"
        records.append({
            "txn_id": txn_id,
            "txn_date": (month + pd.Timedelta(days=15)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "account_number": 6100,
            "account_id": 6100,
            "department": "Main",
            "location": "Headquarters",
            "description": "Advertising & Marketing",
            "amount": round(-marketing, 2),
            "source": "Marketing",
        })
        txn_counter += 1

        # Insurance – approximate monthly cost
        insurance_mo = 4000 / 12 * growth_factor
        txn_id = f"TXN-{period}-{txn_counter:03d}"
        records.append({
            "txn_id": txn_id,
            "txn_date": (month + pd.Timedelta(days=12)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "account_number": 6340,
            "account_id": 6340,
            "department": "Main",
            "location": "Headquarters",
            "description": "Insurance",
            "amount": round(-insurance_mo, 2),
            "source": "Insurance",
        })
        txn_counter += 1

        # Interest expense – 5k monthly
        interest = 5_000
        txn_id = f"TXN-{period}-{txn_counter:03d}"
        records.append({
            "txn_id": txn_id,
            "txn_date": (month + pd.Timedelta(days=28)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "account_number": 7000,
            "account_id": 7000,
            "department": "Main",
            "location": "Headquarters",
            "description": "Interest Expense",
            "amount": -interest,
            "source": "Manual",
        })
        txn_counter += 1

    df = pd.DataFrame(records)
    return df


def make_budget_from_gl(gl: pd.DataFrame) -> pd.DataFrame:
    """Generate a simple budget by applying small growth to actuals."""
    agg = gl.groupby(["period", "account_number"])["amount"].sum().reset_index()
    agg["budget_amount"] = agg["amount"] * 1.05
    agg["scenario"] = "Budget"
    agg["account_id"] = agg["account_number"]
    budget = agg[["period", "account_number", "account_id", "scenario", "budget_amount"]]
    return budget


def make_cashflow_items() -> pd.DataFrame:
    """Create simple monthly cashflow items for Jan–Aug 2025."""
    months = pd.date_range("2025-01-01", "2025-08-01", freq="MS")
    records = []
    opening_cash = 300_000
    for month in months:
        period = month.strftime("%Y-%m")
        # Opening cash entry
        records.append({
            "date": month.strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "item_type": "Opening Cash",
            "description": "Beginning cash balance",
            "amount": opening_cash,
        })
        # Financing – optional loan draw in February & March
        if month.month in [2, 3]:
            records.append({
                "date": (month + pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
                "period": period,
                "scenario": "Actual",
                "item_type": "Financing",
                "description": "Loan draw",
                "amount": 50_000,
            })
            opening_cash += 50_000
        # Investing – Capex spending every quarter
        if month.month in [1, 4, 7]:
            records.append({
                "date": (month + pd.Timedelta(days=20)).strftime("%Y-%m-%d"),
                "period": period,
                "scenario": "Actual",
                "item_type": "Investing",
                "description": "Capex – equipment & improvements",
                "amount": -50_000,
            })
            opening_cash -= 50_000
        # Owner Draw – monthly draw of 10k
        records.append({
            "date": (month + pd.Timedelta(days=25)).strftime("%Y-%m-%d"),
            "period": period,
            "scenario": "Actual",
            "item_type": "Owner Draw",
            "description": "Owner distribution",
            "amount": -10_000,
        })
        opening_cash -= 10_000
    return pd.DataFrame(records)


def make_operational_kpis() -> pd.DataFrame:
    """Create a very simple operational KPI dataset."""
    months = pd.date_range("2025-01-01", "2025-08-01", freq="MS")
    metrics = []
    base_customers = 1000
    base_headcount = 50
    for i, month in enumerate(months):
        period = month.strftime("%Y-%m")
        growth = 1 + 0.015 * i  # 1.5% growth per month
        customers = int(base_customers * growth)
        new_customers = int(customers * 0.15)
        churned = int(customers * 0.05)
        headcount = int(base_headcount * (1 + 0.01 * i))
        avg_basket = 60 * growth  # average basket size in dollars
        metrics.extend([
            {"period": period, "scenario": "Actual", "metric_name": "Active Customers", "metric_value": customers, "unit": "Count"},
            {"period": period, "scenario": "Actual", "metric_name": "New Customers", "metric_value": new_customers, "unit": "Count"},
            {"period": period, "scenario": "Actual", "metric_name": "Churned Customers", "metric_value": churned, "unit": "Count"},
            {"period": period, "scenario": "Actual", "metric_name": "Headcount", "metric_value": headcount, "unit": "Count"},
            {"period": period, "scenario": "Actual", "metric_name": "Avg Basket Size", "metric_value": round(avg_basket, 2), "unit": "USD"},
        ])
    return pd.DataFrame(metrics)


def make_model_assumptions() -> pd.DataFrame:
    """Return baseline model assumptions."""
    data = [
        ("revenue_growth_rate_yoy", "Annual revenue growth rate", 0.15),
        ("gross_margin_target", "Target gross margin (0-1)", 0.33),
        ("opex_as_percent_revenue", "Operating expenses as % of revenue", 0.35),
        ("cash_safety_months", "Target cash runway (months)", 6),
        ("headcount_growth_rate_yoy", "Annual headcount growth rate", 0.10),
        ("capex_as_percent_revenue", "Capex as % of revenue", 0.04),
        ("owner_draw_monthly", "Owner distributions per month", 10000),
        ("tax_rate_effective", "Effective tax rate (0-1)", 0.21),
    ]
    df = pd.DataFrame(data, columns=["assumption_key", "description", "base_value"])
    return df


def main():
    root = Path(__file__).resolve().parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    coa = make_chart_of_accounts()
    gl = make_gl_transactions(coa)
    budget = make_budget_from_gl(gl)
    cashflow = make_cashflow_items()
    kpis = make_operational_kpis()
    assumptions = make_model_assumptions()

    # Write to CSVs
    coa.to_csv(data_dir / "chart_of_accounts.csv", index=False)
    gl.to_csv(data_dir / "gl_transactions.csv", index=False)
    budget.to_csv(data_dir / "budget_monthly.csv", index=False)
    cashflow.to_csv(data_dir / "cashflow_items.csv", index=False)
    kpis.to_csv(data_dir / "operational_kpis.csv", index=False)
    assumptions.to_csv(data_dir / "model_assumptions.csv", index=False)

    print(f"Generated data files in {data_dir}")


if __name__ == "__main__":
    main()