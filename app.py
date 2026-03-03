"""Hospice ADR Response Letter Generator — Streamlit application."""

from typing import List

import streamlit as st

import config
from extractors.claim_form import extract_claim_form
from extractors.hospice import extract_hospice_data
from extractors.progress_note import extract_progress_note
from llm import ExtractionError
from models import merge_data
from ocr import extract_text_from_file
from ui.dashboard import render_dashboard
from ui.letter_view import render_letter_view
from ui.sidebar import render_sidebar
from ui.uploaders import render_uploaders


def init_session_state() -> None:
    """Initialize all session state keys with defaults."""
    defaults = {
        # OCR results
        "hospice_ocr_text": None,
        "claim_ocr_text": None,
        "progress_ocr_text": None,
        # Extraction results
        "claim_data": None,
        "progress_data": None,
        "hospice_data": None,
        "hospice_doc_map": None,
        # Merged result
        "merged_data": None,
        # Letter
        "letter_addressee": "",
        # Template
        "template_bytes": None,
        "template_filename": None,
        "filled_template_bytes": None,
        "company_name": "",
        # Developer settings
        "claim_system_prompt": config.DEFAULT_CLAIM_PROMPT,
        "progress_system_prompt": config.DEFAULT_PROGRESS_PROMPT,
        # Processing state
        "processing_errors": [],
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def main() -> None:
    st.set_page_config(
        page_title="Hospice ADR Generator",
        page_icon="\U0001f3e5",
        layout="wide",
    )

    init_session_state()
    render_sidebar()

    st.title("Hospice ADR Response Letter Generator")
    st.caption(
        "Upload medical documents to extract data and generate an ADR response letter."
    )

    hospice_file, claim_file, progress_file = render_uploaders()

    # --- Validation ---
    has_hospice = hospice_file is not None
    has_claim = claim_file is not None
    has_progress = progress_file is not None
    has_secondary = has_claim or has_progress
    can_process = has_hospice and has_secondary

    if not has_hospice:
        st.warning("Please upload the Hospice Certification document (required).")
    elif not has_secondary:
        st.warning(
            "Please upload at least one additional document (Claim Form or Progress Note)."
        )

    st.divider()

    # --- Process Documents ---
    if st.button("Process Documents", disabled=not can_process, type="primary"):
        errors: List[str] = []

        with st.status("Processing documents...", expanded=True) as status:
            # Phase A: OCR
            st.write("Running OCR on uploaded documents...")

            # Hospice OCR (always required)
            try:
                st.session_state["hospice_ocr_text"] = extract_text_from_file(
                    hospice_file
                )
                st.write("  Hospice document OCR complete.")
            except Exception as e:
                errors.append(f"Hospice OCR failed: {e}")
                st.error(f"Hospice OCR failed: {e}")

            # Claim Form OCR (optional)
            if has_claim:
                try:
                    st.session_state["claim_ocr_text"] = extract_text_from_file(
                        claim_file
                    )
                    st.write("  Claim Form OCR complete.")
                except Exception as e:
                    errors.append(f"Claim Form OCR failed: {e}")
                    st.error(f"Claim Form OCR failed: {e}")

            # Progress Note OCR (optional)
            if has_progress:
                try:
                    st.session_state["progress_ocr_text"] = extract_text_from_file(
                        progress_file
                    )
                    st.write("  Progress Note OCR complete.")
                except Exception as e:
                    errors.append(f"Progress Note OCR failed: {e}")
                    st.error(f"Progress Note OCR failed: {e}")

            # Phase B: LLM Extraction
            st.write("Extracting data with AI...")

            # Hospice pipeline (2 LLM calls)
            if st.session_state.get("hospice_ocr_text"):
                try:
                    doc_map, hospice_data = extract_hospice_data(
                        st.session_state["hospice_ocr_text"]
                    )
                    st.session_state["hospice_doc_map"] = doc_map
                    st.session_state["hospice_data"] = hospice_data
                    st.write("  Hospice data extraction complete.")
                except ExtractionError as e:
                    errors.append(f"Hospice extraction failed: {e}")
                    st.error(f"Hospice extraction failed: {e}")

            # Claim Form extraction (1 LLM call)
            if st.session_state.get("claim_ocr_text"):
                try:
                    claim_data = extract_claim_form(
                        st.session_state["claim_ocr_text"],
                        system_prompt=st.session_state.get("claim_system_prompt"),
                    )
                    st.session_state["claim_data"] = claim_data
                    st.write("  Claim Form data extraction complete.")
                except ExtractionError as e:
                    errors.append(f"Claim Form extraction failed: {e}")
                    st.error(f"Claim Form extraction failed: {e}")

            # Progress Note extraction (1 LLM call)
            if st.session_state.get("progress_ocr_text"):
                try:
                    progress_data = extract_progress_note(
                        st.session_state["progress_ocr_text"],
                        system_prompt=st.session_state.get("progress_system_prompt"),
                    )
                    st.session_state["progress_data"] = progress_data
                    st.write("  Progress Note data extraction complete.")
                except ExtractionError as e:
                    errors.append(f"Progress Note extraction failed: {e}")
                    st.error(f"Progress Note extraction failed: {e}")

            # Phase C: Merge
            st.write("Merging extraction results...")
            merged = merge_data(
                claim=st.session_state.get("claim_data"),
                progress=st.session_state.get("progress_data"),
                hospice=st.session_state.get("hospice_data"),
            )
            st.session_state["merged_data"] = merged
            st.session_state["filled_template_bytes"] = None  # Reset on new merge

            if errors:
                status.update(
                    label="Processing completed with warnings", state="error"
                )
            else:
                status.update(label="Processing complete!", state="complete")

        st.session_state["processing_errors"] = errors

    # --- Display Results ---
    if st.session_state.get("merged_data"):
        render_dashboard()
        st.divider()
        render_letter_view()


if __name__ == "__main__":
    main()
