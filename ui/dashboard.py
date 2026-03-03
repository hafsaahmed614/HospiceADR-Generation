"""Extraction results dashboard — Reference Data display."""

from typing import Optional

import streamlit as st

from models import MergedData


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


def _render_reference_table(merged: MergedData) -> None:
    """Render patient demographics, address, and wound measurements."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Patient Information**")
        _field_row("Patient Name", merged.patient_name, merged.patient_name_page)
        _field_row("Date of Birth", merged.dob, merged.dob_page)
        _field_row("MRN", merged.patient_mrn, merged.patient_mrn_page)
        _field_row("Hospice Status", merged.hospice_status, merged.hospice_status_page)

    with col2:
        st.markdown("**Address & Measurements**")
        address = _build_address(merged)
        _field_row("Address", address, merged.city_page)
        st.markdown("---")
        st.markdown("**Wound Measurements**")
        _field_row("Length (cm)", merged.wound_length, merged.wound_length_page)
        _field_row("Width (cm)", merged.wound_width, merged.wound_width_page)
        _field_row("Depth (cm)", merged.wound_depth, merged.wound_depth_page)


def _render_hospice_details(merged: MergedData) -> None:
    """Render hospice-specific extraction results."""
    _field_row("NOE Date", merged.noe_date, merged.noe_date_page)
    _field_row("NOE Date Source", merged.noe_date_source)
    _field_row("Terminal Diagnosis", merged.terminal_diagnosis, merged.terminal_diagnosis_page)
    _field_row("Primary Diagnosis (Claim)", merged.primary_diagnosis_code, merged.primary_diagnosis_code_page)
    _field_row("Secondary Diagnoses (Claim)", merged.secondary_diagnoses, merged.secondary_diagnoses_page)
    _field_row("Hospice Secondary Diagnoses", merged.hospice_secondary_diagnoses, merged.hospice_secondary_diagnoses_page)

    if merged.certification_periods:
        st.markdown("**Certification Periods**")
        for period in merged.certification_periods:
            page_info = f" (p. {period.page})" if period.page else ""
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


def _field_row(label: str, value: Optional[str], page: Optional[str] = None) -> None:
    """Display a single field as 'Label: Value (p. X)' with styling for missing values."""
    display = value if (value and str(value).strip().lower() != "null") else "N/A"
    page_info = f" *(p. {page})*" if page else ""
    st.markdown(f"**{label}:** {display}{page_info}")


def _build_address(merged: MergedData) -> Optional[str]:
    """Build a formatted address string from city, state, zip."""
    parts = [p for p in [merged.city, merged.state, merged.zip_code] if p]
    return ", ".join(parts) if parts else None
