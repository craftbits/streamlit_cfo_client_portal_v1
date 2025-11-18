"""
Layout and UI helpers.

The functions defined here encapsulate common UI patterns for the
portal, such as rendering metric cards, stylised sections and
downloadable tables. By consolidating these helpers the pages stay
concise and changes to the look and feel can be made centrally.

Some CSS is injected via ``st.markdown`` blocks to style the metric
cards similar to the reference portal. See ``build_metric_row`` for
usage.
"""
from __future__ import annotations

import base64
from io import BytesIO
from typing import Iterable, Tuple

import pandas as pd
import streamlit as st


def inject_css() -> None:
    """Inject custom CSS to tweak Streamlit's default styling."""
    st.markdown(
        """
        <style>
        .metric-card {
            border: 1px solid #f0f2f6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: #ffffff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .metric-title {
            font-size: 0.875rem;
            color: #6c757d;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #212529;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_currency(amount: float, currency: str = "$", precision: int = 0) -> str:
    """Format a number as a currency string with separators.

    Parameters
    ----------
    amount : float
        Numeric value to format.
    currency : str
        Currency symbol prefix. Defaults to '$'.
    precision : int
        Number of decimal places.
    """
    return f"{currency}{amount:,.{precision}f}"


def build_metric_row(metrics: Iterable[Tuple[str, float]], columns: int = 4) -> None:
    """Render a row of metric cards.

    Parameters
    ----------
    metrics : iterable of tuples
        Each tuple should contain a label and a numeric value.
    columns : int
        Number of columns to split the row into. Defaults to 4.
    """
    # Create columns and iterate metrics. If fewer metrics than columns, reuse columns.
    cols = st.columns(columns)
    for idx, (label, value) in enumerate(metrics):
        col = cols[idx % columns]
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">{label}</div>
                    <div class="metric-value">{format_currency(value)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def table_download_link(df: pd.DataFrame, filename: str) -> None:
    """Render a download button to export a DataFrame as CSV."""
    csv = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv).decode()
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
    )
