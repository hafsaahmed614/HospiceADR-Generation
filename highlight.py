"""Document highlighting — match extracted text to OCR bounding boxes and annotate images."""

from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

# Color palette for field highlights (RGBA with transparency)
FIELD_COLORS = {
    # Claim Form fields
    "patient_name": (255, 99, 71, 80),       # Tomato
    "dob": (30, 144, 255, 80),               # Dodger Blue
    "city": (255, 165, 0, 80),               # Orange
    "state": (255, 165, 0, 80),              # Orange (same as city)
    "zip_code": (255, 165, 0, 80),           # Orange (same as city)
    "primary_diagnosis_code": (50, 205, 50, 80),  # Lime Green
    "secondary_diagnoses": (148, 103, 189, 80),   # Purple

    # Progress Note fields
    "patient_mrn": (255, 215, 0, 80),        # Gold
    "hospice_status": (0, 206, 209, 80),     # Dark Turquoise
    "wound_length": (219, 112, 147, 80),     # Pale Violet Red
    "wound_width": (219, 112, 147, 80),      # Pale Violet Red
    "wound_depth": (219, 112, 147, 80),      # Pale Violet Red

    # Hospice fields
    "terminal_diagnosis": (255, 69, 0, 80),  # Red-Orange
    "hospice_secondary_diagnoses": (148, 103, 189, 80),  # Purple
    "noe_date": (0, 191, 255, 80),           # Deep Sky Blue
    "certification_periods": (60, 179, 113, 80),  # Medium Sea Green
}

# Solid colors for the legend (no alpha)
FIELD_COLORS_SOLID = {k: (r, g, b) for k, (r, g, b, _) in FIELD_COLORS.items()}

# Human-readable labels for the legend
FIELD_LABELS = {
    "patient_name": "Patient Name",
    "dob": "Date of Birth",
    "city": "City",
    "state": "State",
    "zip_code": "ZIP Code",
    "primary_diagnosis_code": "Primary Diagnosis",
    "secondary_diagnoses": "Secondary Diagnoses",
    "patient_mrn": "MRN",
    "hospice_status": "Hospice Status",
    "wound_length": "Wound Length",
    "wound_width": "Wound Width",
    "wound_depth": "Wound Depth",
    "terminal_diagnosis": "Terminal Diagnosis",
    "hospice_secondary_diagnoses": "Hospice Secondary DX",
    "noe_date": "NOE Date",
    "certification_periods": "Certification Periods",
}


def _normalize(text: str) -> str:
    """Lowercase and strip for comparison."""
    return text.strip().lower()


def match_text_to_boxes(
    search_text: str,
    ocr_data: Dict,
    padding: int = 4,
) -> List[Dict]:
    """Find bounding boxes in OCR data that match the search text.

    Uses a sliding window over consecutive OCR words to find matches.
    Returns a list of dicts with keys: left, top, width, height.
    """
    if not search_text or not ocr_data:
        return []

    search_normalized = _normalize(search_text)
    if not search_normalized or search_normalized in ("n/a", "null"):
        return []

    words = ocr_data.get("text", [])
    lefts = ocr_data.get("left", [])
    tops = ocr_data.get("top", [])
    widths = ocr_data.get("width", [])
    heights = ocr_data.get("height", [])
    n = len(words)

    # Build list of valid word indices (non-empty text)
    valid = [(i, _normalize(words[i])) for i in range(n) if words[i].strip()]
    if not valid:
        return []

    # Split search text into words for multi-word matching
    search_words = search_normalized.split()
    if not search_words:
        return []

    boxes = []

    # Sliding window: try to match consecutive OCR words to search words
    for start_idx in range(len(valid)):
        matched = 0
        end_idx = start_idx

        for sw in search_words:
            # Try to find this search word starting from end_idx
            found = False
            for check_idx in range(end_idx, min(end_idx + 3, len(valid))):
                ocr_word = valid[check_idx][1]
                # Check if search word is contained in OCR word or vice versa
                if sw in ocr_word or ocr_word in sw:
                    end_idx = check_idx + 1
                    matched += 1
                    found = True
                    break
            if not found:
                break

        # If we matched enough words, compute the bounding box
        if matched >= len(search_words) or (matched > 0 and matched >= len(search_words) * 0.7):
            matched_indices = [valid[j][0] for j in range(start_idx, min(end_idx, len(valid)))]
            if matched_indices:
                min_left = min(lefts[i] for i in matched_indices) - padding
                min_top = min(tops[i] for i in matched_indices) - padding
                max_right = max(lefts[i] + widths[i] for i in matched_indices) + padding
                max_bottom = max(tops[i] + heights[i] for i in matched_indices) + padding
                boxes.append({
                    "left": max(0, min_left),
                    "top": max(0, min_top),
                    "width": max_right - max(0, min_left),
                    "height": max_bottom - max(0, min_top),
                })
                # Only take the first match to avoid duplicates
                break

    return boxes


def annotate_page(
    image: Image.Image,
    highlights: List[Dict],
) -> Image.Image:
    """Draw colored highlight rectangles on a page image.

    Parameters
    ----------
    image : PIL.Image.Image
        The page image to annotate.
    highlights : list[dict]
        Each dict has keys: left, top, width, height, color (RGBA tuple).

    Returns
    -------
    PIL.Image.Image
        A copy of the image with highlights drawn.
    """
    annotated = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", annotated.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for h in highlights:
        x0 = h["left"]
        y0 = h["top"]
        x1 = x0 + h["width"]
        y1 = y0 + h["height"]
        color = h.get("color", (255, 255, 0, 80))
        draw.rectangle([x0, y0, x1, y1], fill=color)

    annotated = Image.alpha_composite(annotated, overlay)
    return annotated.convert("RGB")
