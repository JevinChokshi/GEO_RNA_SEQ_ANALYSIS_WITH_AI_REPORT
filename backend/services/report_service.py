import json

from backend.database.crud import (
    get_dataset_summary,
    get_qc_metrics,
    get_comparisons_for_dataset,
    get_top_upregulated,
    get_top_downregulated,
    get_deg_count
)


# =====================================================
# DATASET SUMMARY
# =====================================================

def generate_dataset_summary(gse_id):

    dataset = get_dataset_summary(gse_id)

    if not dataset:
        return None

    qc = get_qc_metrics(dataset.id)

    comparisons = get_comparisons_for_dataset(
        dataset.id
    )

    summary = {

        "gse_id":
        dataset.gse_id,

        "disease":
        dataset.disease,

        "platform":
        dataset.platform,

        "sample_count":
        dataset.sample_count,

        "comparisons":
        [
            c.comparison_name
            for c in comparisons
        ]
    }

    if qc:

        summary["qc"] = {

            "significant_genes":
            qc.significant_genes,

            "upregulated":
            qc.upregulated,

            "downregulated":
            qc.downregulated,

            "mean_counts":
            qc.mean_counts,

            "median_counts":
            qc.median_counts,

            "variance_explained_pc1":
            qc.variance_explained_pc1,

            "variance_explained_pc2":
            qc.variance_explained_pc2,

            "cluster_separation":
            qc.cluster_separation,

            "batch_effect":
            qc.batch_effect
        }

    return summary


# =====================================================
# COMPARISON SUMMARY
# =====================================================

def generate_comparison_summary(
    comparison
):

    deg_count = get_deg_count(
        comparison.id
    )

    top_up = get_top_upregulated(
        comparison.id,
        limit=20
    )

    top_down = get_top_downregulated(
        comparison.id,
        limit=20
    )

    summary = {

        "comparison_name":
        comparison.comparison_name,

        "case_group":
        comparison.case_group,

        "control_group":
        comparison.control_group,

        "deg_count":
        deg_count,

        "top_upregulated":
        [
            {
                "gene":
                g.symbol,

                "log2fc":
                g.log2fc,

                "padj":
                g.padj
            }
            for g in top_up
        ],

        "top_downregulated":
        [
            {
                "gene":
                g.symbol,

                "log2fc":
                g.log2fc,

                "padj":
                g.padj
            }
            for g in top_down
        ]
    }

    return summary


# =====================================================
# AI REPORT INPUT
# =====================================================

def build_ai_report_payload(
    dataset,
    comparison,
    qc,
    top_up,
    top_down,
    deg_count
):

    payload = {

        "dataset": {

            "gse_id":
            dataset.gse_id,

            "disease":
            dataset.disease,

            "platform":
            dataset.platform,

            "sample_count":
            dataset.sample_count
        },

        "comparison": {

            "name":
            comparison.comparison_name,

            "case_group":
            comparison.case_group,

            "control_group":
            comparison.control_group
        },

        "qc": {

            "significant_genes":
            qc.significant_genes,

            "upregulated":
            qc.upregulated,

            "downregulated":
            qc.downregulated,

            "variance_explained_pc1":
            qc.variance_explained_pc1,

            "variance_explained_pc2":
            qc.variance_explained_pc2,

            "cluster_separation":
            qc.cluster_separation,

            "batch_effect":
            qc.batch_effect
        },

        "deg_count":
        deg_count,

        "top_upregulated":
        [
            gene.symbol
            for gene in top_up
        ],

        "top_downregulated":
        [
            gene.symbol
            for gene in top_down
        ]
    }

    return payload


# =====================================================
# GEMINI PROMPT
# =====================================================

def build_ai_report_prompt(
    payload
):

    prompt = f"""
You are a biomedical transcriptomics expert.

Analyze the following differential expression study.

DATA:

{json.dumps(payload, indent=4)}

Generate a professional RNA-seq report with:

1. Executive Summary

2. Dataset Overview

3. Differential Expression Findings

4. Biological Interpretation

5. Top Upregulated Genes Discussion

6. Top Downregulated Genes Discussion

7. Transcriptomic Signature Assessment

8. Potential Disease Mechanisms

9. Therapeutic Implications

10. Key Conclusions

Use scientific language suitable for researchers.
Avoid hallucinating pathways.
Only discuss information supported by the supplied data.
"""

    return prompt