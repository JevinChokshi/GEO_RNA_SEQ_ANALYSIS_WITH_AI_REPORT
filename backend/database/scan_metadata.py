import tempfile
from pathlib import Path

from backend.database.ingest import ingest_metadata
from backend.database.crud import get_dataset_by_gse

from pipelines.geo.download_geo_bundle import get_s3_client

BUCKET = "data"


def scan_metadata():

    s3 = get_s3_client()

    paginator = s3.get_paginator("list_objects_v2")

    total = 0

    diseases = set()

    response = s3.list_objects_v2(
        Bucket=BUCKET,
        Delimiter="/"
    )

    for prefix in response.get("CommonPrefixes", []):
        diseases.add(
            prefix["Prefix"].rstrip("/")
        )

    for disease in diseases:

        response = s3.list_objects_v2(
            Bucket=BUCKET,
            Prefix=f"{disease}/",
            Delimiter="/"
        )

        for ds_prefix in response.get(
            "CommonPrefixes",
            []
        ):

            gse_id = (
                ds_prefix["Prefix"]
                .rstrip("/")
                .split("/")[-1]
            )

            existing = get_dataset_by_gse(
                gse_id
            )

            if existing:

                print(
                    f"Skipping {gse_id}"
                )

                continue

            metadata_key = (
                f"{disease}/"
                f"{gse_id}/"
                f"SraRunTable.csv"
            )

            try:

                with tempfile.TemporaryDirectory() as tmp:

                    local_file = (
                        Path(tmp)
                        / "SraRunTable.csv"
                    )

                    s3.download_file(
                        BUCKET,
                        metadata_key,
                        str(local_file)
                    )

                    print(
                        f"Ingesting {gse_id}"
                    )

                    ingest_metadata(
                        gse_id=gse_id,
                        disease=disease,
                        metadata_file=local_file
                    )

                    total += 1

            except Exception as e:

                print(
                    f"Failed {gse_id}: {e}"
                )

    print(
        f"\nMetadata scan complete\n"
        f"Datasets ingested: {total}"
    )