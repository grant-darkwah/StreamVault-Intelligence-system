import streamlit as st
from dashboard.data import DashboardDataError, load_dashboard_data
from dashboard.pages.deal_assessment import render_deal_assessment
from dashboard.pages.franchises import render_franchises
from dashboard.pages.overview import render_overview
from dashboard.pages.standalone import render_standalone

# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="StreamVault | Licensing Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "StreamVault Licensing Intelligence — "
            "A data-driven content acquisition decision-support dashboard."
        ),
    },
)


# --------------------------------------------------
# CUSTOM THEME
# --------------------------------------------------


def load_theme():
    """Load the custom dashboard stylesheet."""
    from pathlib import Path

    theme_path = Path("dashboard/styles/theme.css")

    if theme_path.exists():
        css = theme_path.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )


load_theme()


# --------------------------------------------------
# PAGE REGISTRY
# --------------------------------------------------

pages = {
    "Executive Overview": render_overview,
    "Franchise Opportunities": render_franchises,
    "Standalone Films": render_standalone,
    "Deal Assessment": render_deal_assessment,
}


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🎬 STREAMVAULT")
    st.caption("CONTENT LICENSING INTELLIGENCE")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        options=list(pages.keys()),
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("DATA ENGINEERING HUB")
    st.caption("Decision Support · 2026")


# --------------------------------------------------
# LOAD ANALYTICAL DATA
# --------------------------------------------------

try:
    data = load_dashboard_data()

except DashboardDataError as error:
    st.error(f"Dashboard data could not be loaded: {error}")
    st.stop()

except Exception as error:  # noqa: BLE001
    st.error(f"An unexpected application error occurred: {error}")
    st.stop()


# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------

pages[page](data)
