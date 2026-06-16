import os
import boto3
import importlib  # Forces Python to reload the file if it's cached in memory
import pipelines.deseq2.app.config as config_module
from pipelines.geo.downloader_utils import download_raw_counts_for_gse
from pipelines.geo.metadata_utils import build_run_table_for_gse
from dotenv import load_dotenv
from io import BytesIO

DATASETS = [
    "GSE199911",
]

def get_s3_client():

    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        region_name=os.getenv("S3_REGION")
    )


bucket = os.getenv("S3_BUCKET_DATA")


def upload_bytes_to_s3(
    s3,
    data: bytes,
    key: str
):

    buffer = BytesIO(data)

    s3.upload_fileobj(
        buffer,
        bucket,
        key
    )

def process_gse(gse):

    print(f"\n===== Processing {gse} =====")

    importlib.reload(config_module)

    current_disease = (
        config_module
        .SETTINGS["deseq2"]["disease"]
    )

    prefix = f"{current_disease}/{gse}/"

    s3 = get_s3_client()

    # --------------------------------------------------
    # RAW COUNTS
    # --------------------------------------------------
    try:

        raw_files = download_raw_counts_for_gse(gse)

        if raw_files:

            print(
                f"[{gse}] Raw files received: "
                f"{len(raw_files)}"
            )

            for file in raw_files:

                key = prefix + file["filename"]

                print("Uploading:", key)

                upload_bytes_to_s3(
                    s3,
                    file["data"],
                    key
                )

        else:

            print(
                f"[{gse}] No raw count files found."
            )

    except Exception as e:

        print(
            f"[{gse}] Raw counts step failed: {e}"
        )

    # --------------------------------------------------
    # RUN TABLE
    # --------------------------------------------------
    try:

        filename, csv_bytes = build_run_table_for_gse(
            gse_id=gse,
            geo_destdir=None,
            email=os.getenv("NCBI_EMAIL"),
            tool=os.getenv("NCBI_TOOL")
        )

        upload_bytes_to_s3(
            s3,
            csv_bytes,
            prefix + filename
        )

        print(
            f"[{gse}] Uploaded run table"
        )

    except Exception as e:

        print(
            f"[{gse}] Run table step failed: {e}"
        )

    print(
        f"[{gse}] DONE"
    )


if __name__ == "__main__":

    importlib.reload(config_module)

    current_disease = (
        config_module
        .SETTINGS["deseq2"]["disease"]
    )

    print(
        f"🚀 Running download pipeline for "
        f"disease: {current_disease}"
    )

    for gse in DATASETS:
        process_gse(gse)

