import os
import re
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import seaborn as sns
from adjustText import adjust_text

from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import pdist

from itertools import combinations

from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats
from pydeseq2.default_inference import DefaultInference

from pipelines.deseq2.app.validators import *
from pipelines.deseq2.app.config import SETTINGS


# =========================================================
# SAFE FILE NAME
# =========================================================

def safe_filename(text):

    text = str(text)

    text = re.sub(r"[^\w\-\.]", "_", text)
    text = re.sub(r"_+", "_", text)

    return text.strip("_")


# =========================================================
# QC SUMMARY APPENDER
# =========================================================

def append_dataset_qc_summary(summary_dict, summary_file):

    summary_df = pd.DataFrame([summary_dict])

    if os.path.exists(summary_file):

        existing = pd.read_csv(summary_file)

        existing = existing[
            existing["dataset"] != summary_dict["dataset"]
        ]

        updated = pd.concat(
            [existing, summary_df],
            ignore_index=True
        )

    else:

        updated = summary_df

    updated.to_csv(summary_file, index=False)

    print(f"QC summary updated: {summary_file}")


# =========================================================
# MANIFEST WRITER
# =========================================================

def write_manifest(manifest_data, output_path):

    with open(output_path, "w") as f:
        json.dump(manifest_data, f, indent=4)

    print(f"Manifest saved: {output_path}")


# =========================================================
# OUTLIER DETECTION
# =========================================================

def detect_pca_outliers(df_pc, z_threshold=3):

    outliers = []

    for axis in ["PC1", "PC2"]:

        z_scores = (
            (df_pc[axis] - df_pc[axis].mean())
            / df_pc[axis].std()
        )

        axis_outliers = df_pc[
            np.abs(z_scores) > z_threshold
        ]["sample"].tolist()

        outliers.extend(axis_outliers)

    return list(set(outliers))


# =========================================================
# BATCH EFFECT
# =========================================================

def estimate_batch_effect(df_pc):

    distances = pdist(
        df_pc[["PC1", "PC2"]].values
    )

    mean_distance = np.mean(distances)

    if mean_distance < 2:
        return "HIGH"

    elif mean_distance < 5:
        return "MODERATE"

    return "LOW"


# =========================================================
# LOAD + PROCESS
# =========================================================

def load_and_process_data(
    meta_file,
    counts_file,
    label_col='disease',
    control_label='control'
):

    validate_file_exists(meta_file)
    validate_file_exists(counts_file)

    meta_df = pd.read_csv(
        meta_file,
        index_col='Sample_GEO'
    )

    counts_df = pd.read_csv(
        counts_file,
        sep='\t',
        index_col='GeneID'
    )

    validate_dataframe_not_empty(meta_df, "Metadata")
    validate_dataframe_not_empty(counts_df, "Counts")

    validate_required_columns(
        meta_df,
        [label_col],
        "Metadata"
    )

    original_samples = meta_df.shape[0]
    original_genes = counts_df.shape[0]

    meta_df.rename(
        columns={label_col: 'disease_state'},
        inplace=True
    )

    meta_df.loc[
        meta_df['disease_state'] == control_label,
        'disease_state'
    ] = 'Control'

    meta_df = meta_df.dropna(
        subset=['disease_state']
    )

    labels = meta_df['disease_state'].unique().tolist()

    meta_df['disease_state'] = pd.Categorical(
        meta_df['disease_state'],
        categories=labels,
        ordered=True
    )

    meta_df = meta_df[
        ~meta_df.index.duplicated(keep="first")
    ]

    validate_sample_overlap(
        counts_df,
        meta_df
    )

    common_samples = counts_df.columns.intersection(
        meta_df.index
    )

    counts_df = counts_df[common_samples]
    meta_df = meta_df.loc[common_samples]

    counts_df = counts_df.loc[
        (counts_df.sum(axis=1) > 0),
        :
    ]

    min_gene_count = SETTINGS["deseq2"]["min_gene_count"]

    min_samples = SETTINGS["deseq2"]["min_samples"]

    counts_df = counts_df[
        (counts_df >= min_gene_count).sum(axis=1)
        >= min_samples
    ]

    validate_numeric_counts(counts_df)

    filtered_genes = (
        original_genes - counts_df.shape[0]
    )

    removed_samples = (
        original_samples - meta_df.shape[0]
    )

    processing_stats = {
        "original_samples": original_samples,
        "samples_retained": meta_df.shape[0],
        "samples_removed": removed_samples,
        "original_genes": original_genes,
        "genes_retained": counts_df.shape[0],
        "genes_filtered": filtered_genes
    }

    return (
        counts_df,
        meta_df,
        labels,
        processing_stats
    )


