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
        _field_row("Patient Name", merged.patient_name)
        _field_row("Date of Birth", merged.dob)
        _field_row("MRN", merged.patient_mrn)
        _field_row("Hospice Status", merged.hospice_status)

    with col2:
        st.markdown("**Address & Measurements**")
        address = _build_address(merged)
        _field_row("Address", address)
        st.markdown("---")
        st.markdown("**Wound Measurements**")
        _field_row("Length (cm)", merged.wound_length)
        _field_row("Width (cm)", merged.wound_width)
        _field_row("Depth (cm)", merged.wound_depth)


def _render_hospice_details(merged: MergedData) -> None:
    """Render hospice-specific extraction results."""
    _field_row("NOE Date", merged.noe_date)
    _field_row("NOE Date Source", merged.noe_date_source)
    _field_row("Terminal Diagnosis", merged.terminal_diagnosis)
    _field_row("Primary Diagnosis (Claim)", merged.primary_diagnosis_code)
    _field_row("Secondary Diagnoses (Claim)", merged.secondary_diagnoses)

    if merged.certification_periods:
        st.markdown("**Certification Periods**")
        for period in merged.certification_periods:
            st.markdown(
                f"- **{period.period_name}**: {period.start_date} — {period.end_date}"
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


def _field_row(label: str, value: Optional[str]) -> None:
    """Display a single field as 'Label: Value' with styling for missing values."""
    display = value if (value and str(value).strip().lower() != "null") else "N/A"
    st.markdown(f"**{label}:** {display}")


def _build_address(merged: MergedData) -> Optional[str]:
    """Build a formatted address string from city, state, zip."""
    parts = [p for p in [merged.city, merged.state, merged.zip_code] if p]
    return ", ".join(parts) if parts else None
