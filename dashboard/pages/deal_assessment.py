import streamlit as st

from dashboard.components import render_page_header, render_section_header
from dashboard.metrics import format_currency


def render_deal_assessment(data: dict) -> None:
    """Present the licensing recommendation and outstanding diligence."""
    franchise_all = data["franchise_all"]
    standalone_all = data["standalone_all"]

    render_page_header(
        "Deal Assessment",
        "Licensing priorities, supporting evidence, and outstanding commercial diligence.",
    )

    st.metric("Proposed licensing budget", format_currency(14_000_000))

    st.warning(
        "Recommendation: proceed to commercial diligence, not final approval. "
        "The available dataset supports content prioritisation but does not "
        "establish whether the proposed licensing price is commercially viable."
    )

    render_section_header("Priority franchise opportunities")

    priority_franchises = franchise_all.head(3)

    for rank, (_, franchise) in enumerate(priority_franchises.iterrows(), start=1):
        st.markdown(
            f"**{rank}. {franchise['collection_name']}**  \n"
            f"Sampled titles: {int(franchise['sampled_titles'])} · "
            f"Audience rating: {franchise['median_rating']:.2f} · "
            f"Reported revenue: {format_currency(franchise['median_revenue'])}"
        )

    render_section_header("Standalone alternatives")

    for rank, (_, film) in enumerate(standalone_all.head(5).iterrows(), start=1):
        year = film.get("release_year")
        year_label = str(int(year)) if year == year else "Year unavailable"  # noqa: PLR0124

        st.markdown(
            f"**{rank}. {film['title']}** ({year_label})  \n"
            f"Audience rating: {film['vote_average']:.2f} · "
            f"Reported revenue: {format_currency(film['revenue'])}"
        )

    render_section_header("Commercial diligence required")

    diligence_items = [
        "Obtain the asking price for each franchise bundle and standalone title.",
        "Confirm whether franchise rights are all-or-none and identify bundle contents.",
        "Verify territories, exclusivity, licensing windows, and contract duration.",
        "Confirm streaming, download, and other permitted distribution rights.",
        "Obtain historical title-level streaming performance where available.",
        "Estimate expected audience demand and incremental subscriber value.",
        "Model licensing cost against expected revenue and contribution margin.",
        "Confirm content delivery, localisation, marketing, and operational costs.",
    ]

    completed = []
    for item in diligence_items:
        completed.append(st.checkbox(item, key=f"diligence_{item[:35]}"))

    completed_count = sum(completed)
    st.progress(completed_count / len(diligence_items))
    st.caption(
        f"{completed_count} of {len(diligence_items)} diligence items marked complete."
    )

    render_section_header("Decision constraints")

    st.markdown(
        """
        - **No verified licensing prices:** the dataset contains film production
          budgets and reported box-office revenue, not the cost of acquiring rights.
        - **No streaming outcome data:** audience ratings, votes, and popularity
          are screening indicators, not forecasts of platform performance.
        - **Bundle scope is uncertain:** sampled films may not represent every
          title included in a franchise licensing package.
        - **Historical financial comparability is limited:** reported figures
          are not adjusted for inflation or currency changes.
        - **No ROI conclusion:** profitability cannot be calculated without
          licensing fees and the relevant operating and revenue assumptions.
        """
    )

    st.success(
        "Recommended next step: request title-level and bundle-level commercial "
        "terms for Avengers, The Lord of the Rings, and The Dark Knight, then "
        "compare them with the strongest standalone alternatives."
    )

    st.caption(
        "This assessment is based on the retrieved candidate sample and its "
        "reported metadata. It is a diligence recommendation, not an investment "
        "or procurement approval."
    )
