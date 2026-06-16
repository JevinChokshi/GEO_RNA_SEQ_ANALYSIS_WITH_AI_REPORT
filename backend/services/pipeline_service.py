from backend.services.geo_service import download_dataset
from backend.services.deseq2_service import run_dataset

from backend.database.scan_metadata import scan_metadata
from backend.database.scan_results import scan_results

def run_full_pipeline(gse_id):

    download_dataset(gse_id)

    scan_metadata()

    run_dataset(gse_id)

    scan_results()