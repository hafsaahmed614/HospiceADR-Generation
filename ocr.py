"""OCR engine: extract text from uploaded PDFs and images via pytesseract."""

from typing import List

import io

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text_from_file(uploaded_file) -> str:
    """Extract OCR text from a Streamlit UploadedFile (PDF or image).

    Returns concatenated text with ``--- Page N ---`` delimiters for PDFs.
    """
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        images = convert_from_bytes(file_bytes)
    else:
        images = [Image.open(io.BytesIO(file_bytes))]

    pages: List[str] = []
    for i, img in enumerate(images, 1):
        text = pytesseract.image_to_string(img)
        pages.append(f"--- Page {i} ---\n{text}")

    return "\n\n".join(pages)
