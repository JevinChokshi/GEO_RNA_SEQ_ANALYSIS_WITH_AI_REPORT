import streamlit as st
import pandas as pd

from backend.database.crud import (
    get_all_datasets,
    get_analysis_jobs
)

from backend.database.db import (
    SessionLocal
)

from backend.database.models import (
    Sample,
    Comparison,
    DEGResult,
    AIReport
)

def get_platform_stats():

    db = SessionLocal()

    stats = {

        "samples":
        db.query(Sample).count(),

        "comparisons":
        db.query(Comparison).count(),

        "degs":
        db.query(DEGResult).count(),

        "reports":
        db.query(AIReport).count()
    }

    db.close()

    return stats

st.set_page_config(
    page_title="Transcriptomics Platform",
    layout="wide"
)

st.title(
    "Transcriptomics Analytics Platform"
)

datasets = get_all_datasets()

stats = get_platform_stats()

c1,c2,c3,c4,c5 = st.columns(5)

c1.metric(
    "Datasets",
    len(datasets)
)

c2.metric(
    "Samples",
    stats["samples"]
)

c3.metric(
    "Comparisons",
    stats["comparisons"]
)

c4.metric(
    "DEGs",
    stats["degs"]
)

c5.metric(
    "AI Reports",
    stats["reports"]
)

st.subheader(
    "Available Datasets"
)

dataset_df = pd.DataFrame([

    {
        "GSE": d.gse_id,
        "Disease": d.disease,
        "Platform": d.platform,
        "Samples": d.sample_count
    }

    for d in datasets
])

st.dataframe(
    dataset_df,
    use_container_width=True
)

st.subheader(
    "Recent Analysis Jobs"
)

jobs = get_analysis_jobs()

job_df = pd.DataFrame([

    {
        "Dataset": j.gse_id,
        "Status": j.status,
        "Started": j.started_at,
        "Completed": j.completed_at
    }

    for j in jobs[:20]
])

st.dataframe(
    job_df,
    use_container_width=True
)

