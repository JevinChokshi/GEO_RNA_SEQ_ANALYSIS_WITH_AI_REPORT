import pandas as pd
import streamlit as st

from backend.database.crud import (
    get_analysis_jobs
)

st.set_page_config(
    page_title="Analysis Jobs",
    layout="wide"
)

st.title(
    "Analysis Job Monitoring"
)

jobs = get_analysis_jobs()

if not jobs:

    st.info(
        "No jobs found."
    )

    st.stop()

df = pd.DataFrame([

    {
        "Job ID": j.id,
        "Dataset": j.gse_id,
        "Status": j.status,
        "Started": j.started_at,
        "Completed": j.completed_at
    }

    for j in jobs
])

st.dataframe(
    df,
    use_container_width=True
)

st.subheader(
    "Job Status Summary"
)

status_counts = (
    df["Status"]
    .value_counts()
    .reset_index()
)

status_counts.columns = [
    "Status",
    "Count"
]

st.bar_chart(
    status_counts.set_index(
        "Status"
    )
)

