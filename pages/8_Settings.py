import streamlit as st
from backend.database.db import SessionLocal
from backend.services.config_service import (
    load_settings,
    load_datasets,
    load_selections,
    save_yaml
)

# ==================================================
# APP CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="Settings",
    layout="wide"
)

st.title("⚙️ Project Settings")

# Fresh read directly from hardware drive
settings = load_settings()
datasets = load_datasets()
selections = load_selections()

dataset_registry = datasets.get("datasets", {})

# ==================================================
# CASE 1: NO DATASETS PRESENT
# ==================================================
if not dataset_registry:
    st.warning("⚠️ No datasets found in registry")
    st.info("Please add your first dataset to begin analysis")
    st.header("➕ Add First Dataset")

    new_gse = st.text_input("GEO Accession", placeholder="GSE123456", key="init_gse")
    new_label_col = st.text_input("Label Column", value="disease", key="init_label")
    new_control = st.text_input("Control Label", value="", key="init_control")
    new_design = st.text_input("Design Formula", value="~disease_state", key="init_design")

    if st.button("Create Dataset"):
        if not new_gse:
            st.error("GSE ID cannot be empty")
            st.stop()

        datasets["datasets"] = {}
        datasets["datasets"][new_gse] = {
            "label_col": new_label_col,
            "control_label": new_control,
            "design": new_design
        }

        save_yaml("datasets.yaml", datasets)
        st.success(f"{new_gse} created successfully")
        st.rerun()
    st.stop()

# ==================================================
# CASE 2: DATASETS EXIST → FULL SETTINGS UI
# ==================================================
st.header("Dataset Selection (For DESeq2)")

available_datasets = list(dataset_registry.keys())

selected_datasets = st.multiselect(
    "Select Datasets for Analysis",
    options=available_datasets,
    default=selections.get("selected_datasets", [])
)

# ==================================================
# DESEQ2 SETTINGS
# ==================================================
st.header("DESeq2 Parameters")
deseq_cfg = settings.get("deseq2", {})

log2fc = st.number_input(
    "Log2FC Threshold",
    value=float(deseq_cfg.get("log2fc_threshold", 1.5))
)

padj = st.number_input(
    "Adjusted P-value",
    value=float(deseq_cfg.get("padj_threshold", 0.05))
)

min_gene_count = st.number_input(
    "Minimum Gene Count",
    value=int(deseq_cfg.get("min_gene_count", 10))
)

min_samples = st.number_input(
    "Minimum Samples",
    value=int(deseq_cfg.get("min_samples", 2))
)

# Initialise session state to prevent Streamlit from overwriting this widget on intermediate reruns
if "disease_input_state" not in st.session_state:
    st.session_state["disease_input_state"] = deseq_cfg.get("disease", "")

disease_name = st.text_input(
    "Disease Name", 
    key="disease_input_state"
)

# ==================================================
# DATASET CONFIGS
# ==================================================
st.header("Dataset Configurations")

for gse in available_datasets:
    with st.expander(gse):
        ds = datasets["datasets"][gse]

        ds["label_col"] = st.text_input(
            f"{gse} Label Column",
            value=ds.get("label_col", ""),
            key=f"{gse}_label"
        )
        ds["control_label"] = st.text_input(
            f"{gse} Control Label",
            value=ds.get("control_label", ""),
            key=f"{gse}_control"
        )
        ds["design"] = st.text_input(
            f"{gse} Design Formula",
            value=ds.get("design", "~disease_state"),
            key=f"{gse}_design"
        )

# ==================================================
# SAVE CONFIG
# ==================================================
if st.button("💾 Save Configuration", use_container_width=True):

    selections["selected_datasets"] = selected_datasets

    # Update Core deseq2 Parameters
    settings.setdefault("deseq2", {})
    settings["deseq2"]["log2fc_threshold"] = log2fc
    settings["deseq2"]["padj_threshold"] = padj
    settings["deseq2"]["min_gene_count"] = min_gene_count
    settings["deseq2"]["min_samples"] = min_samples
    
    # Extract clean target name directly from state tracker
    chosen_disease = st.session_state["disease_input_state"].strip()
    settings["deseq2"]["disease"] = chosen_disease

    # Reset directories to the default static base values
    settings.setdefault("directories", {})
    settings["directories"]["logs"] = "results/deseq2/logs"
    settings["directories"]["mapper_data"] = "data/Human.GRCh38.p13.annot.tsv"
    settings["directories"]["raw_data"] = "data/raw/geo"
    settings["directories"]["results"] = "results/deseq2"

    # Save to disk using the atomic overwrite code
    save_yaml("settings.yaml", settings)
    save_yaml("datasets.yaml", datasets)
    save_yaml("selections.yaml", selections)

    db = SessionLocal()
    db.close()

    st.success(f"Configuration Saved for {chosen_disease}!")
    st.rerun()

# ==================================================
# ADD NEW DATASET
# ==================================================
st.header("Add New Dataset")

new_gse = st.text_input("GEO Accession", placeholder="GSE123456", key="new_gse_add")
new_label_col = st.text_input("Label Column", value="disease", key="new_label_add")
new_control = st.text_input("Control Label", value="", key="new_control_add")
new_design = st.text_input("Design Formula", value="~disease_state", key="new_design_add")

if st.button("➕ Add Dataset"):
    if not new_gse:
        st.error("GSE ID cannot be empty")
        st.stop()

    datasets.setdefault("datasets", {})
    datasets["datasets"][new_gse] = {
        "label_col": new_label_col,
        "control_label": new_control,
        "design": new_design
    }

    save_yaml("datasets.yaml", datasets)
    st.success(f"{new_gse} added successfully")
    st.rerun()
