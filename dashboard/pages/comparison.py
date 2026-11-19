import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components import render_page_header, render_section_header
from dashboard.metrics import format_currency


def render_comparison(data: dict) -> None:
    """Compare reported film performance across release periods."""
    films = data["films"].copy()
    films["release_year"] = pd.to_numeric(films["release_year"], errors="coerce")
    films["period"] = films["release_year"].apply(
        lambda year: (
            "Pre-2000"
            if pd.notna(year) and year < 2000
            else "2000 onward"
            if pd.notna(year)
            else "Unknown"
        )
    )

    render_page_header(
        "Financial Comparison",
        "How reported film performance differs between older and more recent titles.",
    )

    valid = films[films["period"] != "Unknown"].copy()
    periods = ["Pre-2000", "2000 onward"]

    summary = (
        valid.groupby("period")
        .agg(
            film_count=("movie_id", "nunique"),
            median_revenue=("revenue", "median"),
            median_budget=("budget", "median"),
            median_rating=("vote_average", "median"),
            median_votes=("vote_count", "median"),
            median_popularity=("popularity", "median"),
        )
        .reindex(periods)
        .reset_index()
    )

    render_section_header("Reported financial performance")

    col1, col2 = st.columns(2, gap="large")
    for column, metric, heading in [
        (col1, "median_revenue", "Median reported revenue"),
        (col2, "median_budget", "Median reported production budget"),
    ]:
        with column:
            st.markdown(f"**{heading}**")
            chart = px.bar(
                summary,
                x="period",
                y=metric,
                text=summary[metric].apply(format_currency),
                labels={"period": "Release period", metric: "USD"},
            )
            chart.update_layout(
                showlegend=False,
                yaxis_title="Reported USD",
                xaxis_title="",
                margin={"l": 10, "r": 10, "t": 20, "b": 10},
            )
            chart.update_traces(textposition="outside")
            st.plotly_chart(chart, use_container_width=True)

    render_section_header("Audience response")

    audience_col1, audience_col2 = st.columns(2, gap="large")

    with audience_col1:
        st.markdown("**Median audience rating**")
        rating_chart = px.bar(
            summary,
            x="period",
            y="median_rating",
            labels={
                "period": "Release period",
                "median_rating": "Audience rating",
            },
            text_auto=".2f",
        )
        rating_chart.update_layout(
            showlegend=False,
            yaxis_title="Rating",
            xaxis_title="",
            margin={"l": 10, "r": 10, "t": 20, "b": 10},
        )
        st.plotly_chart(rating_chart, use_container_width=True)

    with audience_col2:
        st.markdown("**Median audience vote count**")
        votes_chart = px.bar(
            summary,
            x="period",
            y="median_votes",
            labels={
                "period": "Release period",
                "median_votes": "Audience votes",
            },
            text_auto=",",
        )
        votes_chart.update_layout(
            showlegend=False,
            yaxis_title="Votes",
            xaxis_title="",
            margin={"l": 10, "r": 10, "t": 20, "b": 10},
        )
        st.plotly_chart(votes_chart, use_container_width=True)

    st.dataframe(
        summary.rename(
            columns={
                "period": "Release period",
                "film_count": "Films analysed",
                "median_revenue": "Median reported revenue",
                "median_budget": "Median reported budget",
                "median_rating": "Audience rating",
                "median_votes": "Audience votes",
                "median_popularity": "Popularity",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Median reported revenue": st.column_config.NumberColumn(format="$%.0f"),
            "Median reported budget": st.column_config.NumberColumn(format="$%.0f"),
            "Audience rating": st.column_config.NumberColumn(format="%.2f"),
            "Audience votes": st.column_config.NumberColumn(format="%,.0f"),
            "Popularity": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    st.warning(
        "Historical financial figures are not adjusted for inflation or "
        "currency changes. Revenue and production budget are reported source "
        "values, not verified cash flows. Revenue divided by budget is not "
        "profit or return on investment."
    )

    render_section_header("Do the shortlisted titles change?")

    franchise_all = data["franchise_all"].head(5).copy()
    franchise_recent = data["franchise_recent"].head(5).copy()
    standalone_all = data["standalone_all"].head(5).copy()
    standalone_recent = data["standalone_recent"].head(5).copy()

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("**Top franchise opportunities**")
        franchise_comparison = pd.DataFrame(
            {
                "All years": franchise_all["collection_name"].tolist(),
                "2000 onward": franchise_recent["collection_name"].tolist(),
            }
        )
        st.dataframe(
            franchise_comparison,
            hide_index=True,
            use_container_width=True,
        )

    with right:
        st.markdown("**Top standalone films**")
        standalone_comparison = pd.DataFrame(
            {
                "All years": standalone_all["title"].tolist(),
                "2000 onward": standalone_recent["title"].tolist(),
            }
        )
        st.dataframe(
            standalone_comparison,
            hide_index=True,
            use_container_width=True,
        )

    st.caption(
        "Rankings use the same audience and reported-revenue indicators "
        "across both periods. They are comparative screening tools, not "
        "forecasts of streaming performance."
    )
