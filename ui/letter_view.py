"""Letter template fill and download UI."""

import re

import streamlit as st


def _sanitize_filename(name: str) -> str:
    """Turn a patient name into a safe filename component."""
    clean = re.sub(r"[^\w\s\-,]", "", name)
    clean = re.sub(r"[\s,]+", "_", clean).strip("_")
    return clean or "Patient"


def _get_filename_base() -> str:
    """Build the filename base from the patient name."""
    merged = st.session_state.get("merged_data")
    if merged and merged.patient_name:
        return f"{_sanitize_filename(merged.patient_name)}_ADRR"
    return "ADRR"


def _has_sufficient_data(merged) -> bool:
    """Check whether minimum fields are populated to generate a letter."""
    has_patient = bool(merged.patient_name)
    has_diagnosis = bool(merged.primary_diagnosis_code) or bool(merged.terminal_diagnosis)
    has_hospice = bool(merged.noe_date)
    return has_patient and has_diagnosis and has_hospice


def render_letter_view() -> None:
    """Render the ADR letter generator section."""
    merged = st.session_state.get("merged_data")
    if merged is None:
        return

    st.subheader("ADR Response Letter")

    if not _has_sufficient_data(merged):
        st.info(
            "Insufficient data to generate the letter. "
            "Ensure Patient Name, at least one diagnosis code, and NOE Date are extracted."
        )
        return

    if st.session_state.get("template_bytes") is None:
        st.warning("Upload a DOCX template in the sidebar to generate a letter.")
        return

    st.markdown(
        f"**Template:** {st.session_state.get('template_filename', 'uploaded')}"
    )

    if st.button("Fill Custom Template", type="primary"):
        from template_filler import fill_docx_template

        try:
            filled = fill_docx_template(
                st.session_state["template_bytes"],
                merged,
                addressee=st.session_state.get("letter_addressee", ""),
                company_name=st.session_state.get("company_name", ""),
            )
            st.session_state["filled_template_bytes"] = filled
        except Exception as e:
            st.error(f"Template fill failed: {e}")

    if st.session_state.get("filled_template_bytes"):
        filename_base = _get_filename_base()
        st.download_button(
            label="Download Filled Template (.docx)",
            data=st.session_state["filled_template_bytes"],
            file_name=f"{filename_base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
