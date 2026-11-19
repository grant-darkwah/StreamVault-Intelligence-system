import html

import pandas as pd
import streamlit as st

from dashboard.metrics import (
    format_currency,
    get_backdrop_url,
    get_poster_url,
)


def render_page_header(title: str, subtitle: str):
    """Render a consistent executive dashboard heading."""

    st.markdown(f"# {title}")
    st.caption(subtitle)
    st.divider()


def render_section_header(title: str, description: str = ""):
    """Render a consistent section heading."""

    st.subheader(title)

    if description:
        st.caption(description)


def render_kpi(label: str, value: str, delta: str | None = None):
    """Render a polished KPI card."""

    st.metric(
        label=label,
        value=value,
        delta=delta,
        border=True,
    )


def render_data_notice(message: str, level: str = "info"):
    """Render a consistent information or risk notice."""

    if level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def render_dataframe(data, height: int = 420):
    """Render a standardized analytical table."""

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        height=height,
    )


def render_featured_film(
    film: dict,
    label: str = "FEATURED OPPORTUNITY",
):
    """Render a cinematic featured-film banner."""

    backdrop_url = get_backdrop_url(film.get("backdrop_path"))

    if not backdrop_url:
        st.info(f"Featured title: {film.get('title', 'Untitled')}")
        return

    title = html.escape(str(film.get("title", "Untitled")))

    label = html.escape(label)

    year = film.get("release_year", "N/A")
    rating = film.get("vote_average")

    rating_text = f"{float(rating):.1f}/10" if pd.notna(rating) else "N/A"

    revenue = format_currency(film.get("revenue") or 0)

    banner = (
        f'<div style="'
        f"background-image:linear-gradient("
        f"90deg,rgba(8,14,27,.97),rgba(8,14,27,.25)),"
        f"url(&quot;{backdrop_url}&quot;);"
        f"background-position:center;"
        f"background-size:cover;"
        f"background-repeat:no-repeat;"
        f"border:1px solid #263650;"
        f"border-radius:16px;"
        f"padding:42px;"
        f"min-height:280px;"
        f"display:flex;"
        f"flex-direction:column;"
        f'justify-content:center;">'
        f'<div style="color:#36c6b3;'
        f"font-size:11px;"
        f"font-weight:800;"
        f'letter-spacing:2px;">'
        f"{label}</div>"
        f'<div style="color:white;'
        f"font-size:38px;"
        f"font-weight:800;"
        f"margin-top:14px;"
        f'line-height:1.15;">'
        f"{title}</div>"
        f'<div style="color:#e0e7f0;'
        f"font-size:14px;"
        f'margin-top:16px;">'
        f"{year} &nbsp;·&nbsp; "
        f"Audience rating {rating_text}"
        f" &nbsp;·&nbsp; "
        f"Reported revenue {revenue}"
        f"</div></div>"
    )

    st.markdown(
        banner,
        unsafe_allow_html=True,
    )


def render_movie_card(film: dict):
    """Render a stakeholder-friendly standalone film card."""

    poster_url = get_poster_url(film.get("poster_path"))

    with st.container(border=True):
        if poster_url:
            st.image(
                poster_url,
                use_container_width=True,
            )
        else:
            st.caption("Poster unavailable")

        st.markdown(f"**{film.get('title', 'Untitled')}**")

        year = film.get("release_year", "N/A")
        rating = film.get("vote_average")
        votes = film.get("vote_count")
        revenue = film.get("revenue")

        rating_text = f"{float(rating):.1f}/10" if pd.notna(rating) else "N/A"

        st.caption(f"{year} · Audience rating: {rating_text}")

        if pd.notna(votes):
            st.caption(f"{int(votes):,} audience votes")

        if pd.notna(revenue):
            st.caption(f"Reported revenue: {format_currency(revenue)}")


def render_franchise_card(
    collection: dict,
    rank: int,
    films: pd.DataFrame,
):
    """Render a visually consistent franchise opportunity card."""

    collection_id = collection.get("collection_id")

    collection_films = films.loc[films["collection_id"].eq(collection_id)].copy()

    representative = None

    if not collection_films.empty:
        collection_films = collection_films.sort_values(
            "revenue",
            ascending=False,
            na_position="last",
        )

        representative = collection_films.iloc[0]

    with st.container(border=True):
        st.caption(f"PRIORITY OPPORTUNITY #{rank}")

        if representative is not None:
            poster_url = get_poster_url(representative.get("poster_path"))

            if poster_url:
                st.image(
                    poster_url,
                    use_container_width=True,
                )
            else:
                st.caption("Poster unavailable")

            st.markdown(f"**{representative['title']}**")

        else:
            st.caption("Artwork unavailable")

        collection_name = collection.get(
            "collection_name",
            "Unnamed collection",
        )

        st.markdown(f"**{collection_name}**")

        sampled_titles = collection.get("sampled_titles")

        audience_rating = collection.get("median_rating")

        reported_revenue = collection.get("median_revenue")

        if pd.notna(sampled_titles):
            st.caption(f"{int(sampled_titles)} sampled films")

        if pd.notna(audience_rating):
            st.caption(f"Audience rating: {float(audience_rating):.1f}/10")

        if pd.notna(reported_revenue):
            st.caption(f"Reported revenue: {format_currency(reported_revenue)}")
