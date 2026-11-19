import pandas as pd
import streamlit as st

from dashboard.components import (
    render_page_header,
    render_section_header,
)
from dashboard.metrics import get_poster_url


def render_talent(data: dict) -> None:
    """Render director and lead-cast insights for shortlisted films."""
    films = data["films"].copy()
    cast = data["cast"].copy()
    crew = data["crew"].copy()
    standalone = data["standalone_all"].head(5).copy()

    render_page_header(
        "Talent Insights",
        "Directors and lead performers across the strongest standalone titles.",
    )

    shortlist_ids = standalone["movie_id"].tolist()
    shortlist = films[films["movie_id"].isin(shortlist_ids)].copy()

    if shortlist.empty:
        st.warning("No shortlisted films are available.")
        return

    shortlist["display_title"] = shortlist["title"].fillna("Untitled")
    shortlist = shortlist.sort_values("release_year", ascending=False)

    selected_title = st.selectbox(
        "Explore a shortlisted film",
        shortlist["display_title"].tolist(),
        key="talent_film_selector",
    )
    selected = shortlist.loc[shortlist["display_title"] == selected_title].iloc[0]

    movie_id = selected["movie_id"]

    directors = crew[
        (crew["movie_id"] == movie_id) & (crew["job"].str.lower() == "director")
    ].copy()

    lead_cast = cast[cast["movie_id"] == movie_id].copy()
    lead_cast = lead_cast.sort_values("order").head(3)

    left, right = st.columns([1, 2], gap="large")

    with left:
        poster_url = get_poster_url(selected.get("poster_path"))
        if poster_url:
            st.image(poster_url, use_container_width=True)
        else:
            st.info("Poster artwork unavailable.")

    with right:
        st.subheader(selected_title)
        year = selected.get("release_year")
        st.caption(str(int(year)) if pd.notna(year) else "Release year unavailable")

        render_section_header("Director")
        if directors.empty:
            st.info("Director credit unavailable in the retrieved data.")
        else:
            for _, director in directors.iterrows():
                st.markdown(f"**{director['name']}**")

        render_section_header("Lead cast")
        if lead_cast.empty:
            st.info("Lead cast credits unavailable.")
        else:
            for _, person in lead_cast.iterrows():
                st.markdown(
                    f"**{int(person['order']) + 1}. {person['name']}**"
                    f" — {person.get('character') or 'Role not listed'}"
                )

    st.divider()
    render_section_header("Recurring talent across the shortlist")

    shortlist_cast = cast[cast["movie_id"].isin(shortlist_ids)].copy()
    shortlist_crew = crew[crew["movie_id"].isin(shortlist_ids)].copy()

    director_counts = (
        shortlist_crew[shortlist_crew["job"].str.lower() == "director"]
        .groupby("name")["movie_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    cast_counts = (
        shortlist_cast[shortlist_cast["order"] <= 2]
        .groupby("name")["movie_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("**Directors**")
        if director_counts.empty:
            st.info("No director credits available.")
        else:
            st.dataframe(
                director_counts.rename("Shortlisted films").reset_index(),
                hide_index=True,
                use_container_width=True,
            )

    with col2:
        st.markdown("**Lead performers**")
        if cast_counts.empty:
            st.info("No lead-cast credits available.")
        else:
            st.dataframe(
                cast_counts.rename("Shortlisted films").reset_index().head(10),
                hide_index=True,
                use_container_width=True,
            )

    st.caption(
        "Talent frequency is descriptive of this candidate sample. "
        "It does not establish that a director or performer caused commercial success."
    )