# =========================================================
# SAVE RESULTS
# =========================================================

def save_results(
    results: pd.DataFrame,
    results_mapped: pd.DataFrame,
    results_dir: str,
    contrast: list
) -> None:

    c1 = safe_filename(contrast[1])
    c2 = safe_filename(contrast[2])

    os.makedirs(results_dir, exist_ok=True)

    results_mapped.to_csv(
        os.path.join(
            results_dir,
            f"{c1}_vs_{c2}_results.csv"
        ),
        index=False
    )

    # results.to_csv(
    #     os.path.join(
    #         results_dir,
    #         f"{c1}_vs_{c2}_DESeq2_results_raw.csv"
    #     )
    # )

    print(
        f"Saved results for {c1} vs {c2}"
    )


# =========================================================
# CONFIDENCE ELLIPSE
# =========================================================

def confidence_ellipse(
    x,
    y,
    ax,
    n_std=2.0,
    facecolor='none',
    **kwargs
):

    if x.size != y.size:

        raise ValueError(
            "x and y must be same size"
        )

    cov = np.cov(x, y)

    vals, vecs = np.linalg.eigh(cov)

    order = vals.argsort()[::-1]

    vals = vals[order]

    vecs = vecs[:, order]

    theta = np.degrees(

        np.arctan2(
            *vecs[:, 0][::-1]
        )
    )

    width, height = 2 * n_std * np.sqrt(vals)

    ellipse = Ellipse(

        xy=(np.mean(x), np.mean(y)),

        width=width,

        height=height,

        angle=theta,

        facecolor=facecolor,

        **kwargs
    )

    ax.add_patch(ellipse)

    return ellipse


# =========================================================
# PCA PLOT + METRICS
# =========================================================

