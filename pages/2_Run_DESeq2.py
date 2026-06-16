import streamlit as st

from backend.services.deseq2_service import (
    run_dataset
)

from backend.services.config_service import (
    load_selections
)

st.title("🧬 Run DESeq2 Pipeline")

selections = load_selections()

selected_datasets = selections.get(
    "selected_datasets",
    []
)

st.write(
    "Datasets to process:",
    selected_datasets
)

# ==================================================
# RUN PIPELINE
# ==================================================

if st.button("🚀 Run DESeq2"):

    if not selected_datasets:

        st.warning(
            "No datasets selected"
        )

        st.stop()

    progress = st.progress(0)

    status = st.empty()

    total = len(
        selected_datasets
    )

    successful = 0

    failed = []

    for idx, gse in enumerate(
        selected_datasets,
        start=1
    ):

        status.write(
            f"Running DESeq2 for {gse} "
            f"({idx}/{total})..."
        )

        try:

            run_dataset(gse)

            st.success(
                f"{gse} completed"
            )

            successful += 1

        except Exception as e:

            st.error(
                f"{gse} failed: {str(e)}"
            )

            failed.append(gse)

        progress.progress(
            idx / total
        )

    status.empty()

    st.success(
        f"Pipeline finished. "
        f"{successful}/{total} datasets processed."
    )

    if failed:

        st.warning(
            f"Failed datasets: "
            f"{', '.join(failed)}"
        )