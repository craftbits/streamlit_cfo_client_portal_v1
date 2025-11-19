"""
Layout and UI helpers inspired by the Streamlit Executive Portal.

The shared CSS mirrors the clean Contour-style look: generous whitespace,
rounded metric cards and a tidy sidebar. Consolidating these helpers keeps
the visual language consistent across pages.
"""
from __future__ import annotations

from typing import Iterable, Optional, Tuple

import pandas as pd
import streamlit as st

_BASE_CSS = """
<style>
:root {
    --cfo-primary: #0f172a;
    --cfo-accent: #ef4444;
    --cfo-muted: #94a3b8;
    --cfo-bg: #f8fafc;
}
main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}
[data-testid="stSidebar"] {
    background: var(--cfo-bg);
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.25rem 2rem 1.25rem;
}
.sidebar-label {
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--cfo-muted);
    margin: 1.25rem 0 0.35rem 0;
}
.sidebar-label:first-of-type {
    margin-top: 0.5rem;
}
[data-testid="stSidebar"] .stSelectbox > label,
[data-testid="stSidebar"] .stRadio > label {
    display: none;
}
[data-baseweb="select"] > div {
    border-radius: 12px;
    border-color: #d4d4d8;
}
div[data-baseweb="radio"] > div {
    row-gap: 0.4rem;
}
div[data-baseweb="radio"] label {
    font-weight: 500;
    color: #0f172a;
}
div[data-baseweb="radio"] svg {
    color: var(--cfo-primary);
}
.page-title {
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--cfo-primary);
}
.page-caption {
    color: #64748b;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    background-color: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 4px 24px rgba(15, 23, 42, 0.04);
    margin-bottom: 1rem;
}
.metric-card-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 0.45rem;
}
.metric-card-value {
    font-size: 1.9rem;
    font-weight: 600;
    color: #0f172a;
}
.metric-card-note {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 0.4rem;
}
.stDownloadButton > button,
.stButton > button {
    border-radius: 999px;
    padding: 0.45rem 1.4rem;
    border: 1px solid #0f172a;
    background: #0f172a;
    color: white;
    font-weight: 600;
}
.stDownloadButton > button:hover,
.stButton > button:hover {
    border-color: var(--cfo-accent);
    background: var(--cfo-accent);
}
</style>
"""


def inject_css() -> None:
    """Inject the shared CSS once per run."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """Render a consistent page header."""
    heading = f"{icon} {title}" if icon else title
    st.markdown(f'<h1 class="page-title">{heading}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-caption">{subtitle}</p>', unsafe_allow_html=True)


def format_currency(amount: float, currency: str = "$", precision: int = 0) -> str:
    """Format a number as a currency string with separators."""
    return f"{currency}{amount:,.{precision}f}"


def metric_card(label: str, value: str, note: Optional[str] = None) -> None:
    """Render a single metric card with optional supporting note."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-card-label">{label}</div>
            <div class="metric-card-value">{value}</div>
            {f'<div class="metric-card-note">{note}</div>' if note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_metric_row(
    metrics: Iterable[Tuple[str, float]], columns: int = 4, currency: str = "$", precision: int = 0
) -> None:
    """Render a row of metric cards using the shared styling."""
    cols = st.columns(columns)
    for idx, (label, value) in enumerate(metrics):
        col = cols[idx % columns]
        with col:
            metric_card(label, format_currency(value, currency=currency, precision=precision))


def table_download_link(df: pd.DataFrame, filename: str) -> None:
    """Render a download button to export a DataFrame as CSV."""
    csv = df.to_csv(index=False).encode()
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
    )
