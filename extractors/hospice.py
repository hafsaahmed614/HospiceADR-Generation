"""Hospice document extraction — 2-call pipeline (stages 0+1 combined, stages 2+3 combined)."""

from typing import Tuple

import json

import config
from llm import ExtractionError, extract_json
from models import CertificationPeriod, HospiceData, HospiceDocumentMap


def _build_document_map(ocr_text: str) -> HospiceDocumentMap:
    """Stage 0+1: Create and enrich a document map identifying all sections."""
    result = extract_json(
        system_prompt=config.HOSPICE_STAGE1_PROMPT,
        user_content=f"OCR Text:\n{ocr_text}",
        response_schema=config.HOSPICE_STAGE1_SCHEMA,
    )
    return HospiceDocumentMap(**result)


def _extract_clinical_data(
    ocr_text: str, doc_map: HospiceDocumentMap
) -> HospiceData:
    """Stage 2+3: Extract certification periods, terminal diagnosis, and NOE date."""
    doc_map_json = json.dumps(doc_map.model_dump(), indent=2)
    prompt = config.HOSPICE_STAGE2_PROMPT.format(document_map_json=doc_map_json)

    result = extract_json(
        system_prompt=prompt,
        user_content=f"OCR Text:\n{ocr_text}",
        response_schema=config.HOSPICE_STAGE2_SCHEMA,
    )

    periods = [CertificationPeriod(**p) for p in result.get("certification_periods", [])]

    # Programmatic NOE date fallback logic
    noe_date = result.get("noe_date")
    noe_source = result.get("noe_date_source")

    if not noe_date:
        # Try to find Benefit Period 1
        for period in periods:
            if "1" in period.period_name.lower() or "benefit period 1" in period.period_name.lower():
                noe_date = period.start_date
                noe_source = "Benefit Period 1"
                break

    return HospiceData(
        noe_date=noe_date,
        noe_date_source=noe_source,
        terminal_diagnosis=result.get("terminal_diagnosis"),
        certification_periods=periods,
    )


def extract_hospice_data(ocr_text: str) -> Tuple[HospiceDocumentMap, HospiceData]:
    """Run the full 2-call hospice extraction pipeline.

    Returns
    -------
    tuple[HospiceDocumentMap, HospiceData]
        The document map (for debugging/display) and extracted clinical data.

    Raises
    ------
    ExtractionError
        If either pipeline stage fails.
    """
    doc_map = _build_document_map(ocr_text)
    hospice_data = _extract_clinical_data(ocr_text, doc_map)
    return doc_map, hospice_data
