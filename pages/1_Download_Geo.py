import os
from io import BytesIO

import pandas as pd
import streamlit as st

from backend.services.config_service import load_settings
from backend.services.geo_service import download_dataset
from pipelines.geo.download_geo_bundle import get_s3_client

st.title("📥 Download New GEO Datasets")

# ==================================================
# INPUT
# ==================================================

st.subheader("Enter GEO Datasets (comma-separated)")

gse_input = st.text_area(
    "GEO IDs",
    placeholder="GSE156072, GSE135251, GSE81965"
)

# ==================================================
# DOWNLOAD BUTTON
# ==================================================

if st.button("🚀 Download All Datasets"):

    if not gse_input.strip():

        st.error(
            "Please enter at least one GEO dataset"
        )

        st.stop()

    gse_list = [
        gse.strip().upper()
        for gse in gse_input.split(",")
        if gse.strip()
    ]

    st.write(
        "📌 Datasets:",
        gse_list
    )

    settings = load_settings()

    disease = settings["deseq2"]["disease"]

    s3 = get_s3_client()

    bucket = os.getenv(
        "S3_BUCKET_DATA"
    )

    for gse in gse_list:

        st.divider()

        st.subheader(
            f"⬇️ Processing {gse}"
        )

        try:

            # ==================================================
            # DOWNLOAD
            # ==================================================

            download_dataset(gse)

            st.success(
                f"{gse} downloaded successfully"
            )

            # ==================================================
            # FIND SRA TABLE IN STORAGE
            # ==================================================

            possible_keys = [
                f"{disease}/{gse}/SraRunTable.csv",
                f"{disease}/{gse}/sra_run_table.csv",
                f"{disease}/{gse}/SRA_Run_Table.csv"
            ]

            run_table_df = None

            for key in possible_keys:

                try:

                    response = s3.get_object(
                        Bucket=bucket,
                        Key=key
                    )

                    csv_bytes = response[
                        "Body"
                    ].read()

                    run_table_df = pd.read_csv(
                        BytesIO(csv_bytes)
                    )

                    break

                except Exception:
                    continue

            # ==================================================
            # DISPLAY TABLE
            # ==================================================

            if run_table_df is not None:

                st.subheader(
                    "📊 SRA Run Table"
                )

                st.dataframe(
                    run_table_df,
                    use_container_width=True
                )

                st.caption(
                    f"Rows: {len(run_table_df)} | "
                    f"Columns: {len(run_table_df.columns)}"
                )

                condition_cols = [
                    "condition",
                    "disease",
                    "infection",
                    "disease_state",
                    "diagnosis"
                ]

                found_col = next(
                    (
                        c for c in condition_cols
                        if c in run_table_df.columns
                    ),
                    None
                )

                if found_col:

                    st.write(
                        f"{found_col} distribution:"
                    )

                    st.bar_chart(
                        run_table_df[
                            found_col
                        ].value_counts()
                    )

            else:

                st.warning(
                    "SRA Run Table not found "
                    "in Supabase Storage"
                )

        except Exception as e:

            st.error(
                f"Failed for {gse}: {str(e)}"
            )

    st.success(
        "🎉 Batch download completed"
    )