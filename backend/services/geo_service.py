from pipelines.geo.download_geo_bundle import process_gse

from backend.database.scan_metadata import (
    scan_metadata
)

from backend.database.crud import (
    create_analysis_job,
    update_analysis_job
)



    
def download_dataset(gse_id):

    job_id = create_analysis_job(
        gse_id,
        "DOWNLOADING"
    )

    try:
        

        process_gse(gse_id)
        scan_metadata()
        

        update_analysis_job(
            job_id,
            "DOWNLOADED"
        )
    

        return job_id

    except Exception:

        update_analysis_job(
            job_id,
            "FAILED"
        )

        raise


    