from sqlalchemy import (
    Column,
    Index,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey
)

from datetime import datetime

from backend.database.db import Base


class Dataset(Base):

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)

    gse_id = Column(String)

    disease = Column(String)

    platform = Column(String)

    sample_count = Column(Integer)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Sample(Base):

    __tablename__ = "samples"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id")
    )

    gsm = Column(String)

    srr = Column(String)

    condition = Column(String)

    cell_type = Column(String)

    platform = Column(String)

    title = Column(Text)


class Comparison(Base):

    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id")
    )

    comparison_name = Column(String)

    case_group = Column(String)

    control_group = Column(String)


class DEGResult(Base):

    __tablename__ = "deg_results"

    id = Column(Integer, primary_key=True)

    comparison_id = Column(
        Integer,
        ForeignKey("comparisons.id")
    )

    geneid = Column(String)

    symbol = Column(String)

    description = Column(Text)

    base_mean = Column(Float)

    log2fc = Column(Float)

    padj = Column(Float)

    direction = Column(String)


class QCMetric(Base):

    __tablename__ = "qc_metrics"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id")
    )

    significant_genes = Column(Integer)

    upregulated = Column(Integer)

    downregulated = Column(Integer)

    cluster_separation = Column(Float)

    batch_effect = Column(String)

    mean_counts = Column(Float)

    median_counts = Column(Float)

    variance_explained_pc1 = Column(Float)

    variance_explained_pc2 = Column(Float)

class PlotFile(Base):

    __tablename__ = "plot_files"

    id = Column(Integer, primary_key=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id")
    )

    plot_type = Column(String)

    file_path = Column(Text)

class AIReport(Base):

    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True)

    comparison_id = Column(
        Integer,
        ForeignKey("comparisons.id")
    )

    report_text = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class AnalysisJob(Base):

    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True)

    gse_id = Column(String)

    status = Column(String)

    started_at = Column(DateTime)

    completed_at = Column(DateTime)


Index("idx_geneid", DEGResult.geneid)
Index("idx_symbol", DEGResult.symbol)
Index("idx_comp", DEGResult.comparison_id)