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

from config import PAGE_ROUTES
from layout import inject_css


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
    page_names = list(PAGE_ROUTES.keys())
    selected_page = st.sidebar.selectbox("Select a page", page_names)

    # Render selected page
    module_name = PAGE_ROUTES[selected_page]
    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by Fractional CFO Services")
    st.sidebar.caption("Version 1.0")
    if module_name is None:
        st.title(selected_page)
        st.info("This section is under development. Check back soon!")
    else:
        page_module = importlib.import_module(f"pages.{module_name}")
        # Each page module should expose a ``render`` function
        if hasattr(page_module, "render"):
            page_module.render()
        else:
            st.error(f"Page '{selected_page}' is missing a render() function.")


if __name__ == "__main__":
    main()
