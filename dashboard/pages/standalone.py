import pandas as pd
import streamlit as st

from dashboard.components import (
    render_page_header,
    render_section_header,
)
from dashboard.metrics import format_currency, get_poster_url


def render_standalone(data: dict):
    """Render standalone film acquisition opportunities."""

    films = data["standalone_all"].copy()
    recent = data["standalone_recent"].copy()

    render_page_header(
        "Standalone Film Opportunities",
        "INDIVIDUAL TITLE PORTFOLIO | ACQUISITION PRIORITIES",
    )

    render_section_header(
        "Top five standalone candidates",
        "The highest-ranked individual films across all release years.",
    )

    top_five = films.head(5)

    columns = st.columns(5)

    for rank, (_, film) in enumerate(top_five.iterrows(), start=1):
        with columns[rank - 1], st.container(border=True):
            st.caption(f"RANK #{rank}")

            poster = get_poster_url(film.get("poster_path"))

            if poster:
                st.image(
                    poster,
                    use_container_width=True,
                )
            else:
                st.caption("Poster unavailable")

            st.markdown(f"**{film['title']}**")

            rating = film["vote_average"]

            st.caption(
                f"{film['release_year']} · Rating {rating:.1f}/10"
                if pd.notna(rating)
                else f"{film['release_year']} · Rating unavailable"
            )

            st.caption(f"Revenue: {format_currency(film['revenue'])}")

    st.divider()

    render_section_header(
        "Explore a standalone title",
        "Select a film to inspect its audience and financial indicators.",
    )

    film_names = films["title"].dropna().tolist()

    if not film_names:
        st.warning("No standalone film rankings are available.")
        return

    selected_name = st.selectbox(
        "Choose a film",
        film_names,
        key="standalone_detail_selection",
    )

    selected = films.loc[films["title"].eq(selected_name)].iloc[0]

    image_column, detail_column = st.columns(
        [1, 2],
        gap="large",
    )

    with image_column:
        poster = get_poster_url(selected.get("poster_path"))

        if poster:
            st.image(
                poster,
                use_container_width=True,
            )
        else:
            st.info("Poster unavailable")

    with detail_column:
        st.markdown(f"## {selected['title']}")

        st.caption(f"STANDALONE OPPORTUNITY · {selected['release_year']}")

        metric_columns = st.columns(3)

        with metric_columns[0]:
            rating = selected["vote_average"]

            st.metric(
                "Audience rating",
                f"{rating:.1f}/10" if pd.notna(rating) else "N/A",
            )

        with metric_columns[1]:
            votes = selected["vote_count"]

            st.metric(
                "Audience votes",
                f"{int(votes):,}" if pd.notna(votes) else "N/A",
            )

        with metric_columns[2]:
            popularity = selected["popularity"]

            st.metric(
                "Popularity indicator",
                f"{popularity:.1f}" if pd.notna(popularity) else "N/A",
            )

        st.metric(
            "Reported revenue",
            format_currency(selected["revenue"]),
        )

        st.metric(
            "Reported production budget",
            format_currency(selected["budget"]),
        )

        ratio = selected.get("revenue_budget_ratio")

        if pd.notna(ratio):
            st.metric(
                "Reported revenue-to-budget ratio",
                f"{ratio:.2f}×",
            )

        st.caption(
            "The revenue-to-budget ratio excludes marketing, "
            "distribution, licensing, and other costs. "
            "It is not profit or ROI."
        )

        homepage = selected.get("homepage")

        if isinstance(homepage, str) and homepage.startswith("https://"):
            st.link_button(
                "Visit official film website",
                homepage,
            )

    st.divider()

    render_section_header(
        "All-years versus recent rankings",
        "Compare the leading individual titles against the 2000-onward analysis.",
    )

    comparison = []

    for rank in range(min(5, len(films), len(recent))):
        comparison.append(
            {
                "Rank": rank + 1,
                "All years": films.iloc[rank]["title"],
                "2000 onward": recent.iloc[rank]["title"],
            }
        )

    st.dataframe(
        pd.DataFrame(comparison),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Audience ratings, vote counts, popularity, and reported "
        "revenue are screening indicators, not guaranteed streaming demand."
    )
