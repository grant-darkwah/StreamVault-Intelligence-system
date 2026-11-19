import streamlit as st
from dashboard.data import DashboardDataError, load_dashboard_data
from dashboard.pages.overview import render_overview

st.set_page_config(
    page_title="StreamVault Intelligence",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_theme():
    """Load the custom dashboard stylesheet."""

    from pathlib import Path

    theme_path = Path("dashboard/styles/theme.css")

    if theme_path.exists():
        st.markdown(
            f"<style>{theme_path.read_text()}</style>",
            unsafe_allow_html=True,
        )


load_theme()

with st.sidebar:
    st.markdown("## 🎬 STREAMVAULT")
    st.caption("LICENSING INTELLIGENCE")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Executive Overview"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("DATA ENGINEERING HUB")
    st.caption("Decision Support · 2026")


try:
    data = load_dashboard_data()
except DashboardDataError as error:
    st.error(str(error))
    st.stop()

if page == "Executive Overview":
    render_overview(data)
