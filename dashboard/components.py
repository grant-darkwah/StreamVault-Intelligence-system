import html

import pandas as pd
import streamlit as st

from dashboard.metrics import (
    format_currency,
    get_backdrop_url,
    get_poster_url,
)


def render_page_header(title: str, subtitle: str):
    """Render a consistent page heading."""

    st.markdown(f"# {title}")
    st.caption(subtitle)
    st.divider()


def render_section_header(title: str, description: str = ""):
    """Render a section heading."""

    st.subheader(title)

    if description:
        st.caption(description)


def render_kpi(label: str, value: str, delta: str | None = None):
    """Render a reusable KPI card."""

    st.metric(
        label=label,
        value=value,
        delta=delta,
        border=True,
    )


def render_data_notice(message: str, level: str = "info"):
    """Render a consistent data-quality notice."""

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
    label: str = "FEATURED ACQUISITION",
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

    # Keep the HTML on one line so Streamlit does not
    # interpret the multiline markup as a code block.
    banner = (
        f'<div style="'
        f"background-image:linear-gradient(90deg,rgba(8,14,27,.97),rgba(8,14,27,.25)),"
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
        f'<div style="color:#36c6b3;font-size:11px;'
        f'font-weight:800;letter-spacing:2px;">'
        f"{label}</div>"
        f'<div style="color:white;font-size:38px;'
        f'font-weight:800;margin-top:14px;line-height:1.15;">'
        f"{title}</div>"
        f'<div style="color:#e0e7f0;font-size:14px;'
        f'margin-top:16px;">'
        f"{year} &nbsp;·&nbsp; Rating {rating_text}"
        f" &nbsp;·&nbsp; Reported revenue {revenue}"
        f"</div></div>"
    )

    st.markdown(
        banner,
        unsafe_allow_html=True,
    )


def render_movie_card(film: dict, score=None):
    """Render a poster-based standalone film card."""

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

        rating_text = f"{float(rating):.1f}/10" if pd.notna(rating) else "N/A"

        st.caption(f"{year} · Rating {rating_text}")

        if score is not None and pd.notna(score):
            st.caption(f"Composite score: {float(score):.3f}")

        revenue = film.get("revenue")

        if revenue is not None and pd.notna(revenue):
            st.caption(f"Reported revenue: {format_currency(revenue)}")


def render_franchise_card(
    collection: dict,
    rank: int,
    films: pd.DataFrame,
):
    """Render a simplified franchise card with representative artwork."""

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
        st.caption(f"FRANCHISE #{rank}")

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

        st.markdown(f"**{collection.get('collection_name', 'Unnamed collection')}**")

        median_revenue = collection.get("median_revenue")

        st.markdown(
            f"Median reported revenue: **{format_currency(median_revenue or 0)}**"
        )
