from backend.database.db import SessionLocal

from backend.database.models import (
    Dataset,
    Sample,
    Comparison,
    QCMetric,
    DEGResult,
    PlotFile,
    AIReport,
    AnalysisJob,
)
from backend.services.config_service import load_settings
import os
from dotenv import load_dotenv

load_dotenv()



def get_session():
    return SessionLocal()


# ==========================================
# DATASET
# ==========================================

def get_dataset_by_gse(gse_id):

    db = get_session()

    dataset = (
        db.query(Dataset)
        .filter(Dataset.gse_id == gse_id)
        .first()
    )

    db.close()

    return dataset



def create_dataset(
    gse_id,
    disease,
    platform,
    sample_count
):

    existing = get_dataset_by_gse(gse_id)

    if existing:
        return existing.id

    db = get_session()

    dataset = Dataset(
        gse_id=gse_id,
        disease=disease,
        platform=platform,
        sample_count=sample_count
    )

    db.add(dataset)

    db.commit()

    db.refresh(dataset)

    dataset_id = dataset.id

    db.close()

    return dataset_id


# ==========================================
# SAMPLE
# ==========================================

def create_sample(
    dataset_id,
    gsm,
    srr,
    condition,
    cell_type,
    platform,
    title
):

    db = get_session()

    sample = Sample(
        dataset_id=dataset_id,
        gsm=gsm,
        srr=srr,
        condition=condition,
        cell_type=cell_type,
        platform=platform,
        title=title
    )

    db.add(sample)

    db.commit()

    db.close()


# ==========================================
# COMPARISON
# ==========================================

def create_comparison(
    dataset_id,
    comparison_name
):

    db = get_session()

    existing = (
        db.query(Comparison)
        .filter(
            Comparison.dataset_id == dataset_id,
            Comparison.comparison_name == comparison_name
        )
        .first()
    )

    if existing:

        comp_id = existing.id

        db.close()

        return comp_id

    # ----------------------------------
    # Extract case/control groups
    # ----------------------------------

    case_group = None
    control_group = None

    if "_vs_" in comparison_name:

        parts = comparison_name.split(
            "_vs_",
            1
        )

        case_group = parts[0]
        control_group = parts[1]

    # ----------------------------------
    # Create comparison
    # ----------------------------------

    comp = Comparison(

        dataset_id=dataset_id,

        comparison_name=comparison_name,

        case_group=case_group,

        control_group=control_group
    )

    db.add(comp)

    db.commit()

    db.refresh(comp)

    comp_id = comp.id

    db.close()

    return comp_id


# ==========================================
# QC
# ==========================================

def create_qc_metric(
    dataset_id,
    manifest
):

    db = get_session()

    existing = (
        db.query(QCMetric)
        .filter(
            QCMetric.dataset_id == dataset_id
        )
        .first()
    )

    if existing:

        db.close()

        return

    qc = QCMetric(

        dataset_id=dataset_id,

        significant_genes=
        manifest.get(
            "significant_genes"
        ),

        upregulated=
        manifest.get(
            "upregulated"
        ),

        downregulated=
        manifest.get(
            "downregulated"
        ),

        mean_counts=
        manifest.get(
            "mean_counts"
        ),

        median_counts=
        manifest.get(
            "median_counts"
        ),
    )

    db.add(qc)

    db.commit()

    db.close()


# ==========================================
# DEG
# ==========================================

def bulk_insert_deg(
    comparison_id,
    dataframe
):

    db = get_session()

    records = []

    for _, row in dataframe.iterrows():

        records.append(

            DEGResult(

                comparison_id=comparison_id,

                geneid=str(
                    row["GeneID"]
                ),

                symbol=row.get(
                    "Symbol",
                    None
                ),

                description=row.get(
                    "Description",
                    None
                ),

                base_mean = row.get('baseMean', None),

                log2fc=float(
                    row["log2FoldChange"]
                ),

                padj=float(
                    row["padj"]
                ),

                direction=row.get(
                    "direction",
                    None
                )
            )
        )

    db.bulk_save_objects(records)

    db.commit()

    db.close()

