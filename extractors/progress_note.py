"""Progress Note clinical data extraction."""

from typing import Optional

import config
from llm import ExtractionError, extract_json
from models import ProgressNoteData


def extract_progress_note(
    ocr_text: str, system_prompt: Optional[str] = None
) -> ProgressNoteData:
    """Extract clinical and demographic data from a Progress Note.

    Parameters
    ----------
    ocr_text : str
        Raw OCR text from the progress note.
    system_prompt : str, optional
        Override the default system prompt (from Developer Settings).

    Returns
    -------
    ProgressNoteData
        Extracted progress note fields.

    Raises
    ------
    ExtractionError
        If extraction fails.
    """
    prompt = system_prompt or config.DEFAULT_PROGRESS_PROMPT
    result = extract_json(
        system_prompt=prompt,
        user_content=f"OCR Text:\n{ocr_text}",
        response_schema=config.PROGRESS_NOTE_SCHEMA,
    )
    return ProgressNoteData(**result)
