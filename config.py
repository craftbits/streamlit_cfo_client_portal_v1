"""
Central configuration for the CFO portal.

This module centralises various configuration values, default settings and
convenience functions used throughout the app. Having a single source
of truth for file paths and names makes it easy to adjust data sources
without modifying multiple files. Additionally, any global constants
should be defined here.

The portal stores its datasets as CSV files under the ``data``
subdirectory. Use the ``get_data_path`` helper to construct the full
path to a given CSV file. Default page names and navigation order are
also defined here.
"""
from __future__ import annotations

from pathlib import Path

# Base directory of the project. We compute this relative to this file
# so that it works whether you run the app via ``streamlit run app.py``
# or import modules from elsewhere.
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

# Names of CSV files used by the portal. If you generate new data
# schemas or update the filenames they should be updated here. See
# ``generate_data.py`` for definitions of the generated files.
CHART_OF_ACCOUNTS_FILE = "chart_of_accounts.csv"
GL_TRANSACTIONS_FILE = "gl_transactions.csv"
BUDGET_FILE = "budget_monthly.csv"
CASHFLOW_FILE = "cashflow_items.csv"
OP_KPI_FILE = "operational_kpis.csv"
MODEL_ASSUMPTIONS_FILE = "model_assumptions.csv"

# Mapping of page names to the python module implementing the view. The
# key is used for sidebar navigation and the value is the module name
# under ``PAGE_MODULE_PACKAGE``. When adding new pages update this dict.
PAGE_ROUTES = {
    "Home": "home",
    "Financial Statements": "financial_statements",
    "Comparison": "comparison",
    "Review": "review",
    "Cash Flow": "cash_flow",
    "Ratio Analysis": "ratio_analysis",
    "Financial Model": "financial_model",
    "Assumptions": "assumptions",
    # Placeholders for future sections. They will simply display a
    # coming‑soon message until implemented.
    "Tools": None,
    "Resources": None,
    "Links": None,
    "Directories": None,
    "Reference": None,
}

# Navigation is organised into high-level sections for the sidebar.
# Each tuple contains the section label and the ordered list of pages
# (keys from ``PAGE_ROUTES``) that belong to that section.
NAV_SECTIONS: list[tuple[str, list[str]]] = [
    ("Overview", ["Home"]),
    ("Management Reporting", ["Financial Statements", "Comparison", "Review"]),
    (
        "Performance & Planning",
        ["Cash Flow", "Ratio Analysis", "Financial Model", "Assumptions"],
    ),
    ("Knowledge Base", ["Tools", "Resources", "Links", "Directories", "Reference"]),
]

# Directory/package that stores the Streamlit page modules. Renaming this
# prevents Streamlit's automatic page picker from rendering on the main UI.
PAGE_MODULE_PACKAGE = "views"


def get_data_path(filename: str) -> Path:
    """Return the full path to a data file in the ``data`` directory.

    Parameters
    ----------
    filename : str
        Name of the CSV file to locate.

    Returns
    -------
    pathlib.Path
        Full path to the requested data file.
    """
    return DATA_DIR / filename


def available_scenarios() -> list[str]:
    """List the available scenarios present in the data.

    This function simply returns common scenario names. In the
    future this could be extended to read distinct scenarios from the
    dataset itself.
    """
    return ["Actual", "Budget", "Forecast"]
