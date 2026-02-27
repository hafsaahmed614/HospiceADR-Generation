"""CMS-1500 Claim Form data extraction."""

from typing import Optional

import config
from llm import ExtractionError, extract_json
from models import ClaimFormData


def extract_claim_form(ocr_text: str, system_prompt: Optional[str] = None) -> ClaimFormData:
    """Extract CMS-1500 fields from OCR text.

    Parameters
    ----------
    ocr_text : str
        Raw OCR text from the claim form.
    system_prompt : str, optional
        Override the default system prompt (from Developer Settings).

    Returns
    -------
    ClaimFormData
        Extracted claim form fields.

    Raises
    ------
    ExtractionError
        If extraction fails.
    """
    prompt = system_prompt or config.DEFAULT_CLAIM_PROMPT
    result = extract_json(
        system_prompt=prompt,
        user_content=f"OCR Text:\n{ocr_text}",
        response_schema=config.CLAIM_FORM_SCHEMA,
    )
    return ClaimFormData(**result)
