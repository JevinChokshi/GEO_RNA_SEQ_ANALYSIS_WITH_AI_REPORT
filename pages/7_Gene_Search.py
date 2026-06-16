import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

import pandas as pd
import streamlit as st

from backend.database.crud import (
    search_gene_global
)

st.set_page_config(
    page_title="Gene Search",
    layout="wide"
)

st.title("Global Gene Search")

st.markdown(
    """
Search a gene across all DESeq2 comparisons stored in the platform.
"""
)

gene = st.text_input(
    "Gene Symbol",
    placeholder="STAT1"
)

# Empty dataframe by default
df = pd.DataFrame()

if gene:

    results = search_gene_global(
        gene.strip()
    )

    if not results:

        st.warning(
            f"No matches found for '{gene}'."
        )

    else:

        rows = []

        for deg, comp, dataset in results:

            rows.append({

                "Dataset":
                dataset.gse_id,

                "Disease":
                dataset.disease,

                "Comparison":
                comp.comparison_name,

                "Gene":
                deg.symbol,

                "Log2FC":
                deg.log2fc,

                "Padj":
                deg.padj,

                "Direction":
                deg.direction

            })

        df = pd.DataFrame(rows)

if not df.empty:

    st.divider()

    direction_filter = st.selectbox(
        "Direction Filter",
        [
            "ALL",
            "UP",
            "DOWN"
        ]
    )

    filtered_df = df.copy()

    if direction_filter != "ALL":

        filtered_df = filtered_df[
            filtered_df["Direction"]
            == direction_filter
        ]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Matches",
        len(filtered_df)
    )

    c2.metric(
        "Upregulated",
        len(
            filtered_df[
                filtered_df["Direction"]
                == "UP"
            ]
        )
    )

    c3.metric(
        "Downregulated",
        len(
            filtered_df[
                filtered_df["Direction"]
                == "DOWN"
            ]
        )
    )

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    csv = filtered_df.to_csv(
        index=False
    )

    st.download_button(

        label="Download CSV",

        data=csv,

        file_name=
        f"{gene}_gene_search.csv",

        mime="text/csv"
    )