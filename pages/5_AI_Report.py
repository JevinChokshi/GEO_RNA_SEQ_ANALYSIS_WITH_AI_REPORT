import streamlit as st

from backend.database.crud import (
    get_all_datasets,
    get_comparisons_for_dataset,
    get_ai_report
)

from backend.services.ai_report_service import (
    generate_ai_report
)

st.title(
    "AI Transcriptomics Report"
)

datasets = get_all_datasets()

dataset = st.selectbox(
    "Dataset",
    datasets,
    format_func=lambda x:
    x.gse_id
)

comparisons = (
    get_comparisons_for_dataset(
        dataset.id
    )
)

comparison = st.selectbox(
    "Comparison",
    comparisons,
    format_func=lambda x:
    x.comparison_name
)

existing_report = (
    get_ai_report(
        comparison.id
    )
)

if existing_report:

    st.success(
        "Stored report found."
    )

    st.markdown(
        existing_report.report_text
    )

else:

    st.warning(
        "No report generated yet."
    )

if st.button(
    "Generate AI Report"
):

    with st.spinner(
        "Generating report..."
    ):

        report = (
            generate_ai_report(
                comparison
            )
        )

    st.success(
        "Report generated."
    )

    st.markdown(report)