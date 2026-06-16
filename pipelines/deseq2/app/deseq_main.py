from pipelines.deseq2.app.deseq_runner import run_selected_datasets
from pipelines.deseq2.app.config import SELECTIONS
def run_deseq_pipeline():

    print("====================================")
    print("Running DESeq2 Pipeline")
    print("====================================")

    selected_datasets = SELECTIONS["selected_datasets"]

    run_selected_datasets(selected_datasets)

    print("====================================")
    print("DESeq2 COMPLETE")
    print("====================================")