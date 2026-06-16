import pandas as pd
import streamlit as st

from backend.database.crud import (
    get_all_datasets,
    get_comparisons_for_dataset,
    get_top_upregulated,
    get_top_downregulated,
    get_deg_count,
    get_deg_table,
    search_genes,
    get_comparison_plots,
    find_volcano_plot,
    get_storage_image_url
)

datasets = get_all_datasets()

dataset = st.selectbox(
    "Dataset",
    datasets,
    format_func=lambda x: x.gse_id
)

comparisons = get_comparisons_for_dataset(
    dataset.id
)

comparison = st.selectbox(
    "Comparison",
    comparisons,
    format_func=lambda x:
    x.comparison_name
)

deg_count = get_deg_count(
    comparison.id
)

up_genes = get_top_upregulated(
    comparison.id,
    limit=100000
)

down_genes = get_top_downregulated(
    comparison.id,
    limit=100000
)

c1,c2,c3 = st.columns(3)

c1.metric(
    "Total DEGs",
    deg_count
)

c2.metric(
    "Upregulated",
    len(up_genes)
)

c3.metric(
    "Downregulated",
    len(down_genes)
)

plots = get_comparison_plots(
    dataset.id
)

volcano = find_volcano_plot(
    comparison,
    plots
)

if volcano:

    st.subheader(
        "Volcano Plot"
    )

    st.image(
        get_storage_image_url(volcano.file_path),
        use_container_width=True
    )

top_up = get_top_upregulated(
    comparison.id,
    limit=25
)

up_df = pd.DataFrame([
    {
        "Gene": g.symbol,
        "Log2FC": g.log2fc,
        "Padj": g.padj
    }
    for g in top_up
])

st.subheader(
    "Top Upregulated Genes"
)

st.dataframe(
    up_df,
    use_container_width=True
)

top_down = get_top_downregulated(
    comparison.id,
    limit=25
)

gene_query = st.text_input(
    "Search Gene"
)

if gene_query:

    results = search_genes(
        comparison.id,
        gene_query
    )

    search_df = pd.DataFrame([
        {
            "Gene": g.symbol,
            "Log2FC": g.log2fc,
            "Padj": g.padj,
            "Direction": g.direction
        }
        for g in results
    ])

    st.dataframe(
        search_df,
        use_container_width=True
    )

st.subheader(
    "Full DEG Table"
)

degs = get_deg_table(
    comparison.id
)

deg_df = pd.DataFrame([
    {
        "Gene": g.symbol,
        "Log2FC": g.log2fc,
        "Padj": g.padj,
        "Direction": g.direction
    }
    for g in degs
])

st.dataframe(
    deg_df,
    use_container_width=True
)

