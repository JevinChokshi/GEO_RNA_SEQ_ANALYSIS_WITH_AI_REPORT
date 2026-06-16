import pandas as pd
import streamlit as st

from backend.database.crud import (
    get_all_datasets,
    get_qc_metrics,
    get_samples_for_dataset,
    get_dataset_plots,
    get_storage_image_url
)

st.title("📊 Dataset Explorer")

# ==================================================
# DATASET SELECTION
# ==================================================

datasets = get_all_datasets()

if not datasets:

    st.warning(
        "No datasets available."
    )

    st.stop()

dataset = st.selectbox(
    "Select Dataset",
    datasets,
    format_func=lambda x: x.gse_id
)

# ==================================================
# DATASET INFO
# ==================================================

st.subheader(
    "Dataset Metadata"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Disease",
    dataset.disease
)

c2.metric(
    "Platform",
    dataset.platform or "-"
)

c3.metric(
    "Samples",
    dataset.sample_count
)

# ==================================================
# QC METRICS
# ==================================================

qc = get_qc_metrics(
    dataset.id
)

if qc:

    st.subheader(
        "QC Metrics"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Significant Genes",
        qc.significant_genes
    )

    c2.metric(
        "Upregulated",
        qc.upregulated
    )

    c3.metric(
        "Downregulated",
        qc.downregulated
    )

    c4.metric(
        "Batch Effect",
        qc.batch_effect
    )

    st.subheader(
        "PCA Statistics"
    )

    st.write("QC Object")

    st.write({
        "pc1": qc.variance_explained_pc1,
        "pc2": qc.variance_explained_pc2,
        "cluster": qc.cluster_separation,
    })

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "PC1 %",
        round(
            qc.variance_explained_pc1 or 0,
            2
        )
    )

    c2.metric(
        "PC2 %",
        round(
            qc.variance_explained_pc2 or 0,
            2
        )
    )

    c3.metric(
        "Cluster Separation",
        round(
            qc.cluster_separation or 0,
            3
        )
    )

# ==================================================
# PLOTS FROM SUPABASE STORAGE
# ==================================================

plots = get_dataset_plots(
    dataset.id
)

if plots:

    st.subheader(
        "Analysis Plots"
    )

    for plot in plots:

        try:

            image_url = (
                get_storage_image_url(
                    plot.file_path
                )
            )

            st.markdown(
                f"**{plot.plot_type}**"
            )

            st.image(
                image_url,
                use_container_width=True
            )

        except Exception as e:

            st.warning(
                f"Unable to load "
                f"{plot.plot_type}: {e}"
            )

# ==================================================
# SAMPLE TABLE
# ==================================================

samples = get_samples_for_dataset(
    dataset.id
)

sample_data = [

    {
        "GSM": s.gsm,
        "SRR": s.srr,
        "Condition": s.condition,
        "Cell Type": s.cell_type,
        "Platform": s.platform,
        "Title": getattr(
            s,
            "title",
            ""
        )
    }

    for s in samples
]

st.subheader(
    "Samples"
)

if sample_data:

    st.dataframe(
        pd.DataFrame(sample_data),
        use_container_width=True
    )

else:

    st.info(
        "No samples found."
    )