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
from dashboard.metrics import (
    format_currency,
    get_poster_url,
)


def render_overview(data: dict):
    """Render the interactive StreamVault executive dashboard."""

    films = data["films"]

    franchises = data["franchise_all"].head(3).copy()
    standalone = data["standalone_all"].head(5).copy()

    summary = get_data_summary(data)

    # ==================================================
    # EXECUTIVE HEADER
    # ==================================================

    render_page_header(
        "StreamVault Executive Overview",
        "CONTENT LICENSING INTELLIGENCE  |  $14M INVESTMENT REVIEW",
    )

    # ==================================================
    # FEATURED FRANCHISE
    # ==================================================

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
            "LEADING FRANCHISE OPPORTUNITY  |  AVENGERS",
        )

        st.caption(
            "Avengers ranks first in the franchise analysis. "
            "The featured title represents one sampled film."
        )

    # ==================================================
    # EXECUTIVE KPIs
    # ==================================================

    render_section_header(
        "Portfolio at a glance",
        "An overview of the candidate catalogue and analysis coverage.",
    )

    coverage = (
        summary["analysed_titles"] / summary["unique_valid_ids"] * 100
        if summary["unique_valid_ids"]
        else 0
    )

    kpis = [
        ("Films analysed", f"{summary['analysed_titles']:,}"),
        ("Priority franchises", f"{len(franchises):,}"),
        ("Standalone opportunities", f"{len(standalone):,}"),
        ("Candidate coverage", f"{coverage:.1f}%"),
    ]

    columns = st.columns(4)

    for column, (label, value) in zip(columns, kpis):
        with column:
            render_kpi(label, value)

    st.divider()

    # ==================================================
    # PRIORITY FRANCHISES
    # ==================================================

    render_section_header(
        "Priority franchise opportunities",
        "Three leading collections ranked by audience and "
        "reported financial indicators.",
    )

    franchise_columns = st.columns(3)

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

    # ==================================================
    # STANDALONE FILMS
    # ==================================================

    render_section_header(
        "Top standalone films",
        "Leading individual titles identified by the analysis.",
    )

    movie_columns = st.columns(5)

    for column, (_, film) in zip(
        movie_columns,
        standalone.iterrows(),
    ):
        with column:
            render_movie_card(film.to_dict())

    st.divider()

    # ==================================================
    # FINANCIAL PERFORMANCE
    # ==================================================

    render_section_header(
        "Financial performance",
        "Compare typical reported production budgets and revenues "
        "across film release periods.",
    )

    financial = films.copy()

    financial["release_period"] = pd.NA

    financial.loc[
        financial["release_year"] < 2000,
        "release_period",
    ] = "Before 2000"

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
        .reindex(["Before 2000", "2000 onward"])
        .dropna(
            subset=[
                "median_budget",
                "median_revenue",
            ]
        )
        .reset_index()
    )

    if not period_summary.empty:
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
                "median_budget": "Typical production budget",
                "median_revenue": "Typical reported revenue",
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
                "release_period": "Film release period",
                "Amount": "Reported USD",
            },
            color_discrete_map={
                "Typical production budget": "#6478F5",
                "Typical reported revenue": "#36C6B3",
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
            height=390,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title_text="",
            bargap=0.35,
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
            "Figures represent medians. Historical amounts are not "
            "inflation-adjusted or currency-normalized. Revenue is "
            "not profit or licensing ROI."
        )

    st.divider()

    # ==================================================
    # INTERACTIVE OPPORTUNITY EXPLORER
    # ==================================================

    render_section_header(
        "Explore the opportunities",
        "Select a franchise, individual film, or release period "
        "to explore its performance.",
    )

    franchise_tab, standalone_tab, financial_tab = st.tabs(
        [
            "🏆 Franchise explorer",
            "🎬 Film explorer",
            "📊 Financial explorer",
        ]
    )

    # --------------------------------------------------
    # FRANCHISE EXPLORER
    # --------------------------------------------------

    with franchise_tab:
        franchise_options = data["franchise_all"].head(3).copy()

        franchise_names = franchise_options["collection_name"].tolist()

        if franchise_names:
            selected_franchise_name = st.selectbox(
                "Select a franchise",
                franchise_names,
                key="selected_franchise",
            )

            selected_franchise = franchise_options.loc[
                franchise_options["collection_name"].eq(selected_franchise_name)
            ].iloc[0]

            collection_films = films.loc[
                films["collection_id"].eq(selected_franchise["collection_id"])
            ].copy()

            representative = None

            if not collection_films.empty:
                representative = collection_films.sort_values(
                    "revenue",
                    ascending=False,
                    na_position="last",
                ).iloc[0]

            image_column, details_column = st.columns(
                [1, 2],
                gap="large",
            )

            with image_column:
                if representative is not None:
                    poster_url = get_poster_url(representative.get("poster_path"))

                    if poster_url:
                        st.image(
                            poster_url,
                            use_container_width=True,
                        )
                    else:
                        st.info("Poster unavailable")

            with details_column:
                st.markdown(f"### {selected_franchise_name}")

                st.caption("PRIORITY FRANCHISE OPPORTUNITY")

                metric1, metric2, metric3 = st.columns(3)

                with metric1:
                    st.metric(
                        "Sampled films",
                        int(selected_franchise["sampled_titles"]),
                    )

                with metric2:
                    rating = selected_franchise["median_rating"]

                    st.metric(
                        "Audience rating",
                        f"{rating:.1f}/10" if pd.notna(rating) else "N/A",
                    )

                with metric3:
                    revenue = selected_franchise["median_revenue"]

                    st.metric(
                        "Reported revenue",
                        format_currency(revenue) if pd.notna(revenue) else "N/A",
                    )

                if representative is not None:
                    st.caption(f"Featured sampled title: {representative['title']}")

                st.info(
                    "This collection is one of the three highest-ranked "
                    "franchise opportunities. The sampled titles are "
                    "not necessarily the complete licensing bundle."
                )

    # --------------------------------------------------
    # STANDALONE FILM EXPLORER
    # --------------------------------------------------

    with standalone_tab:
        standalone_options = data["standalone_all"].head(5).copy()

        film_names = standalone_options["title"].tolist()

        if film_names:
            selected_film_name = st.selectbox(
                "Select a film",
                film_names,
                key="selected_standalone_film",
            )

            selected_film = standalone_options.loc[
                standalone_options["title"].eq(selected_film_name)
            ].iloc[0]

            image_column, details_column = st.columns(
                [1, 2],
                gap="large",
            )

            with image_column:
                poster_url = get_poster_url(selected_film.get("poster_path"))

                if poster_url:
                    st.image(
                        poster_url,
                        use_container_width=True,
                    )

                else:
                    st.info("Poster unavailable")

            with details_column:
                st.markdown(f"### {selected_film['title']}")

                st.caption(
                    f"STANDALONE OPPORTUNITY  |  {selected_film['release_year']}"
                )

                metric1, metric2 = st.columns(2)

                with metric1:
                    rating = selected_film["vote_average"]

                    st.metric(
                        "Audience rating",
                        f"{rating:.1f}/10" if pd.notna(rating) else "N/A",
                    )

                with metric2:
                    votes = selected_film["vote_count"]

                    st.metric(
                        "Audience votes",
                        f"{int(votes):,}" if pd.notna(votes) else "N/A",
                    )

                revenue = selected_film["revenue"]

                st.metric(
                    "Reported revenue",
                    format_currency(revenue) if pd.notna(revenue) else "N/A",
                )

                st.info(
                    "This title is among the five leading standalone "
                    "opportunities. Audience engagement and reported "
                    "financial performance are screening indicators, "
                    "not guaranteed streaming returns."
                )

    # --------------------------------------------------
    # FINANCIAL PERIOD EXPLORER
    # --------------------------------------------------

    with financial_tab:
        available_periods = period_summary["release_period"].tolist()

        if available_periods:
            selected_period_name = st.radio(
                "Choose a release period",
                available_periods,
                horizontal=True,
                key="selected_financial_period",
            )

            selected_period = period_summary.loc[
                period_summary["release_period"].eq(selected_period_name)
            ].iloc[0]

            metric1, metric2, metric3 = st.columns(3)

            with metric1:
                st.metric(
                    "Films analysed",
                    f"{int(selected_period['titles']):,}",
                )

            with metric2:
                st.metric(
                    "Typical production budget",
                    format_currency(selected_period["median_budget"]),
                )

            with metric3:
                st.metric(
                    "Typical reported revenue",
                    format_currency(selected_period["median_revenue"]),
                )

            comparison_chart = pd.DataFrame(
                {
                    "Financial measure": [
                        "Production budget",
                        "Reported revenue",
                    ],
                    "Amount": [
                        selected_period["median_budget"],
                        selected_period["median_revenue"],
                    ],
                }
            )

            comparison_fig = px.bar(
                comparison_chart,
                x="Amount",
                y="Financial measure",
                orientation="h",
                text_auto=".3s",
                template="plotly_dark",
                color="Financial measure",
                color_discrete_map={
                    "Production budget": "#6478F5",
                    "Reported revenue": "#36C6B3",
                },
            )

            comparison_fig.update_layout(
                height=260,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin={
                    "l": 10,
                    "r": 20,
                    "t": 20,
                    "b": 20,
                },
                xaxis={
                    "tickprefix": "$",
                    "tickformat": "~s",
                    "gridcolor": "rgba(145,161,184,0.15)",
                },
                yaxis={
                    "showgrid": False,
                },
                font={
                    "color": "#E8EEF7",
                },
            )

            st.plotly_chart(
                comparison_fig,
                use_container_width=True,
            )

            st.caption(
                "The chart compares median reported production "
                "budgets and revenues. These are not profit or "
                "investment-return estimates."
            )

    st.divider()

    # ==================================================
    # EXECUTIVE INSIGHTS
    # ==================================================

    render_section_header(
        "What the analysis tells us",
        "The strongest findings across the candidate catalogue.",
    )

    franchise_all = data["franchise_all"].head(3).reset_index(drop=True)

    franchise_recent = data["franchise_recent"].head(3).reset_index(drop=True)

    standalone_all = data["standalone_all"].head(3).reset_index(drop=True)

    standalone_recent = data["standalone_recent"].head(3).reset_index(drop=True)

    franchise_stable = (
        franchise_all["collection_name"].tolist()
        == franchise_recent["collection_name"].tolist()
    )

    standalone_stable = (
        standalone_all["title"].tolist() == standalone_recent["title"].tolist()
    )

    insight_columns = st.columns(3)

    with insight_columns[0], st.container(border=True):
        st.markdown("🏆 **FRANCHISE OPPORTUNITIES**")

        st.metric(
            "Leading recommendations retained",
            "3 of 3" if franchise_stable else "Ranking changes",
        )

        for title in franchise_all["collection_name"]:
            st.write(f"• {title}")

        st.caption(
            "The top three retain their order across both release-period analyses."
            if franchise_stable
            else "The leading franchise order changes between periods."
        )

    with insight_columns[1], st.container(border=True):
        st.markdown("🎬 **STANDALONE OPPORTUNITIES**")

        st.metric(
            "Leading recommendations retained",
            "3 of 3" if standalone_stable else "Ranking changes",
        )

        for title in standalone_all["title"]:
            st.write(f"• {title}")

        st.caption(
            "The top three retain their order across both release-period analyses."
            if standalone_stable
            else "The leading standalone order changes between periods."
        )

    with insight_columns[2], st.container(border=True):
        st.markdown("📊 **FINANCIAL CONTEXT**")

        recent_period = period_summary.loc[
            period_summary["release_period"].eq("2000 onward")
        ]

        if not recent_period.empty:
            recent_revenue = recent_period.iloc[0]["median_revenue"]

            st.metric(
                "Typical reported revenue",
                format_currency(recent_revenue),
            )

            st.caption("Median reported revenue for films released from 2000 onward.")

        else:
            st.metric(
                "Financial comparison",
                "Unavailable",
            )

    st.divider()

    # ==================================================
    # COMMERCIAL DUE DILIGENCE
    # ==================================================

    render_section_header(
        "Before committing the $14M",
        "Five commercial questions that must be answered "
        "before approving a licensing agreement.",
    )

    diligence_items = [
        (
            "01",
            "Acquisition price",
            ("What is the actual cost of each franchise bundle and standalone title?"),
        ),
        (
            "02",
            "Rights and exclusivity",
            (
                "Do the agreements include the required streaming "
                "rights and exclusivity?"
            ),
        ),
        (
            "03",
            "Territory and licensing window",
            (
                "Which countries are covered, and how long will "
                "the content remain available?"
            ),
        ),
        (
            "04",
            "Bundle contents",
            ("Which exact films are included in each franchise package?"),
        ),
        (
            "05",
            "Expected commercial return",
            (
                "What evidence supports audience demand, subscriber "
                "impact, and expected revenue?"
            ),
        ),
    ]

    for number, heading, description in diligence_items:
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.6, 2.2, 6])

            with col1:
                st.markdown(f"### {number}")

            with col2:
                st.markdown(f"**{heading}**")

            with col3:
                st.write(description)

    render_data_notice(
        "The analysis identifies promising acquisition opportunities "
        "for further diligence. It does not establish that any "
        "opportunity is worth a specific purchase price or that "
        "the $14M budget will generate a positive return. "
        "Final approval requires verified licensing terms "
        "and commercial forecasts.",
        level="warning",
    )
