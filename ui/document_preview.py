"""Document preview with highlighted extraction regions."""

from typing import Dict, List, Optional

import streamlit as st
from PIL import Image

from highlight import (
    FIELD_COLORS,
    FIELD_COLORS_SOLID,
    FIELD_LABELS,
    annotate_page,
    match_text_to_boxes,
)

# Which fields to highlight per document type
_CLAIM_FIELDS = [
    "patient_name", "dob", "city", "state", "zip_code",
    "primary_diagnosis_code", "secondary_diagnoses",
]

_PROGRESS_FIELDS = [
    "patient_name", "dob", "patient_mrn", "hospice_status",
    "wound_length", "wound_width", "wound_depth",
]

_HOSPICE_FIELDS = [
    "terminal_diagnosis", "hospice_secondary_diagnoses", "noe_date",
    "certification_periods",
]


def _get_field_value(data, field_name: str) -> Optional[str]:
    """Get a field value from a Pydantic model, returning None for missing/empty."""
    val = getattr(data, field_name, None)
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in ("", "n/a", "null", "none"):
        return None
    return s


def _get_field_page(data, field_name: str) -> Optional[int]:
    """Get the page number for a field (1-indexed), or None."""
    page_val = getattr(data, f"{field_name}_page", None)
    if page_val is None:
        return None
    try:
        return int(page_val)
    except (ValueError, TypeError):
        return None


def _build_highlights_for_page(
    data,
    fields: List[str],
    page_num: int,
    ocr_data: Dict,
) -> List[Dict]:
    """Build highlight rectangles for all fields on a given page."""
    highlights = []

    for field in fields:
        if field == "certification_periods":
            # Special handling for certification periods
            periods = getattr(data, "certification_periods", [])
            for period in periods:
                page = None
                try:
                    page = int(period.page) if period.page else None
                except (ValueError, TypeError):
                    pass
                if page != page_num:
                    continue
                color = FIELD_COLORS.get(field, (255, 255, 0, 80))
                for date_val in [period.start_date, period.end_date]:
                    if date_val:
                        boxes = match_text_to_boxes(date_val, ocr_data)
                        for box in boxes:
                            box["color"] = color
                            highlights.append(box)
            continue

        value = _get_field_value(data, field)
        if not value:
            continue

        field_page = _get_field_page(data, field)
        if field_page is not None and field_page != page_num:
            continue

        color = FIELD_COLORS.get(field, (255, 255, 0, 80))
        boxes = match_text_to_boxes(value, ocr_data)
        for box in boxes:
            box["color"] = color
            highlights.append(box)

    return highlights


def _render_legend(fields: List[str]) -> None:
    """Render a color-coded legend for the highlighted fields."""
    # Deduplicate colors (group fields sharing the same color)
    seen_colors = {}
    for field in fields:
        color = FIELD_COLORS_SOLID.get(field, (200, 200, 200))
        label = FIELD_LABELS.get(field, field)
        color_key = color
        if color_key not in seen_colors:
            seen_colors[color_key] = []
        seen_colors[color_key].append(label)

    legend_items = []
    for color, labels in seen_colors.items():
        r, g, b = color
        label_text = ", ".join(labels)
        legend_items.append(
            f'<span style="display:inline-block;width:14px;height:14px;'
            f'background:rgb({r},{g},{b});border-radius:2px;margin-right:6px;'
            f'vertical-align:middle;"></span>'
            f'<span style="vertical-align:middle;">{label_text}</span>'
        )

    st.markdown(
        "&nbsp;&nbsp;&nbsp;".join(legend_items),
        unsafe_allow_html=True,
    )


def _render_doc_preview(
    doc_label: str,
    page_images: Optional[List[Image.Image]],
    page_ocr_data: Optional[List[Dict]],
    extracted_data,
    fields: List[str],
) -> None:
    """Render a document preview with highlights for one document type."""
    if not page_images or not page_ocr_data:
        st.info(f"No {doc_label} document uploaded or processed.")
        return

    if not extracted_data:
        st.info(f"No extraction data available for {doc_label}.")
        return

    num_pages = len(page_images)

    # Page selector for multi-page documents
    if num_pages > 1:
        page_idx = st.selectbox(
            f"Page",
            range(num_pages),
            format_func=lambda x: f"Page {x + 1} of {num_pages}",
            key=f"preview_page_{doc_label}",
        )
    else:
        page_idx = 0

    page_num = page_idx + 1  # 1-indexed

    # Build highlights for this page
    highlights = _build_highlights_for_page(
        extracted_data, fields, page_num, page_ocr_data[page_idx]
    )

    # Annotate and display
    if highlights:
        annotated = annotate_page(page_images[page_idx], highlights)
        st.image(annotated, use_container_width=True)
    else:
        st.image(page_images[page_idx], use_container_width=True)

    # Legend
    _render_legend(fields)


def render_document_preview() -> None:
    """Render document preview tabs with highlighted extraction regions."""
    tab_claim, tab_progress, tab_hospice = st.tabs(
        ["Claim Form", "Progress Note", "Hospice Certification"]
    )

    with tab_claim:
        _render_doc_preview(
            "Claim Form",
            st.session_state.get("claim_page_images"),
            st.session_state.get("claim_ocr_data"),
            st.session_state.get("claim_data"),
            _CLAIM_FIELDS,
        )

    with tab_progress:
        _render_doc_preview(
            "Progress Note",
            st.session_state.get("progress_page_images"),
            st.session_state.get("progress_ocr_data"),
            st.session_state.get("progress_data"),
            _PROGRESS_FIELDS,
        )

    with tab_hospice:
        _render_doc_preview(
            "Hospice Certification",
            st.session_state.get("hospice_page_images"),
            st.session_state.get("hospice_ocr_data"),
            st.session_state.get("hospice_data"),
            _HOSPICE_FIELDS,
        )
