"""Extraction results dashboard — Reference Data display."""

from typing import Optional

import streamlit as st

from models import MergedData

# Document source labels for page number display
_SRC_CLAIM = "Claim Form"
_SRC_PROGRESS = "Progress Note"
_SRC_HOSPICE = "Hospice"


def render_dashboard() -> None:
    """Display extracted reference data in a tabbed layout."""
    merged = st.session_state.get("merged_data")
    if merged is None:
        return

    st.subheader("Extraction Results")

    tab_ref, tab_hospice, tab_raw = st.tabs(
        ["Reference Data", "Hospice Details", "Raw Extractions"]
    )

    with tab_ref:
        _render_reference_table(merged)

    with tab_hospice:
        _render_hospice_details(merged)

    with tab_raw:
        _render_raw_data()


def _patient_name_source(merged: MergedData) -> str:
    """Determine which document patient name came from."""
    progress = st.session_state.get("progress_data")
    if progress and progress.patient_name:
        return _SRC_PROGRESS
    return _SRC_CLAIM


def _dob_source(merged: MergedData) -> str:
    """Determine which document DOB came from."""
    progress = st.session_state.get("progress_data")
    if progress and progress.dob:
        return _SRC_PROGRESS
    return _SRC_CLAIM


def _render_reference_table(merged: MergedData) -> None:
    """Render patient demographics, address, and wound measurements."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Patient Information**")
        _field_row("Patient Name", merged.patient_name, merged.patient_name_page, _patient_name_source(merged))
        _field_row("Date of Birth", merged.dob, merged.dob_page, _dob_source(merged))
        _field_row("MRN", merged.patient_mrn, merged.patient_mrn_page, _SRC_PROGRESS)
        _field_row("Hospice Status", merged.hospice_status, merged.hospice_status_page, _SRC_PROGRESS)

    with col2:
        st.markdown("**Address & Measurements**")
        address = _build_address(merged)
        _field_row("Address", address, merged.city_page, _SRC_CLAIM)
        st.markdown("---")
        st.markdown("**Wound Measurements**")
        _field_row("Length (cm)", merged.wound_length, merged.wound_length_page, _SRC_PROGRESS)
        _field_row("Width (cm)", merged.wound_width, merged.wound_width_page, _SRC_PROGRESS)
        _field_row("Depth (cm)", merged.wound_depth, merged.wound_depth_page, _SRC_PROGRESS)


def _render_hospice_details(merged: MergedData) -> None:
    """Render hospice-specific extraction results."""
    _field_row("NOE Date", merged.noe_date, merged.noe_date_page, _SRC_HOSPICE)
    _field_row("NOE Date Source", merged.noe_date_source)
    _field_row("Terminal Diagnosis", merged.terminal_diagnosis, merged.terminal_diagnosis_page, _SRC_HOSPICE)
    _field_row("Primary Diagnosis (Claim)", merged.primary_diagnosis_code, merged.primary_diagnosis_code_page, _SRC_CLAIM)
    _field_row("Secondary Diagnoses (Claim)", merged.secondary_diagnoses, merged.secondary_diagnoses_page, _SRC_CLAIM)
    _field_row("Hospice Secondary Diagnoses", merged.hospice_secondary_diagnoses, merged.hospice_secondary_diagnoses_page, _SRC_HOSPICE)

    if merged.certification_periods:
        st.markdown("**Certification Periods**")
        for period in merged.certification_periods:
            page_info = f" *(Page {period.page}, {_SRC_HOSPICE})*" if period.page else ""
            st.markdown(
                f"- **{period.period_name}**: {period.start_date} — {period.end_date}{page_info}"
            )
    else:
        st.markdown("**Certification Periods**: Not found")


def _render_raw_data() -> None:
    """Show raw JSON extraction results for debugging."""
    claim_data = st.session_state.get("claim_data")
    progress_data = st.session_state.get("progress_data")
    hospice_data = st.session_state.get("hospice_data")
    doc_map = st.session_state.get("hospice_doc_map")

    if claim_data:
        st.markdown("**Claim Form Extraction**")
        st.json(claim_data.model_dump())

    if progress_data:
        st.markdown("**Progress Note Extraction**")
        st.json(progress_data.model_dump())

    if hospice_data:
        st.markdown("**Hospice Data Extraction**")
        st.json(hospice_data.model_dump())

    if doc_map:
        st.markdown("**Hospice Document Map**")
        st.json(doc_map.model_dump())


def _is_valid(value: Optional[str]) -> bool:
    """Check if a value is a real data value (not empty, null, or a field name)."""
    if not value:
        return False
    stripped = str(value).strip().lower()
    if stripped in ("null", "n/a", ""):
        return False
    # Catch cases where the LLM returns a field name instead of a value
    if "_page" in stripped:
        return False
    return True


def _field_row(
    label: str,
    value: Optional[str],
    page: Optional[str] = None,
    source: Optional[str] = None,
) -> None:
    """Display a single field as 'Label: Value (Page X, Source)'."""
    display = value if _is_valid(value) else "N/A"
    page_info = ""
    if page and _is_valid(value):
        if source:
            page_info = f" *(Page {page}, {source})*"
        else:
            page_info = f" *(Page {page})*"
    st.markdown(f"**{label}:** {display}{page_info}")


def _build_address(merged: MergedData) -> Optional[str]:
    """Build a formatted address string from city, state, zip."""
    parts = [p for p in [merged.city, merged.state, merged.zip_code] if p]
    return ", ".join(parts) if parts else None
