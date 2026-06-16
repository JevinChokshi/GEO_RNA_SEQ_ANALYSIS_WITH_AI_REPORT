from pipelines.deseq2.app.deseq_runner import (
    run_selected_datasets
)

from backend.database.scan_results import (
    scan_results
)

from backend.database.crud import (
    create_analysis_job,
    update_analysis_job
)


def run_dataset(gse_id):
    job_id = create_analysis_job(gse_id, "DESeq2")

    update_analysis_job(
    job_id,
    "RUNNING_DESEQ2"
    )
    
    run_selected_datasets([gse_id])


    update_analysis_job(
    job_id,
    "INGESTING_RESULTS")

    scan_results()

    update_analysis_job(
    job_id,
    "COMPLETED"
)