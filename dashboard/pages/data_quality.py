import pandas as pd
import streamlit as st

from dashboard.components import render_page_header, render_section_header
from dashboard.data import get_data_summary


def render_data_quality(data: dict) -> None:
    """Display candidate reconciliation and data-quality findings."""

    summary = get_data_summary(data)

    render_page_header(
        "Data Quality",
        "Candidate coverage, retrieval outcomes, and the reliability of the analysis dataset.",
    )

    metrics = [
        ("Candidate records", summary["candidate_records"]),
        ("Unique valid IDs", summary["unique_valid_ids"]),
        ("Titles analysed", summary["analysed_titles"]),
        ("Invalid records", summary["invalid_records"]),
        ("Duplicate excess", summary["duplicate_excess"]),
        ("Valid IDs not retrieved", summary["unretrieved_valid_ids"]),
    ]

    columns = st.columns(3)

    for index, (label, value) in enumerate(metrics):
        with columns[index % 3]:
            st.metric(label, f"{value:,}")

    render_section_header("Candidate reconciliation")

    reconciliation_rows = pd.DataFrame(
        [
            {"Stage": "Raw candidate records", "Records": summary["candidate_records"]},
            {
                "Stage": "Invalid candidate records",
                "Records": summary["invalid_records"],
            },
            {
                "Stage": "Valid candidate rows",
                "Records": summary["valid_candidate_rows"],
            },
            {
                "Stage": "Duplicate excess occurrences",
                "Records": summary["duplicate_excess"],
            },
            {
                "Stage": "Unique valid candidate IDs",
                "Records": summary["unique_valid_ids"],
            },
            {
                "Stage": "Valid IDs not retrieved",
                "Records": summary["unretrieved_valid_ids"],
            },
            {
                "Stage": "Titles available for analysis",
                "Records": summary["analysed_titles"],
            },
        ]
    )

    st.dataframe(
        reconciliation_rows,
        hide_index=True,
        use_container_width=True,
    )

    st.info(
        f"The candidate list contains {summary['candidate_records']} records. "
        f"After excluding {summary['invalid_records']} invalid records and "
        f"collapsing {summary['duplicate_excess']} excess duplicate occurrences, "
        f"{summary['unique_valid_ids']} unique valid IDs remain. "
        f"{summary['unretrieved_valid_ids']} valid IDs were not retrieved, "
        f"leaving {summary['analysed_titles']} titles for analysis."
    )

    render_section_header("Retrieved dataset coverage")

    coverage = pd.DataFrame(
        [
            {"Dataset": "Films", "Rows": len(data["films"])},
            {"Dataset": "Cast credits", "Rows": len(data["cast"])},
            {"Dataset": "Crew credits", "Rows": len(data["crew"])},
        ]
    )

    st.bar_chart(coverage.set_index("Dataset")["Rows"])

    st.dataframe(
        coverage,
        hide_index=True,
        use_container_width=True,
    )

    render_section_header("Candidate retrieval details")

    reconciliation = data["reconciliation"]

    if reconciliation.empty:
        st.info("No candidate reconciliation records are available.")
    else:
        status_filter = st.selectbox(
            "Filter candidate records",
            ["All records", "Invalid records", "Valid records", "Duplicate records"],
        )

        filtered = reconciliation.copy()

        if status_filter == "Invalid records":
            filtered = filtered[filtered["is_valid"].eq(False)]
        elif status_filter == "Valid records":
            filtered = filtered[filtered["is_valid"].eq(True)]
        elif status_filter == "Duplicate records":
            filtered = filtered[filtered["is_duplicate"].eq(True)]

        st.dataframe(
            filtered,
            hide_index=True,
            use_container_width=True,
        )

    st.warning(
        f"The analysis covers {summary['analysed_titles']} retrieved titles, "
        f"not the complete set of {summary['unique_valid_ids']} unique valid "
        "candidate IDs. Interpret the findings with this coverage limitation in mind."
    )