def get_all_datasets():

    db = get_session()

    datasets = (
        db.query(Dataset)
        .order_by(Dataset.gse_id)
        .all()
    )

    db.close()

    return datasets

def get_dataset_by_id(
    dataset_id
):

    db = get_session()

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.id == dataset_id
        )
        .first()
    )

    db.close()

    return dataset

def get_dataset_summary(
    gse_id
):

    db = get_session()

    dataset = (
        db.query(Dataset)
        .filter(
            Dataset.gse_id == gse_id
        )
        .first()
    )

    db.close()

    return dataset

def get_samples_for_dataset(
    dataset_id
):

    db = get_session()

    samples = (
        db.query(Sample)
        .filter(
            Sample.dataset_id == dataset_id
        )
        .all()
    )

    db.close()

    return samples

def get_comparisons_for_dataset(
    dataset_id
):

    db = get_session()

    comps = (
        db.query(Comparison)
        .filter(
            Comparison.dataset_id == dataset_id
        )
        .all()
    )

    db.close()

    return comps

def get_comparison(
    comparison_id
):

    db = get_session()

    comp = (
        db.query(Comparison)
        .filter(
            Comparison.id == comparison_id
        )
        .first()
    )

    db.close()

    return comp

def get_qc_metrics(
    dataset_id
):

    db = get_session()

    qc = (
        db.query(QCMetric)
        .filter(
            QCMetric.dataset_id == dataset_id
        )
        .first()
    )

    db.close()

    return qc

def get_top_upregulated(
    comparison_id,
    limit=50
):

    db = get_session()

    genes = (
        db.query(DEGResult)
        .filter(
            DEGResult.comparison_id
            == comparison_id
        )
        .filter(
            DEGResult.direction == "UP"
        )
        .order_by(
            DEGResult.log2fc.desc()
        )
        .limit(limit)
        .all()
    )

    db.close()

    return genes

def get_top_downregulated(
    comparison_id,
    limit=50
):

    db = get_session()

    genes = (
        db.query(DEGResult)
        .filter(
            DEGResult.comparison_id
            == comparison_id
        )
        .filter(
            DEGResult.direction == "DOWN"
        )
        .order_by(
            DEGResult.log2fc.asc()
        )
        .limit(limit)
        .all()
    )

    db.close()

    return genes

def get_deg_count(
    comparison_id
):

    db = get_session()

    count = (
        db.query(DEGResult)
        .filter(
            DEGResult.comparison_id
            == comparison_id
        )
        .count()
    )

    db.close()

    return count

def get_comparison_by_id(
    comparison_id
):

    db = get_session()

    comparison = (
        db.query(Comparison)
        .filter(
            Comparison.id == comparison_id
        )
        .first()
    )

    db.close()

    return comparison


def get_storage_image_url(file_path: str) -> str:

    settings = load_settings()

    disease = settings["deseq2"]["disease"]

    # Normalize all slashes
    path = str(file_path).replace("\\", "/")

    # If already a storage key
    if not (
        path.startswith("C:/")
        or path.startswith("/tmp/")
        or "/Temp/" in path
    ):

        storage_key = path

        if storage_key.startswith("results/deseq2/"):
            storage_key = storage_key[len("results/deseq2/"):]

    else:

        parts = path.split("/")

        filename = parts[-1]
        plot_dir = parts[-2]

        gse_id = next(
            (
                part
                for part in parts
                if part.upper().startswith("GSE")
            ),
            None
        )

        if not gse_id:
            raise ValueError(
                f"Could not determine GSE from path: {file_path}"
            )

        storage_key = (
            f"{disease}/"
            f"{gse_id}/"
            f"{plot_dir}/"
            f"{filename}"
        )

    supabase_url = (
        os.getenv("SUPABASE_URL")
        .rstrip("/")
    )

    return (
        f"{supabase_url}"
        f"/storage/v1/object/public/results/"
        f"{storage_key}"
    )

def get_dataset_plots(
    dataset_id
):

    db = get_session()

    plots = (
        db.query(PlotFile)
        .filter(
            PlotFile.dataset_id
            == dataset_id
        )
        .all()
    )

    db.close()

    return plots