def plot_pca(
    vst_counts,
    meta_df,
    plot_dir,
    qc_dir
):

    pca = PCA(n_components=2)

    pc = pca.fit_transform(vst_counts)

    explained = (
        pca.explained_variance_ratio_ * 100
    )

    df_pc = pd.DataFrame({

        "sample": meta_df.index,

        "PC1": pc[:, 0],

        "PC2": pc[:, 1],

        "condition":
            meta_df[
                "disease_state"
            ].values
    })

    df_pc.to_csv(

        os.path.join(
            qc_dir,
            "PCA_coordinates.csv"
        ),

        index=False
    )

    # =====================================================
    # METRICS
    # =====================================================

    outliers = detect_pca_outliers(df_pc)

    cluster_sep = None

    if len(df_pc["condition"].unique()) > 1:

        try:

            cluster_sep = silhouette_score(
                df_pc[["PC1", "PC2"]],
                df_pc["condition"]
            )

        except:
            cluster_sep = None

    batch_effect = estimate_batch_effect(df_pc)

    pca_metrics = {
        "pc1_variance": round(explained[0], 3),
        "pc2_variance": round(explained[1], 3),
        "cluster_separation": cluster_sep,
        "outlier_samples": outliers,
        "batch_effect": batch_effect
    }

    pd.DataFrame([pca_metrics]).to_csv(
        os.path.join(qc_dir, "PCA_metrics.csv"),
        index=False
    )

    # =====================================================
    # COLORS
    # =====================================================

    conditions = sorted(
        df_pc["condition"].unique()
    )

    palette = sns.color_palette(
        "Set2",
        n_colors=len(conditions)
    )

    color_map = dict(
        zip(conditions, palette)
    )

    plt.figure(figsize=(9, 8))

    ax = plt.gca()

    for cond in conditions:

        subset = df_pc[
            df_pc["condition"] == cond
        ]

        ax.scatter(

            subset["PC1"],

            subset["PC2"],

            s=120,

            alpha=0.9,

            color=color_map[cond],

            edgecolor="black",

            linewidth=0.8,

            label=cond
        )

        if subset.shape[0] >= 3:

            confidence_ellipse(

                subset["PC1"].values,

                subset["PC2"].values,

                ax,

                edgecolor=color_map[cond],

                linestyle="--",

                linewidth=1.5,

                alpha=0.7
            )

    ax.set_xlabel(
        f"PC1 ({explained[0]:.1f}%)",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_ylabel(
        f"PC2 ({explained[1]:.1f}%)",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_title(
        "Principal Component Analysis",
        fontsize=18,
        fontweight="bold"
    )

    ax.grid(
        alpha=0.2,
        linestyle="--"
    )

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    ax.tick_params(
        axis="both",
        labelsize=12
    )

    ax.legend(
        frameon=False,
        fontsize=11,
        loc="best"
    )

    plt.tight_layout()

    png_path = os.path.join(
        plot_dir,
        "PCA_plot.png"
    )

    plt.savefig(
        png_path,
        dpi=600,
        bbox_inches="tight"
    )

    plt.close()

    print(
        "Publication-grade PCA plot saved"
    )

    return pca_metrics



def plot_volcano(
    results_mapped: pd.DataFrame,
    results_dir: str,
    contrast: list,
    padj_threshold: float = 0.05,
    log2fc_threshold: float = 1.5,
    top_n_labels: int = 8
) -> None:

    """
    Publication-grade volcano plot.
    """

    # ======================================
    # CLEAN DATA
    # ======================================

    df = results_mapped.copy()

    df = df.replace([np.inf, -np.inf], np.nan)

    df = df.dropna(
        subset=[
            "padj",
            "log2FoldChange"
        ]
    )

    df["padj"] = df["padj"].clip(lower=1e-300)

    df["neglog10_padj"] = -np.log10(df["padj"])

    # ======================================
    # SIGNIFICANCE GROUPS
    # ======================================

    df["category"] = "Not Significant"

    up_mask = (
        (df["padj"] < padj_threshold)
        &
        (df["log2FoldChange"] >= log2fc_threshold)
    )

    down_mask = (
        (df["padj"] < padj_threshold)
        &
        (df["log2FoldChange"] <= -log2fc_threshold)
    )

    df.loc[up_mask, "category"] = "Upregulated"

    df.loc[down_mask, "category"] = "Downregulated"

    # ======================================
    # COLORS
    # ======================================

    colors = {

        "Not Significant": "#BDBDBD",

        "Upregulated": "#D62728",

        "Downregulated": "#1F77B4"
    }

    # ======================================
    # FIGURE
    # ======================================

    plt.figure(figsize=(10, 8))

    ax = plt.gca()

    # ======================================
    # PLOT POINTS
    # ======================================

    for category in [

        "Not Significant",

        "Upregulated",

        "Downregulated"
    ]:

        subset = df[
            df["category"] == category
        ]

        ax.scatter(

            subset["log2FoldChange"],

            subset["neglog10_padj"],

            c=colors[category],

            s=28,

            alpha=0.75,

            edgecolors="none",

            label=category,

            rasterized=True
        )

    # ======================================
    # THRESHOLD LINES
    # ======================================

    ax.axvline(
        x=log2fc_threshold,
        linestyle="--",
        linewidth=1.2,
        color="black",
        alpha=0.7
    )

    ax.axvline(
        x=-log2fc_threshold,
        linestyle="--",
        linewidth=1.2,
        color="black",
        alpha=0.7
    )

    ax.axhline(
        y=-np.log10(padj_threshold),
        linestyle="--",
        linewidth=1.2,
        color="black",
        alpha=0.7
    )

    # ======================================
    # LABEL TOP GENES ONLY
    # ======================================

    label_df = df[
        df["category"] != "Not Significant"
    ].copy()

    label_df = label_df.sort_values(
        by="neglog10_padj",
        ascending=False
    )

    label_df = label_df.head(top_n_labels)

    texts = []

    for _, row in label_df.iterrows():

        gene = row.get("Symbol")

        if pd.isna(gene):

            gene = row.get("GeneID")

        txt = ax.text(

            row["log2FoldChange"],

            row["neglog10_padj"],

            str(gene),

            fontsize=11,

            fontweight="bold"
        )

        texts.append(txt)

    adjust_text(

        texts,

        arrowprops=dict(

            arrowstyle="-",

            color="black",

            lw=0.8
        )
    )

    # ======================================
    # STYLING
    # ======================================

    ax.set_xlabel(

        r"$\log_2$ Fold Change",

        fontsize=15,

        fontweight="bold"
    )

    ax.set_ylabel(

        r"$-\log_{10}$(Adjusted P-value)",

        fontsize=15,

        fontweight="bold"
    )

    ax.set_title(

        f"{contrast[1]} vs {contrast[2]}",

        fontsize=17,

        fontweight="bold"
    )

    ax.tick_params(

        axis="both",

        labelsize=12
    )

    # ======================================
    # REMOVE TOP/RIGHT SPINES
    # ======================================

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)


    # ======================================
    # LEGEND
    # ======================================

    legend = ax.legend(

        frameon=False,

        fontsize=11,

        loc="center left",

        bbox_to_anchor=(1.02, 0.5),

        borderaxespad=0
    )

    # ======================================
    # ADD RIGHT MARGIN FOR LEGEND
    # ======================================

    plt.subplots_adjust(right=0.82)

    # ======================================
    # LAYOUT
    # ======================================

    plt.tight_layout()

    # ======================================
    # SAVE
    # ======================================

    out_file = os.path.join(

        results_dir,

        f"{safe_filename(contrast[1])}_vs_"
        f"{safe_filename(contrast[2])}"
        "_Volcano_plot.png"
    )

    plt.savefig(

        out_file,

        dpi=600,

        bbox_inches="tight"
    )

    # # Optional vector export
    # pdf_out = out_file.replace(".png", ".pdf")

    # plt.savefig(

    #     pdf_out,

    #     bbox_inches="tight"
    # )

    plt.close()




# =========================================================
# MAP GENES
# =========================================================

def map_genes(results: pd.DataFrame, mapper_file: str):

    mapper = pd.read_csv(
        mapper_file,
        sep="\t",
        low_memory=False
    )

    mapper = mapper[
        [
            "GeneID",
            "Symbol",
            "EnsemblGeneID",
            "Description",
            "GeneType"
        ]
    ].drop_duplicates()

    mapper["GeneID"] = mapper["GeneID"].astype(str)

    results = results.reset_index()

    results["GeneID"] = results["GeneID"].astype(str)

    results_mapped = results.merge(
        mapper,
        on="GeneID",
        how="left"
    )

    # =====================================================
    # DIRECTION COLUMN
    # =====================================================

    results_mapped["direction"] = np.where(
        results_mapped["log2FoldChange"] > 0,
        "UP",
        "DOWN"
    )

    return results_mapped






from io import BytesIO
import boto3
import os


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION")
    )


