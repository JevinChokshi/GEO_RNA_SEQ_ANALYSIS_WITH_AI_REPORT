from backend.database.crud import (
    get_dataset_by_id,
    get_qc_metrics,
    get_top_upregulated,
    get_top_downregulated,
    get_deg_count,
    save_ai_report,
)
import re
from backend.services.report_service import (
    build_ai_report_payload,
    build_ai_report_prompt
)

from backend.services.gemini_service import (
    generate_rnaseq_report
)


def extract_section(report_text, heading):
    lines = report_text.splitlines()
    collected = []
    capture = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("#"):
            clean_heading = stripped.lstrip("#").strip().lower()

            if clean_heading == heading.lower():
                capture = True
                continue

            if capture:
                break

        if capture:
            collected.append(line)

    return "\n".join(collected).strip()

def extract_numbered_section(report_text, section_title):
    pattern = rf"(?:^|\n)\d+\.\s*{re.escape(section_title)}\s*\n(.*?)(?=\n\d+\.\s*[^\n]+\n|$)"
    match = re.search(pattern, report_text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    return ""


def generate_ai_report(comparison):
    dataset = get_dataset_by_id(
        comparison.dataset_id
    )

    qc = get_qc_metrics(
        dataset.id
    )

    top_up = get_top_upregulated(
        comparison.id,
        limit=25
    )

    top_down = get_top_downregulated(
        comparison.id,
        limit=25
    )

    deg_count = get_deg_count(
        comparison.id
    )

    payload = build_ai_report_payload(
        dataset=dataset,
        comparison=comparison,
        qc=qc,
        top_up=top_up,
        top_down=top_down,
        deg_count=deg_count
    )

    prompt = build_ai_report_prompt(
        payload
    )

    report = generate_rnaseq_report(
        prompt
    )

    save_ai_report(
        comparison.id,
        report
    )

    return report