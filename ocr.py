"""OCR engine: extract text from uploaded PDFs and images via pytesseract."""

from typing import Dict, List, Tuple

import io

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text_from_file(uploaded_file) -> str:
    """Extract OCR text from a Streamlit UploadedFile (PDF or image).

    Returns concatenated text with ``--- Page N ---`` delimiters for PDFs.
    """
    text, _, _ = extract_text_and_data(uploaded_file)
    return text


def extract_text_and_data(
    uploaded_file,
) -> Tuple[str, List[Image.Image], List[Dict]]:
    """Extract OCR text, page images, and word-level bounding box data.

    Returns
    -------
    tuple[str, list[PIL.Image.Image], list[dict]]
        - Concatenated OCR text with ``--- Page N ---`` delimiters.
        - List of page images (PIL Image objects).
        - List of pytesseract ``image_to_data`` dicts (one per page),
          each containing keys: level, page_num, block_num, par_num,
          line_num, word_num, left, top, width, height, conf, text.
    """
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        images = convert_from_bytes(file_bytes)
    else:
        images = [Image.open(io.BytesIO(file_bytes))]

    pages: List[str] = []
    page_ocr_data: List[Dict] = []

    for i, img in enumerate(images, 1):
        text = pytesseract.image_to_string(img)
        pages.append(f"--- Page {i} ---\n{text}")

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        page_ocr_data.append(data)

    ocr_text = "\n\n".join(pages)
    return ocr_text, images, page_ocr_data