def download_s3_file(bucket, key, local_path):

    s3 = get_s3_client()

    os.makedirs(
        os.path.dirname(local_path),
        exist_ok=True
    )

    s3.download_file(
        bucket,
        key,
        local_path
    )

from pathlib import Path


def upload_dataset_results(
    local_dir,
    disease,
    dataset
):

    s3 = get_s3_client()

    bucket = os.getenv(
        "S3_BUCKET_RESULT"
    )

    root = Path(local_dir)

    # ----------------------------------
    # Upload dataset folder
    # ----------------------------------

    for file in root.rglob("*"):

        if not file.is_file():
            continue

        relative = str(
            file.relative_to(root)
        ).replace("\\", "/")

        key = (
            f"{disease}/"
            f"{dataset}/"
            f"{relative}"
        )

        print(
            "Uploading:",
            key
        )

        s3.upload_file(
            str(file),
            bucket,
            key
        )

    # ----------------------------------
    # Upload disease QC summary
    # ----------------------------------

    qc_summary = (
        root.parent.parent
        / "dataset_qc_summary.csv"
    )

    if qc_summary.exists():

        summary_key = (
            f"{disease}/"
            f"dataset_qc_summary.csv"
        )

        print(
            "Uploading:",
            summary_key
        )

        s3.upload_file(
            str(qc_summary),
            bucket,
            summary_key
        )

# =========================================================
# RUN DESEQ2
# =========================================================

