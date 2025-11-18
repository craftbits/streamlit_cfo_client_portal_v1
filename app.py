"""
Main entry point for the CFO portal Streamlit app.

This module wires together the navigation sidebar, global state, and
page rendering. It reads the page routes defined in
``config.PAGE_ROUTES``, dynamically imports the corresponding page
modules, and executes their ``render`` function. Unimplemented pages
display a simple placeholder message.

Run this script with ``streamlit run app.py`` to launch the portal.
"""
from __future__ import annotations

import importlib
import streamlit as st

from config import PAGE_ROUTES, NAV_SECTIONS, PAGE_MODULE_PACKAGE
from layout import inject_css


def _build_section_map() -> dict[str, list[str]]:
    """Return an ordered mapping of sections to the pages they contain."""
    section_map: dict[str, list[str]] = {}
    for section, pages in NAV_SECTIONS:
        valid_pages = [page for page in pages if page in PAGE_ROUTES]
        if valid_pages:
            section_map[section] = valid_pages
    return section_map


def _default_selection(section_map: dict[str, list[str]]) -> tuple[str, str]:
    """Determine the default section/page combination."""
    for section, pages in NAV_SECTIONS:
        if section in section_map:
            return section, section_map[section][0]
    raise ValueError("No pages configured in NAV_SECTIONS.")


def main() -> None:
    # Set global page config. Only call once.
    st.set_page_config(
        page_title="Supermarket CFO Portal",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject CSS for consistent styling
    inject_css()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    section_map = _build_section_map()
    if not section_map:
        st.sidebar.error("No navigation routes are configured.")
        return
    default_section, _default_page = _default_selection(section_map)
    if "nav_section" not in st.session_state:
        st.session_state["nav_section"] = default_section
    section = st.sidebar.selectbox("Section", list(section_map.keys()), key="nav_section")
    pages_for_section = section_map[section]
    page_state_key = "nav_page"
    if (
        page_state_key not in st.session_state
        or st.session_state.get("nav_page_section") != section
        or st.session_state[page_state_key] not in pages_for_section
    ):
        st.session_state[page_state_key] = pages_for_section[0]
    st.session_state["nav_page_section"] = section
    selected_page = st.sidebar.radio("Page", pages_for_section, key=page_state_key)

    # Render selected page
    module_name = PAGE_ROUTES[selected_page]
    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by Fractional CFO Services")
    st.sidebar.caption("Version 1.0")
    if module_name is None:
        st.title(selected_page)
        st.info("This section is under development. Check back soon!")
    else:
        page_module = importlib.import_module(f"{PAGE_MODULE_PACKAGE}.{module_name}")
        # Each page module should expose a ``render`` function
        if hasattr(page_module, "render"):
            page_module.render()
        else:
            st.error(f"Page '{selected_page}' is missing a render() function.")


if __name__ == "__main__":
    main()
