import tempfile
from pathlib import Path

from backend.database.crud import (
    get_dataset_by_gse,
    get_session
)

from backend.database.models import QCMetric

from backend.database.ingest import (
    ingest_dataset_results
)

from pipelines.geo.download_geo_bundle import (
    get_s3_client
)

BUCKET = "results"


def has_existing_results(
    dataset_id
):

    db = get_session()

    exists = (
        db.query(QCMetric)
        .filter(
            QCMetric.dataset_id == dataset_id
        )
        .first()
        is not None
    )

    db.close()

    return exists


def download_prefix(
    s3,
    bucket,
    prefix,
    local_root
):

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=bucket,
        Prefix=prefix
    ):

        for obj in page.get(
            "Contents",
            []
        ):

            key = obj["Key"]

            if key.endswith("/"):
                continue

            relative = key[len(prefix):]

            local_path = (
                local_root / relative
            )

            local_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            s3.download_file(
                bucket,
                key,
                str(local_path)
            )


def scan_results():

    s3 = get_s3_client()

    response = s3.list_objects_v2(
        Bucket=BUCKET,
        Delimiter="/"
    )

    diseases = [
        p["Prefix"].rstrip("/")
        for p in response.get(
            "CommonPrefixes",
            []
        )
    ]

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

            dataset = (
                get_dataset_by_gse(
                    gse_id
                )
            )

            if not dataset:

                print(
                    f"{gse_id} not found"
                )

                continue

            if has_existing_results(
                dataset.id
            ):

                print(
                    f"{gse_id} already ingested"
                )

                continue

            print(
                f"Ingesting {gse_id}"
            )

            with tempfile.TemporaryDirectory() as tmp:

                local_dataset_dir = (
                    Path(tmp)
                    / gse_id
                )

                download_prefix(
                    s3=s3,
                    bucket=BUCKET,
                    prefix=f"{disease}/{gse_id}/",
                    local_root=local_dataset_dir
                )
                summary_key = (
                    f"{disease}/dataset_qc_summary.csv"
                )

                summary_local = (
                    Path(tmp)
                    / "dataset_qc_summary.csv"
                )

                try:

                    s3.download_file(
                        BUCKET,
                        summary_key,
                        str(summary_local)
                    )

                except Exception as e:

                    print(
                        f"Failed downloading QC summary: {e}"
                    )

                ingest_dataset_results(
                    dataset.id,
                    local_dataset_dir
                )

    print(
        "Results ingestion complete"
    )