def run_deseq2(
    counts_df,
    meta_df,
    mapper_file,
    labels,
    de_dir,
    plot_dir,
    qc_dir,
    dataset_name,
    processing_stats,
    design,
    summary_file
):

    inference = DefaultInference()

    dds = DeseqDataSet(
        counts=counts_df.T,
        metadata=meta_df,
        design=design,
        refit_cooks=True,
        inference=inference
    )

    print("Running DESeq2 normalization...")

    dds.deseq2()

    out = list(combinations(labels, 2))

    contrasts = []

    for c in out:

        if 'Control' in c:

            control_idx = c.index('Control')

            contrast = [
                'disease_state',
                c[1-control_idx],
                c[control_idx]
            ]

            contrasts.append(contrast)

    if len(contrasts) == 0:

        raise ValueError(
            "No Control group contrasts found."
        )

    total_deg_count = 0
    total_up = 0
    total_down = 0

    manifest_data = None

    for contrast in contrasts:

        print(
            f"Running contrast: "
            f"{contrast[1]} vs {contrast[2]}"
        )

        de_stats = DeseqStats(
            dds,
            contrast=contrast,
            inference=inference
        )

        de_stats.summary()

        results = de_stats.results_df.copy()

        if results.empty:

            print(
                f"WARNING: Empty results for {contrast}"
            )

            continue

        sig = results[
            (results['padj'] < SETTINGS["deseq2"]["padj_threshold"]) &
            (
                abs(results['log2FoldChange'])
                > SETTINGS["deseq2"]["log2fc_threshold"]
            )
        ].copy()

        # =================================================
        # DIRECTION COLUMN
        # =================================================

        sig["direction"] = np.where(
            sig["log2FoldChange"] > 0,
            "UP",
            "DOWN"
        )

        upregulated = (
            sig["direction"] == "UP"
        ).sum()

        downregulated = (
            sig["direction"] == "DOWN"
        ).sum()

        total_deg_count += sig.shape[0]
        total_up += upregulated
        total_down += downregulated

        sig_file = os.path.join(
            de_dir,
            f"{safe_filename(contrast[1])}"
            f"_vs_"
            f"{safe_filename(contrast[2])}"
            f"_DEGs.csv"
        )

        sig.to_csv(sig_file)

        print(
            f"Significant genes: {sig.shape[0]}"
        )

        mapped_results = map_genes(
            results,
            mapper_file
        )

        save_results(
            results=results,
            results_mapped=mapped_results,
            results_dir=de_dir,
            contrast=contrast
        )

        plot_volcano(
            mapped_results,
            plot_dir,
            contrast
        )

        # =================================================
        # MANIFEST
        # =================================================

        manifest_data = {

            "dataset": dataset_name,

            "disease": contrast[1],

            "n_cases": int(
                (
                    meta_df["disease_state"]
                    == contrast[1]
                ).sum()
            ),

            "n_controls": int(
                (
                    meta_df["disease_state"]
                    == "Control"
                ).sum()
            ),

            "significant_genes": int(
                sig.shape[0]
            ),

            "upregulated": int(upregulated),

            "downregulated": int(downregulated),

            "padj_threshold":
                SETTINGS["deseq2"]["padj_threshold"],

            "logfc_threshold":
                SETTINGS["deseq2"]["log2fc_threshold"],

            "mean_counts":
                float(counts_df.values.mean()),

            "median_counts":
                float(np.median(counts_df.values)),

            "mean_library_size":
                float(counts_df.sum(axis=0).mean()),
            
        }

    # =====================================================
    # VST
    # =====================================================

    print("Generating VST counts...")

    dds.vst(use_design=False)

    vst_counts = dds.layers["vst_counts"]

# =====================================================
# PRESERVE SAMPLE + GENE LABELS
# =====================================================

    vst_df = pd.DataFrame(

        vst_counts,

        index=meta_df.index,

        columns=counts_df.index
    )

    vst_file = os.path.join(

        qc_dir,

        "VST_counts.csv"
    )

    vst_df.to_csv(vst_file)

    # =====================================================
    # PCA
    # =====================================================

    pca_metrics = plot_pca(
        vst_counts,
        meta_df,
        plot_dir,
        qc_dir
    )

    # =====================================================
    # MANIFEST SAVE
    # =====================================================

    manifest_path = os.path.join(
        qc_dir,
        "manifest.json"
    )

    write_manifest(
        manifest_data,
        manifest_path
    )

    # =====================================================
    # DATASET QC SUMMARY
    # =====================================================

    qc_summary = {

        "dataset": dataset_name,

        "samples_removed":
            processing_stats["samples_removed"],

        "samples_retained":
            processing_stats["samples_retained"],

        "genes_filtered":
            processing_stats["genes_filtered"],

        "total_DEGs":
            total_deg_count,

        "upregulated":
            total_up,

        "downregulated":
            total_down,

        "variance_explained_PC1":
            pca_metrics["pc1_variance"],

        "variance_explained_PC2":
            pca_metrics["pc2_variance"],

        "cluster_separation":
            pca_metrics["cluster_separation"],

        "batch_effect":
            pca_metrics["batch_effect"],

        "significant_DEGs":
            total_deg_count
    }

    append_dataset_qc_summary(
        qc_summary,
        summary_file
    )

    print(
        "DESeq2 pipeline completed successfully."
    )