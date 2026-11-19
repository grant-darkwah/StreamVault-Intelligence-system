import pandas as pd
import streamlit as st

from dashboard.components import (
    render_page_header,
    render_section_header,
)
from dashboard.metrics import format_currency, get_poster_url


def render_franchises(data: dict):
    """Render franchise acquisition opportunities."""

    films = data["films"]
    rankings = data["franchise_all"].copy()
    recent = data["franchise_recent"].copy()

    render_page_header(
        "Franchise Opportunities",
        "FRANCHISE PORTFOLIO | ACQUISITION PRIORITIES",
    )

    render_section_header(
        "Leading franchise opportunities",
        "The three highest-ranked collections identified by the analysis.",
    )

    top_three = rankings.head(3)
    columns = st.columns(3)

    for rank, (_, franchise) in enumerate(top_three.iterrows(), start=1):
        collection_films = films.loc[
            films["collection_id"].eq(franchise["collection_id"])
        ].copy()

        representative = None

        if not collection_films.empty:
            representative = collection_films.sort_values(
                "revenue",
                ascending=False,
                na_position="last",
            ).iloc[0]

        with columns[rank - 1], st.container(border=True):
            st.caption(f"PRIORITY #{rank}")

            if representative is not None:
                poster = get_poster_url(representative.get("poster_path"))
                if poster:
                    st.image(poster, use_container_width=True)

            st.markdown(f"**{franchise['collection_name']}**")

            st.metric(
                "Sampled films",
                int(franchise["sampled_titles"]),
            )

            rating = franchise["median_rating"]
            revenue = franchise["median_revenue"]

            st.metric(
                "Audience rating",
                f"{rating:.1f}/10" if pd.notna(rating) else "N/A",
            )

            st.metric(
                "Reported revenue",
                format_currency(revenue) if pd.notna(revenue) else "N/A",
            )

    st.divider()

    render_section_header(
        "Explore a franchise",
        "Select a collection to inspect its sampled titles and performance.",
    )

    names = rankings["collection_name"].dropna().tolist()

    if not names:
        st.warning("No franchise rankings are available.")
        return

    selected_name = st.selectbox(
        "Select franchise",
        names,
        key="franchise_detail_selection",
    )

    selected = rankings.loc[rankings["collection_name"].eq(selected_name)].iloc[0]

    selected_films = films.loc[
        films["collection_id"].eq(selected["collection_id"])
    ].copy()

    selected_films = selected_films.sort_values(
        "release_year",
        na_position="last",
    )

    left, right = st.columns([1, 2], gap="large")

    with left:
        if not selected_films.empty:
            featured = selected_films.sort_values(
                "revenue",
                ascending=False,
                na_position="last",
            ).iloc[0]

            poster = get_poster_url(featured.get("poster_path"))

            if poster:
                st.image(poster, use_container_width=True)

    with right:
        st.markdown(f"### {selected_name}")

        metric_columns = st.columns(3)

        with metric_columns[0]:
            st.metric(
                "Sampled titles",
                int(selected["sampled_titles"]),
            )

        with metric_columns[1]:
            rating = selected["median_rating"]
            st.metric(
                "Audience rating",
                f"{rating:.1f}/10" if pd.notna(rating) else "N/A",
            )

        with metric_columns[2]:
            revenue = selected["median_revenue"]
            st.metric(
                "Reported revenue",
                format_currency(revenue) if pd.notna(revenue) else "N/A",
            )

        st.caption(
            "Collection metrics are calculated from the sampled "
            "films available in the candidate dataset."
        )

    if not selected_films.empty:
        st.markdown("#### Films in this collection")

        display = selected_films[
            [
                "title",
                "release_year",
                "vote_average",
                "vote_count",
                "revenue",
            ]
        ].copy()

        display = display.rename(
            columns={
                "title": "Film",
                "release_year": "Release year",
                "vote_average": "Audience rating",
                "vote_count": "Audience votes",
                "revenue": "Reported revenue",
            }
        )

        display["Reported revenue"] = display["Reported revenue"].apply(format_currency)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    render_section_header(
        "All-years versus recent rankings",
        "Check whether leading franchise recommendations change "
        "when restricting the analysis to films released from 2000 onward.",
    )

    comparison = []

    for rank in range(min(5, len(rankings), len(recent))):
        comparison.append(
            {
                "Rank": rank + 1,
                "All years": rankings.iloc[rank]["collection_name"],
                "2000 onward": recent.iloc[rank]["collection_name"],
            }
        )

    st.dataframe(
        pd.DataFrame(comparison),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Rankings are screening indicators based on audience and "
        "reported financial metrics. They do not establish licensing value."
    )
