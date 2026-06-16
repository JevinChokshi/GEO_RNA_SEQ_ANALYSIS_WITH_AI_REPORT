import re
import io
import time
import pandas as pd
import GEOparse
from Bio import Entrez
import xml.etree.ElementTree as ET


def extract_bioproject_id(gse_obj):
    for relation in gse_obj.metadata.get("relation", []):
        if "BioProject" in relation:
            match = re.search(r"PRJNA\d+", relation)
            if match:
                return match.group(0)
    return None


def parse_characteristics_to_dict(characteristics):
    char_map = {}
    for item in characteristics:
        if ":" in item:
            k, v = item.split(":", 1)
            key = k.strip().replace(" ", "_")
            val = v.strip()
            if key in char_map:
                if isinstance(char_map[key], list):
                    char_map[key].append(val)
                else:
                    char_map[key] = [char_map[key], val]
            else:
                char_map[key] = val
    return char_map


def build_geo_pheno_df(gse_obj):
    pheno_dict = {}

    for gsm_id, gsm in gse_obj.gsms.items():
        meta = gsm.metadata
        char_map = parse_characteristics_to_dict(meta.get("characteristics_ch1", []))
        char_map["source_name"] = meta.get("source_name_ch1", [""])[0]
        char_map["title"] = meta.get("title", [""])[0]
        pheno_dict[gsm_id] = char_map

    pheno_df = (
        pd.DataFrame.from_dict(pheno_dict, orient="index")
        .reset_index()
        .rename(columns={"index": "Sample_GEO"})
    )
    return pheno_df


def fetch_sra_summary_records(bioproject_id, retmax=1000):
    search_handle = Entrez.esearch(
        db="sra",
        term=f"{bioproject_id}[BioProject]",
        retmax=retmax
    )
    search_results = Entrez.read(search_handle)
    search_handle.close()

    sra_uids = search_results.get("IdList", [])
    if not sra_uids:
        return []

    time.sleep(0.34)

    summary_handle = Entrez.esummary(
        db="sra",
        id=",".join(sra_uids),
        retmode="xml"
    )
    summary_records = Entrez.read(summary_handle)
    summary_handle.close()

    return summary_records


def parse_sra_summary_records(summary_records):
    parsed_records = []

    for docsum in summary_records:
        row_data = {"Id": docsum.get("Id", "")}

        for key, value in docsum.items():
            if isinstance(value, str):
                row_data[key] = value

        runs_meta = docsum.get("Runs", "")
        if runs_meta:
            run_match = re.search(r'acc="([A-Z0-9]+)"', runs_meta)
            if run_match:
                row_data["Run"] = run_match.group(1)

        ext_xml_str = docsum.get("ExtXml", "")
        if ext_xml_str:
            try:
                ext_root = ET.fromstring(f"<root>{ext_xml_str}</root>")
                sample_elem = ext_root.find(".//Sample")
                if sample_elem is not None and "acc" in sample_elem.attrib:
                    row_data["Sample_GEO"] = sample_elem.attrib["acc"]
            except Exception:
                pass

        if "Sample_GEO" not in row_data:
            all_text = " ".join([str(v) for v in docsum.values()])
            gsm_match = re.search(r"(GSM\d+)", all_text)
            if gsm_match:
                row_data["Sample_GEO"] = gsm_match.group(1)

        parsed_records.append(row_data)

    return pd.DataFrame(parsed_records)


def extract_clean_sra_fields(df):
    cleaned_rows = []

    for _, row in df.iterrows():
        row_data = {
            "Run": row.get("Run"),
            "Id": row.get("Id"),
            "CreateDate": row.get("CreateDate"),
            "Sample_GEO": row.get("Sample_GEO")
        }

        xml_str = row.get("ExpXml", "")
        if pd.notna(xml_str) and xml_str:
            try:
                root = ET.fromstring(f"<root>{xml_str}</root>")
                bioproject = root.find(".//Bioproject")
                biosample = root.find(".//Biosample")
                strategy = root.find(".//LIBRARY_STRATEGY")
                source = root.find(".//LIBRARY_SOURCE")
                selection = root.find(".//LIBRARY_SELECTION")
                layout_single = root.find(".//SINGLE")
                layout_paired = root.find(".//PAIRED")
                platform_elem = root.find(".//Platform")

                if bioproject is not None:
                    row_data["BioProject"] = bioproject.text
                if biosample is not None:
                    row_data["BioSample"] = biosample.text
                if strategy is not None:
                    row_data["Assay_Type"] = strategy.text
                if source is not None:
                    row_data["Library_Source"] = source.text
                if selection is not None:
                    row_data["Library_Selection"] = selection.text
                if platform_elem is not None:
                    row_data["Platform"] = platform_elem.attrib.get("instrument_model", platform_elem.text)
                else:
                    instrument_elem = root.find(".//Instrument")
                    if instrument_elem is not None:
                        row_data["Platform"] = list(instrument_elem.attrib.values())[0] if instrument_elem.attrib else instrument_elem.text

                if layout_single is not None:
                    row_data["Library_Layout"] = "SINGLE"
                elif layout_paired is not None:
                    row_data["Library_Layout"] = "PAIRED"

            except Exception:
                pass

        cleaned_rows.append(row_data)

    return pd.DataFrame(cleaned_rows)

def build_run_table_for_gse(
    gse_id,
    geo_destdir=None,
    email="23jevin@gmail.com",
    tool="AIDrugRepurposingProject"
):

    Entrez.email = email
    Entrez.tool = tool

    print(f"[{gse_id}] Loading GEO metadata...")

    gse = GEOparse.get_GEO(
        geo=gse_id,
        destdir=geo_destdir
    )

    bioproject_id = extract_bioproject_id(gse)

    if not bioproject_id:
        raise ValueError(
            f"[{gse_id}] Could not locate BioProject ID in GEO metadata."
        )

    print(f"[{gse_id}] Found BioProject: {bioproject_id}")
    print(f"[{gse_id}] Querying SRA summaries...")

    summary_records = fetch_sra_summary_records(bioproject_id)

    if not summary_records:
        raise ValueError(
            f"[{gse_id}] No SRA records found for project {bioproject_id}."
        )

    raw_df = parse_sra_summary_records(summary_records)

    sra_df = extract_clean_sra_fields(raw_df)

    pheno_df = build_geo_pheno_df(gse)

    if (
        "Sample_GEO" in sra_df.columns
        and
        "Sample_GEO" in pheno_df.columns
    ):
        final_df = pd.merge(
            sra_df,
            pheno_df,
            on="Sample_GEO",
            how="left"
        )
    else:
        final_df = sra_df.copy()

    buffer = io.StringIO()

    final_df.to_csv(
        buffer,
        index=False
    )

    csv_bytes = buffer.getvalue().encode()

    return "SraRunTable.csv", csv_bytes