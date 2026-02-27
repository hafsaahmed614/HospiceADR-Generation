"""File upload section with three document uploaders."""

import streamlit as st

import config


def render_uploaders() -> tuple:
    """Render three file uploaders and return the uploaded file objects.

    Returns
    -------
    tuple
        (hospice_file, claim_file, progress_file) — each is a Streamlit
        UploadedFile or None.
    """
    st.subheader("Upload Documents")

    col1, col2, col3 = st.columns(3)

    with col1:
        hospice_file = st.file_uploader(
            "Hospice Certification (Required)",
            type=config.SUPPORTED_FILE_TYPES,
            key="hospice_uploader",
            help="Upload the Hospice certification document (PDF or image).",
        )

    with col2:
        claim_file = st.file_uploader(
            "Claim Form (Optional)",
            type=config.SUPPORTED_FILE_TYPES,
            key="claim_uploader",
            help="Upload the CMS-1500 Claim Form (PDF or image).",
        )

    with col3:
        progress_file = st.file_uploader(
            "Progress Note (Optional)",
            type=config.SUPPORTED_FILE_TYPES,
            key="progress_uploader",
            help="Upload the clinical Progress Note (PDF or image).",
        )

    return hospice_file, claim_file, progress_file
