import os
from pipelines.deseq2.app.config import SETTINGS, DATASETS
from pipelines.deseq2.app.deseq_utils import (
    load_and_process_data,
    run_deseq2,
    download_s3_file,
    upload_dataset_results
)

from pipelines.deseq2.app.logger import setup_logger

logger = setup_logger(
    SETTINGS["directories"]["logs"]
)



def run_selected_datasets(selected_datasets):

    disease = SETTINGS["deseq2"]["disease"]

    data_bucket = os.getenv("S3_BUCKET_DATA")

    tmp_root = "/tmp/deseq2"
    results_root = "/tmp/results"

    os.makedirs(tmp_root, exist_ok=True)
    os.makedirs(results_root, exist_ok=True)

    for dataset, params in DATASETS["datasets"].items():

        if dataset not in selected_datasets:
            continue

        logger.info(f"Running dataset: {dataset}")

        # --------------------------------------------------
        # Local working directory
        # --------------------------------------------------
        local_dataset_dir = os.path.join(
            tmp_root,
            dataset
        )

        os.makedirs(
            local_dataset_dir,
            exist_ok=True
        )

        # --------------------------------------------------
        # Download input files from Supabase
        # --------------------------------------------------
        counts_file = os.path.join(
            local_dataset_dir,
            f"{dataset}_raw_counts_GRCh38.p13_NCBI.tsv"
        )

        meta_file = os.path.join(
            local_dataset_dir,
            "SraRunTable.csv"
        )

        counts_key = (
            f"{disease}/"
            f"{dataset}/"
            f"{dataset}_raw_counts_GRCh38.p13_NCBI.tsv"
        )

        meta_key = (
            f"{disease}/"
            f"{dataset}/"
            f"SraRunTable.csv"
        )

        try:

            logger.info(
                f"Downloading counts file: {counts_key}"
            )

            download_s3_file(
                data_bucket,
                counts_key,
                counts_file
            )

            logger.info(
                f"Downloading metadata file: {meta_key}"
            )

            download_s3_file(
                data_bucket,
                meta_key,
                meta_file
            )

        except Exception as e:

            logger.error(
                f"Failed downloading files for {dataset}: {e}"
            )

            continue

        # --------------------------------------------------
        # Mapper file (still local project file)
        # --------------------------------------------------
        mapper_file = SETTINGS["directories"]["mapper_data"]

        # --------------------------------------------------
        # Result directories (temporary)
        # --------------------------------------------------
        dataset_result_dir = os.path.join(
            results_root,
            disease,
            dataset
        )

        de_dir = os.path.join(
            dataset_result_dir,
            "differential_expression"
        )

        plot_dir = os.path.join(
            dataset_result_dir,
            "plots"
        )

        qc_dir = os.path.join(
            dataset_result_dir,
            "qc"
        )

        os.makedirs(de_dir, exist_ok=True)
        os.makedirs(plot_dir, exist_ok=True)
        os.makedirs(qc_dir, exist_ok=True)

        # --------------------------------------------------
        # Load and process
        # --------------------------------------------------
        try:

            (
                counts_df,
                meta_df,
                labels,
                processing_stats
            ) = load_and_process_data(

                meta_file=meta_file,
                counts_file=counts_file,
                label_col=params["label_col"],
                control_label=params["control_label"]
            )

        except Exception as e:

            logger.error(
                f"Failed processing {dataset}: {e}"
            )

            continue

        # --------------------------------------------------
        # Run DESeq2
        # --------------------------------------------------
        try:
            summary_file = os.path.join(
            results_root,
            "dataset_qc_summary.csv"
            )

            run_deseq2(
                counts_df=counts_df,
                meta_df=meta_df,
                mapper_file=mapper_file,
                labels=labels,
                de_dir=de_dir,
                plot_dir=plot_dir,
                qc_dir=qc_dir,
                dataset_name=dataset,
                processing_stats=processing_stats,
                design=params["design"],
                summary_file=summary_file
            )

        except Exception as e:

            logger.error(
                f"DESeq2 failed for {dataset}: {e}"
            )

            continue

        # --------------------------------------------------
        # Upload results to Supabase
        # --------------------------------------------------
        try:

            upload_dataset_results(
                local_dir=dataset_result_dir,
                disease=disease,
                dataset=dataset
            )

            logger.info(
                f"Uploaded results for {dataset}"
            )

        except Exception as e:

            logger.error(
                f"Upload failed for {dataset}: {e}"
            )

        # --------------------------------------------------
        # Cleanup
        # --------------------------------------------------
        try:

            import shutil

            shutil.rmtree(
                local_dataset_dir,
                ignore_errors=True
            )

            shutil.rmtree(
                dataset_result_dir,
                ignore_errors=True
            )

        except Exception as e:

            logger.warning(
                f"Cleanup failed for {dataset}: {e}"
            )

    logger.info(
        "All selected datasets completed"
    )