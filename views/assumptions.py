# cfo_portal/pages/assumptions.py
from __future__ import annotations

import pandas as pd
import streamlit as st

from data_access import (
    load_assumptions_register,
    save_assumptions_register,
    CASE_TO_COLUMN,
)

HIGH_LEVEL_GROUPS = [
    "Revenue & Demand",
    "Margins & COGS",
    "Opex & Staffing",
    "Financing",
    "Working Capital",
    "Macro & Risk",
]

def _current_case() -> str:
    if "assumptions_case" not in st.session_state:
        st.session_state["assumptions_case"] = "Likely"
    return st.session_state["assumptions_case"]

def render():
    st.title("Assumptions & Drivers")

    st.caption(
        "Tweak a small set of high-impact levers. "
        "We maintain detailed underlying assumptions but only expose what owners and lenders need to see."
    )

    # Scenario & case selectors in sidebar for consistency with your other pages
    with st.sidebar:
        st.subheader("Model view")
        scenario = st.selectbox("Scenario", ["Build New", "Buy Existing"], key="assumption_scenario")
        case = st.radio("Case", ["Conservative", "Likely", "Aggressive"], key="assumption_case", horizontal=False)

    active_case = st.session_state["assumption_case"]
    case_col = CASE_TO_COLUMN.get(active_case, "base_value")

    df = load_assumptions_register()

    st.info(
        f"Editing **{active_case}** case values "
        f"(mapped to column **{case_col}** in the assumptions CSV)."
    )

    tabs = st.tabs(HIGH_LEVEL_GROUPS + ["All assumptions"])

    for idx, group in enumerate(HIGH_LEVEL_GROUPS):
        with tabs[idx]:
            _render_group_editor(df, group, active_case, case_col)

    # "All assumptions" tab: read-only table + CSV download
    with tabs[-1]:
        st.subheader("Full assumptions register")
        st.caption("Read-only view; edit underlying CSV or mark rows editable to expose them above.")
        st.dataframe(df.sort_values(["category", "item_key"]))
        st.download_button(
            "Download assumptions_register.csv",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="assumptions_register.csv",
            mime="text/csv",
        )


def _render_group_editor(df: pd.DataFrame, group: str, case: str, case_col: str) -> None:
    st.subheader(group)

    group_df = df[
        (df["ui_group"] == group)
        & (df["ui_is_editable"] == 1)
    ].copy()

    if group_df.empty:
        st.write("No editable assumptions in this group yet.")
        return

    group_df = group_df.sort_values("ui_order")

    # Split into main / advanced controls
    main_rows = group_df[group_df["ui_is_advanced"] == 0]
    adv_rows = group_df[group_df["ui_is_advanced"] == 1]

    with st.form(f"{group}_form", clear_on_submit=False):
        updated_values: dict[str, float] = {}

        # Main controls (always visible)
        for _, row in main_rows.iterrows():
            val = _render_assumption_widget(row, case_col)
            updated_values[row["item_key"]] = val

        # Advanced controls in an expander
        if not adv_rows.empty:
            with st.expander("Advanced", expanded=False):
                for _, row in adv_rows.iterrows():
                    val = _render_assumption_widget(row, case_col)
                    updated_values[row["item_key"]] = val

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Save changes", type="primary")
        with col2:
            reset_clicked = st.form_submit_button("Reset to defaults")

    if submitted:
        # Write updated values into correct case column and persist
        for key, value in updated_values.items():
            mask = df["item_key"] == key
            df.loc[mask, case_col] = value
        save_assumptions_register(df)
        st.success(f"{group}: {len(updated_values)} assumption(s) saved for {case} case.")

    if reset_clicked:
        # Reset this group's values for selected case back to base (or some reference)
        # Strategy: copy base_value into low/high for current group depending on case
        base_col = "base_value"
        for _, row in group_df.iterrows():
            key = row["item_key"]
            mask = df["item_key"] == key
            df.loc[mask, case_col] = df.loc[mask, base_col]
        save_assumptions_register(df)
        st.warning(f"{group}: reset {case} values back to base defaults.")


def _render_assumption_widget(row: pd.Series, case_col: str) -> float:
    """Render a single slider/number input for one assumption row and return new value."""
    key = row["item_key"]
    label = row["item_name"]
    help_text = row.get("description", "")
    control = row.get("ui_control", "number_input")

    # Current case-specific value; fall back to base_value if NaN
    current = row.get(case_col)
    if pd.isna(current):
        current = row.get("base_value")

    # Bounds & step
    ui_min = row.get("ui_min")
    ui_max = row.get("ui_max")
    ui_step = row.get("ui_step")

    # Convert to appropriate numeric types
    # (assumes everything numeric here; you can add guards as needed)
    try:
        ui_min = float(ui_min)
        ui_max = float(ui_max)
    except (TypeError, ValueError):
        ui_min, ui_max = None, None

    try:
        ui_step = float(ui_step) if pd.notna(ui_step) else None
    except (TypeError, ValueError):
        ui_step = None

    if control == "slider" and ui_min is not None and ui_max is not None:
        value = st.slider(
            label,
            min_value=ui_min,
            max_value=ui_max,
            value=float(current),
            step=ui_step or (ui_max - ui_min) / 100.0,
            help=help_text,
            key=f"{key}_slider",
        )
    else:
        # Default to number_input if control is unknown or bounds missing
        kwargs = {}
        if ui_min is not None:
            kwargs["min_value"] = ui_min
        if ui_max is not None:
            kwargs["max_value"] = ui_max
        if ui_step is not None:
            kwargs["step"] = ui_step

        value = st.number_input(
            label,
            value=float(current),
            help=help_text,
            key=f"{key}_num",
            **kwargs,
        )

    # Optional: small caption under each control for context
    st.caption(f"Key: `{key}` • Units: {row.get('unit','')}")
    return float(value)
