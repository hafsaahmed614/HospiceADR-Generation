"""Sidebar with Developer Settings for editable system prompts."""

import streamlit as st

import config


def render_sidebar() -> None:
    """Render the sidebar with Developer Settings expander."""
    with st.sidebar:
        st.header("Settings")

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
