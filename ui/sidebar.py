"""Sidebar with Letter Template upload and Developer Settings."""

import pandas as pd
import streamlit as st

import config


def render_sidebar() -> None:
    """Render the sidebar with template upload and Developer Settings."""
    with st.sidebar:
        st.header("Settings")

        # --- Letter Template ---
        st.subheader("Letter Template")

        template_file = st.file_uploader(
            "Upload DOCX Template",
            type=["docx"],
            key="template_uploader",
            help=(
                "Upload a .docx template with yellow-highlighted fields. "
                "The app will detect highlighted areas and fill them with "
                "extracted data. Formatting, logos, and images are preserved."
            ),
        )
        if template_file is not None:
            st.session_state["template_bytes"] = template_file.getvalue()
            st.session_state["template_filename"] = template_file.name
            st.session_state["filled_template_bytes"] = None

        if st.session_state.get("template_bytes"):
            st.success(f"Template: {st.session_state.get('template_filename', 'uploaded')}")

            # Show detected fields
            from template_filler import scan_template_placeholders

            fields = scan_template_placeholders(st.session_state["template_bytes"])
            if fields:
                df = pd.DataFrame(fields)
                df.columns = ["Field", "Type", "Status"]
                st.caption("Detected template fields:")
                st.dataframe(df, use_container_width=True, hide_index=True)

        st.session_state["company_name"] = st.text_input(
            "Company Name",
            value=st.session_state.get("company_name", ""),
            key="company_name_input",
            placeholder="e.g., Healing Partners Plus PLLC",
            help="Replaces the highlighted company name in the template body.",
        )

        st.session_state["letter_addressee"] = st.text_area(
            "Addressee (facility name and address)",
            value=st.session_state.get("letter_addressee", ""),
            height=100,
            key="addressee_input",
            placeholder="e.g.,\nNovitas Solutions, Inc.\nP.O. Box 3065\nMechanicsburg, PA 17055-1807",
            help="Replaces the highlighted addressee block in the template.",
        )

        st.divider()

        # --- Developer Settings ---
        with st.expander("Developer Settings", expanded=False):
            st.caption("Edit the system prompts used for LLM extraction.")

            st.session_state["claim_system_prompt"] = st.text_area(
                "Claim Form Extraction Prompt",
                value=st.session_state.get(
                    "claim_system_prompt", config.DEFAULT_CLAIM_PROMPT
                ),
                height=300,
                key="claim_prompt_input",
            )

            st.session_state["progress_system_prompt"] = st.text_area(
                "Progress Note Extraction Prompt",
                value=st.session_state.get(
                    "progress_system_prompt", config.DEFAULT_PROGRESS_PROMPT
                ),
                height=300,
                key="progress_prompt_input",
            )

            if st.button("Reset to Defaults"):
                st.session_state["claim_system_prompt"] = config.DEFAULT_CLAIM_PROMPT
                st.session_state["progress_system_prompt"] = config.DEFAULT_PROGRESS_PROMPT
                st.rerun()