def create_plot_file(
    dataset_id,
    
    plot_type,
    file_path
):

    db = get_session()

    existing = (
        db.query(PlotFile)
        .filter(
            PlotFile.file_path == file_path
        )
        .first()
    )

    if existing:

        db.close()
        return

    plot = PlotFile(
        dataset_id=dataset_id,
        plot_type=plot_type,
        file_path=file_path
    )

    db.add(plot)

    db.commit()

    db.close()

def get_samples_for_dataset(
    dataset_id
):

    db = get_session()

    samples = (
        db.query(Sample)
        .filter(
            Sample.dataset_id == dataset_id
        )
        .all()
    )

    db.close()

    return samples

def search_genes(
    comparison_id,
    gene_symbol
):

    db = get_session()

    genes = (
        db.query(DEGResult)
        .filter(
            DEGResult.comparison_id
            == comparison_id
        )
        .filter(
            DEGResult.symbol.ilike(
                f"%{gene_symbol}%"
            )
        )
        .all()
    )

    db.close()

    return genes

def get_deg_table(
    comparison_id
):

    db = get_session()

    genes = (
        db.query(DEGResult)
        .filter(
            DEGResult.comparison_id
            == comparison_id
        )
        .all()
    )

    db.close()

    return genes

def get_comparison_plots(
    dataset_id
):

    db = get_session()

    plots = (
        db.query(PlotFile)
        .filter(
            PlotFile.dataset_id == dataset_id
        )
        .filter(
            PlotFile.plot_type == "VOLCANO"
        )
        .all()
    )

    db.close()

    return plots

def find_volcano_plot(
    comparison,
    plots
):

    for plot in plots:

        if comparison.comparison_name in plot.file_path:

            return plot

    return None

def find_volcano_plot(
    comparison,
    plots
):

    for plot in plots:

        if comparison.comparison_name in plot.file_path:

            return plot

    return None

# ==========================================
# AI REPORTS
# ==========================================
def save_ai_report(comparison_id, report_text):
    db = get_session()
    try:
        existing = (
            db.query(AIReport)
            .filter(AIReport.comparison_id == comparison_id)
            .first()
        )

        if existing:
            existing.report_text = report_text
            existing_id = existing.id
            db.commit()
            return existing_id

        report = AIReport(
            comparison_id=comparison_id,
            report_text=report_text
        )

        db.add(report)
        db.flush()
        report_id = report.id
        db.commit()
        return report_id

    finally:
        db.close()


def get_ai_report(
    comparison_id
):

    db = get_session()

    report = (
        db.query(AIReport)
        .filter(
            AIReport.comparison_id
            == comparison_id
        )
        .first()
    )

    db.close()

    return report

# ==========================================
# ANALYSIS JOBS
# ==========================================

from datetime import datetime

def create_analysis_job(
    gse_id,
    status="STARTED"
):

    db = get_session()

    job = AnalysisJob(

        gse_id=gse_id,

        status=status,

        started_at=datetime.utcnow()
    )

    db.add(job)

    db.commit()

    db.refresh(job)

    job_id = job.id

    db.close()

    return job_id

def update_analysis_job(
    job_id,
    status
):

    db = get_session()

    job = (
        db.query(AnalysisJob)
        .filter(
            AnalysisJob.id == job_id
        )
        .first()
    )

    if not job:

        db.close()

        return

    job.status = status

    if status in [
        "COMPLETED",
        "FAILED"
    ]:

        job.completed_at = (
            datetime.utcnow()
        )

    db.commit()

    db.close()

def get_analysis_jobs():

    db = get_session()

    jobs = (
        db.query(AnalysisJob)
        .order_by(
            AnalysisJob.id.desc()
        )
        .all()
    )

    db.close()

    return jobs

def search_gene_global(
    gene_symbol
):

    db = get_session()

    results = (
        db.query(
            DEGResult,
            Comparison,
            Dataset
        )
        .join(
            Comparison,
            DEGResult.comparison_id
            == Comparison.id
        )
        .join(
            Dataset,
            Comparison.dataset_id
            == Dataset.id
        )
        .filter(
            DEGResult.symbol.ilike(
                f"%{gene_symbol}%"
            )
        )
        .all()
    )

    db.close()

    return results