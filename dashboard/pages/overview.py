import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components import (
    render_data_notice,
    render_featured_film,
    render_franchise_card,
    render_kpi,
    render_movie_card,
    render_page_header,
    render_section_header,
)
from dashboard.data import get_data_summary


def render_overview(data: dict):
    """Render the StreamVault executive acquisition dashboard."""

    films = data["films"]

    franchises = data["franchise_all"].head(5).copy()

    standalone = data["standalone_all"].head(5).copy()

    summary = get_data_summary(data)

    # --------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------

    render_page_header(
        "Executive Overview",
        "CONTENT ACQUISITION INTELLIGENCE / $14M LICENSING DECISION",
    )

    # --------------------------------------------------
    # FEATURED ACQUISITION
    # --------------------------------------------------

    render_section_header(
        "Featured acquisition",
        "Current highest-ranked franchise opportunity",
    )

    avengers = films.loc[
        films["collection_name"].str.contains(
            "Avengers",
            case=False,
            na=False,
        )
    ].copy()

    if not avengers.empty:
        featured = (
            avengers.sort_values(
                "revenue",
                ascending=False,
                na_position="last",
            )
            .iloc[0]
            .to_dict()
        )

        render_featured_film(
            featured,
            "TOP-RANKED FRANCHISE · AVENGERS",
        )

    else:
        st.warning("Avengers collection artwork is unavailable.")

    # --------------------------------------------------
    # PORTFOLIO KPIs
    # --------------------------------------------------

    st.markdown("### Portfolio performance")

    kpis = [
        ("Analysed titles", summary["analysed_titles"]),
        ("Franchise collections", summary["franchise_collections"]),
        ("Standalone candidates", summary["standalone_titles"]),
        ("Valid candidate IDs", summary["unique_valid_ids"]),
        ("Unretrieved IDs", summary["unretrieved_valid_ids"]),
    ]

    columns = st.columns(5)

    for column, (label, value) in zip(columns, kpis):
        with column:
            render_kpi(
                label,
                f"{value:,}",
            )

    st.divider()

    # --------------------------------------------------
    # FRANCHISE OPPORTUNITIES
    # --------------------------------------------------

    render_section_header(
        "Franchise opportunities",
        "Top five collections ranked by composite score. "
        "Artwork represents the highest-revenue sampled film "
        "within each collection.",
    )

    franchise_columns = st.columns(5)

    for rank, (_, collection) in enumerate(
        franchises.iterrows(),
        start=1,
    ):
        with franchise_columns[rank - 1]:
            render_franchise_card(
                collection.to_dict(),
                rank,
                films,
            )

    st.divider()

    # --------------------------------------------------
    # STANDALONE OPPORTUNITIES
    # --------------------------------------------------

    render_section_header(
        "Standalone opportunities",
        "Top individual titles ranked by audience and financial indicators.",
    )

    movie_columns = st.columns(5)

    for column, (_, film) in zip(
        movie_columns,
        standalone.iterrows(),
    ):
        with column:
            render_movie_card(
                film.to_dict(),
                film["composite_score"],
            )

    st.divider()

    # --------------------------------------------------
    # FINANCIAL PERFORMANCE
    # --------------------------------------------------

    render_section_header(
        "Financial performance",
        "Median reported budgets and revenues by release period.",
    )

    financial = films.copy()

    financial["release_period"] = pd.NA

    financial.loc[
        financial["release_year"] < 2000,
        "release_period",
    ] = "Pre-2000"

    financial.loc[
        financial["release_year"] >= 2000,
        "release_period",
    ] = "2000 onward"

    financial = financial.dropna(
        subset=[
            "release_period",
            "budget",
            "revenue",
        ]
    )

    period_summary = (
        financial.groupby("release_period")
        .agg(
            titles=("movie_id", "nunique"),
            median_budget=("budget", "median"),
            median_revenue=("revenue", "median"),
        )
        .reset_index()
    )

    chart_data = period_summary.melt(
        id_vars=["release_period"],
        value_vars=[
            "median_budget",
            "median_revenue",
        ],
        var_name="Financial metric",
        value_name="Amount",
    )

    chart_data["Financial metric"] = chart_data["Financial metric"].map(
        {
            "median_budget": "Median budget",
            "median_revenue": "Median revenue",
        }
    )

    fig = px.bar(
        chart_data,
        x="release_period",
        y="Amount",
        color="Financial metric",
        barmode="group",
        text_auto=".3s",
        template="plotly_dark",
        labels={
            "release_period": "Release period",
            "Amount": "Reported USD",
        },
        color_discrete_map={
            "Median budget": "#6478F5",
            "Median revenue": "#36C6B3",
        },
        hover_data={
            "Amount": ":$,.0f",
        },
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=430,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        margin={
            "l": 20,
            "r": 20,
            "t": 35,
            "b": 20,
        },
        yaxis={
            "tickprefix": "$",
            "tickformat": "~s",
            "rangemode": "tozero",
            "gridcolor": "rgba(145,161,184,0.15)",
        },
        xaxis={
            "showgrid": False,
        },
        font={
            "color": "#E8EEF7",
        },
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.caption(
        "Historical figures are not inflation-adjusted or "
        "currency-normalized. Revenue is not profit or licensing ROI."
    )

    st.divider()

    # --------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------

    render_section_header(
        "Data integrity",
        "Candidate reconciliation and extraction coverage.",
    )

    quality_metrics = [
        ("Candidate records", summary["candidate_records"]),
        ("Invalid records", summary["invalid_records"]),
        ("Duplicate excess", summary["duplicate_excess"]),
        ("Unretrieved valid IDs", summary["unretrieved_valid_ids"]),
    ]

    quality_columns = st.columns(4)

    for column, (label, value) in zip(
        quality_columns,
        quality_metrics,
    ):
        with column:
            column.metric(
                label,
                f"{value:,}",
            )

    render_data_notice(
        "Acquisition rankings are screening indicators, not "
        "investment returns. Licensing prices, contractual rights, "
        "bundle contents, territories, and streaming performance "
        "remain unverified.",
        level="warning",
    )
