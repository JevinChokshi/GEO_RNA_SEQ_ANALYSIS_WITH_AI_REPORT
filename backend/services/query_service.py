from backend.database.crud import (
    get_all_datasets,
    get_dataset_summary,
    get_samples_for_dataset,
    get_comparisons_for_dataset,
    get_qc_metrics,
    get_top_upregulated,
    get_top_downregulated
)

def dataset_overview():

    return get_all_datasets()

def dataset_details(
    gse_id
):

    dataset = get_dataset_summary(
        gse_id
    )

    if not dataset:

        return None

    return {

        "dataset": dataset,

        "samples":
        get_samples_for_dataset(
            dataset.id
        ),

        "comparisons":
        get_comparisons_for_dataset(
            dataset.id
        ),

        "qc":
        get_qc_metrics(
            dataset.id
        )
    }

def comparison_details(
    comparison_id
):

    return {

        "up":
        get_top_upregulated(
            comparison_id
        ),

        "down":
        get_top_downregulated(
            comparison_id
        )
    }

