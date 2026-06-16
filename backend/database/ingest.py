import json
from pathlib import Path

import pandas as pd

from backend.database.crud import (
    create_dataset,
    create_sample,
    create_comparison,
    create_qc_metric,
    bulk_insert_deg,
    create_plot_file
)



def ingest_metadata(
    gse_id,
    disease,
    metadata_file
):

    df = pd.read_csv(metadata_file)

    platform = (
        df["Platform"].iloc[0]
        if "Platform" in df.columns
        else None
    )


    dataset_id = create_dataset(
        gse_id=gse_id,
        disease=disease,
        platform=platform,
        sample_count=len(df)
    )

    for _, row in df.iterrows():
        # List your target columns in order of preference
        condition_columns = [
            "infection", "disease", "disease_state", "treatment", 
            "cohort", "condition", "diagnosis", "patient_diagnosis"
        ]

        cell_cols = ["cell_type", "source_name", "tissue"]

        create_sample(

            dataset_id=dataset_id,

            gsm=row.get(
                "Sample_GEO",
                ""
            ),

            srr=row.get(
                "Run",
                ""
            ),

            # Loop through columns and take the first non-empty value found
            condition = next((row.get(col) for col in condition_columns if row.get(col)), ""),


            cell_type= next((row.get(col) for col in cell_cols if row.get(col)), ""),

            platform=
            row.get(
                "Platform",
                ""
            ),

            title=
            row.get(
                "title",
                ""
            )
        )

    return dataset_id

def ingest_manifest(
    dataset_id,
    manifest_path
):

    with open(manifest_path) as f:

        manifest = json.load(f)

    create_qc_metric(
        dataset_id,
        manifest
    )

def ingest_deg_file(
    dataset_id,
    results_file
):

    results_file = Path(results_file)

    comparison_name = (
        results_file.stem
        .replace("_results", "")
    )

    comparison_id = (
        create_comparison(
            dataset_id,
            comparison_name
        )
    )

    df = pd.read_csv(results_file)

    bulk_insert_deg(
        comparison_id,
        df
    )

from backend.database.db import SessionLocal
from backend.database.models import QCMetric

# def ingest_qc_summary(
#     dataset_id,
#     qc_summary_file,
#     gse_id
# ):

#     df = pd.read_csv(qc_summary_file)

#     row = df[
#         df["dataset"] == gse_id
#     ]

#     if row.empty:
#         return

#     row = row.iloc[0]

#     db = SessionLocal()

#     qc = (
#         db.query(QCMetric)
#         .filter(
#             QCMetric.dataset_id == dataset_id
#         )
#         .first()
#     )

#     if not qc:

#         db.close()
#         return

#     qc.variance_explained_pc1 = float(
#         row["variance_explained_PC1"]
#     )

#     qc.variance_explained_pc2 = float(
#         row["variance_explained_PC2"]
#     )

#     qc.cluster_separation = float(
#         row["cluster_separation"]
#     )

#     qc.batch_effect = str(
#         row["batch_effect"]
#     )

#     db.commit()

#     db.close()

def ingest_qc_summary(
    dataset_id,
    qc_summary_file,
    gse_id
):

    print("QC SUMMARY FILE:", qc_summary_file)
    print("GSE ID:", repr(gse_id))

    df = pd.read_csv(qc_summary_file)

    print(df[["dataset"]])

    row = df[
        df["dataset"].astype(str).str.strip()
        == str(gse_id).strip()
    ]

    print("MATCHES:", len(row))

    if row.empty:

        print("NO MATCH FOUND")

        return

    row = row.iloc[0]

    print("ROW FOUND:")
    print(row)

    db = SessionLocal()

    qc = (
        db.query(QCMetric)
        .filter(
            QCMetric.dataset_id == dataset_id
        )
        .first()
    )

    print("QC OBJECT:", qc)

    if not qc:

        print("QC RECORD NOT FOUND")

        db.close()
        return

    qc.variance_explained_pc1 = float(
        row["variance_explained_PC1"]
    )

    qc.variance_explained_pc2 = float(
        row["variance_explained_PC2"]
    )

    qc.cluster_separation = float(
        row["cluster_separation"]
    )

    qc.batch_effect = str(
        row["batch_effect"]
    )

    db.commit()

    print("QC UPDATED")

    db.close()

from pathlib import Path


def ingest_plots(
    dataset_id,
    dataset_folder
):

    plots_dir = (
        Path(dataset_folder)
        / "plots"
    )

    if not plots_dir.exists():
        return

    for plot_file in plots_dir.glob("*.png"):

        filename = plot_file.stem

        if filename == "PCA_plot":

            create_plot_file(
                dataset_id=dataset_id,
                
                plot_type="PCA",
                file_path=str(plot_file)
            )

        elif "Volcano" in filename:

            create_plot_file(
                dataset_id=dataset_id,
                
                plot_type="VOLCANO",
                file_path=str(plot_file)
            )

def ingest_dataset_results(
    dataset_id,
    dataset_result_dir
):

    dataset_result_dir = Path(
        dataset_result_dir
    )

    manifest_file = (
        dataset_result_dir
        / "qc"
        / "manifest.json"
    )

    qc_summary_file = (
    dataset_result_dir.parent
    / "dataset_qc_summary.csv"
    )


    if manifest_file.exists():

        ingest_manifest(
            dataset_id,
            manifest_file
        )
    
    if qc_summary_file.exists():
        print(qc_summary_file)

        ingest_qc_summary(
            dataset_id,
            qc_summary_file,
            dataset_result_dir.name
        )
    
    ingest_plots(
        dataset_id,
        dataset_result_dir
    )

    de_dir = (
        dataset_result_dir
        / "differential_expression"
    )

    for file in de_dir.glob(
        "*_results.csv"
    ):

        ingest_deg_file(
            dataset_id,
            file
        )

