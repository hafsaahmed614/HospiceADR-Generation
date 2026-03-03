"""Letter preview and download UI."""

import io
import os
import re
from pathlib import Path

import streamlit as st

from letter import generate_letter, generate_letter_for_pdf, letter_has_sufficient_data

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_LOGO_PATH = _PROJECT_DIR / "assets" / "letterhead.png"

# Field labels that should have underlines drawn after their values
_UNDERLINE_FIELDS = [
    "Patient Name:",
    "Date of Birth:",
    "UWI Primary Diagnosis:",
    "UWI Secondary/Related Diagnoses:",
    "Hospice NOE Date:",
    "Hospice Terminal Diagnosis:",
    "Certification Date(s):",
]

# Lines that should be right-aligned
_RIGHT_ALIGN_LINES = {
    "Saad Mohsin, M.D.",
    "Director of Medical Affairs",
    "2020 Calamos Court, Second Floor",
    "Naperville, IL  60563",
    "Very truly yours,",
}


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


def _is_field_line(line: str) -> bool:
    """Check if this line is a data field that needs an underline."""
    stripped = line.strip()
    return any(stripped.startswith(label) for label in _UNDERLINE_FIELDS)


def _is_right_aligned(line: str) -> bool:
    """Check if this line should be right-aligned."""
    stripped = line.strip()
    return stripped in _RIGHT_ALIGN_LINES


def _is_date_line(line: str) -> bool:
    """Check if this is the centered date line (contains only a date pattern)."""
    stripped = line.strip()
    return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", stripped))


def _generate_pdf(text: str) -> bytes:
    """Generate a formatted PDF matching the official ADRR letter layout."""
    try:
        from reportlab.lib.pagesizes import letter as pagesize
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=pagesize)
        width, height = pagesize
        margin = inch
        right_edge = width - margin
        max_width = width - 2 * margin
        underline_right = margin + max_width  # underlines extend to right margin
        y = height - margin
        line_height = 14
        font_name = "Times-Roman"
        font_bold = "Times-Bold"
        font_size = 11

        # --- Logo ---
        if _LOGO_PATH.exists():
            logo_w = 3.5 * inch
            logo_h = 0.7 * inch
            c.drawImage(
                str(_LOGO_PATH),
                margin,
                height - margin - logo_h + 0.3 * inch,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )
            y = height - margin - logo_h - 0.1 * inch

        c.setFont(font_name, font_size)

        lines = text.split("\n")
        # Track if we're in the signature block to tighten spacing
        in_signature = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if y < margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin

            # Detect signature block start
            if stripped == "Very truly yours,":
                in_signature = True

            # Empty lines — skip entirely in signature block
            if stripped == "":
                if in_signature:
                    pass  # no space between "Very truly yours," and "Saad Mohsin, M.D."
                else:
                    y -= line_height * 0.8
                i += 1
                continue

            # Right-aligned lines
            if _is_right_aligned(stripped):
                line_w = c.stringWidth(stripped, font_name, font_size)
                c.drawString(right_edge - line_w, y, stripped)
                y -= line_height
                i += 1
                continue

            # Date line — centered on page
            if _is_date_line(stripped):
                line_w = c.stringWidth(stripped, font_name, font_size)
                c.drawString((width - line_w) / 2, y, stripped)
                y -= line_height
                i += 1
                continue

            # "Re:" line — bold the subject
            if stripped.startswith("Re:"):
                c.setFont(font_name, font_size)
                re_prefix = "Re:     "
                subject = stripped[len("Re:"):].strip()
                prefix_w = c.stringWidth(re_prefix, font_name, font_size)
                indent_x = 0.5 * inch
                c.drawString(margin + indent_x, y, re_prefix)
                c.setFont(font_bold, font_size)
                c.drawString(margin + indent_x + prefix_w, y, subject)
                c.setFont(font_name, font_size)
                y -= line_height
                i += 1
                continue

            # Field lines (handles wrapping for long values)
            if _is_field_line(stripped):
                colon_pos = stripped.index(":") + 1
                label = stripped[:colon_pos]
                value = stripped[colon_pos:].strip()

                c.setFont(font_name, font_size)
                label_w = c.stringWidth(label + " ", font_name, font_size)

                # Draw label
                c.drawString(margin, y, label + " ")

                # Word-wrap value if it's too long
                value_x_start = margin + label_w
                available_first = max_width - label_w
                available_cont = max_width

                words = value.split()
                current_val = ""
                first_val_line = True

                while words:
                    word = words.pop(0)
                    test = current_val + (" " if current_val else "") + word
                    avail = available_first if first_val_line else available_cont
                    if c.stringWidth(test, font_name, font_size) <= avail:
                        current_val = test
                    else:
                        x = value_x_start if first_val_line else margin
                        c.drawString(x, y, current_val)
                        y -= line_height
                        current_val = word
                        first_val_line = False

                # Flush remaining value
                if current_val:
                    x = value_x_start if first_val_line else margin
                    c.drawString(x, y, current_val)

                y -= line_height
                i += 1
                continue

            # "Enclosures" at bottom left
            if stripped == "Enclosures":
                c.drawString(margin, y, stripped)
                y -= line_height
                i += 1
                continue

            # "The information requested..." — left-aligned at margin, no indent
            if stripped.startswith("The information requested"):
                c.drawString(margin, y, stripped)
                y -= line_height
                i += 1
                continue

            # Normal paragraphs — detect indentation and word-wrap
            para_indent = 0
            if line.startswith("        ") or line.startswith("\t"):
                para_indent = 0.5 * inch

            words = stripped.split()
            current_line = ""
            effective_max = max_width - para_indent
            first_line_of_para = True

            while words:
                word = words.pop(0)
                test_line = current_line + (" " if current_line else "") + word
                if c.stringWidth(test_line, font_name, font_size) <= effective_max:
                    current_line = test_line
                else:
                    x = margin + (para_indent if first_line_of_para else 0)
                    c.drawString(x, y, current_line)
                    y -= line_height
                    if y < margin:
                        c.showPage()
                        c.setFont(font_name, font_size)
                        y = height - margin
                    current_line = word
                    first_line_of_para = False
                    effective_max = max_width

            if current_line:
                x = margin + (para_indent if first_line_of_para else 0)
                c.drawString(x, y, current_line)
                y -= line_height

            i += 1

        c.save()
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None


def render_letter_view() -> None:
    """Render the ADR letter generator section."""
    merged = st.session_state.get("merged_data")
    if merged is None:
        return

    st.subheader("ADR Response Letter")

    if not letter_has_sufficient_data(merged):
        st.info(
            "Insufficient data to generate the letter. "
            "Ensure Patient Name, at least one diagnosis code, and NOE Date are extracted."
        )
        return

    addressee = st.text_area(
        "Addressee (facility name and address)",
        value=st.session_state.get("letter_addressee", ""),
        height=100,
        key="addressee_input",
        placeholder="e.g.,\nNovitas Solutions, Inc.\nP.O. Box 3065\nMechanicsburg, PA 17055-1807",
    )
    st.session_state["letter_addressee"] = addressee

    # --- Custom Template Fill (when template is uploaded) ---
    has_template = st.session_state.get("template_bytes") is not None

    if has_template:
        st.markdown(
            f"**Custom Template:** {st.session_state.get('template_filename', 'uploaded')}"
        )

        if st.button("Fill Custom Template", type="primary"):
            from template_filler import fill_docx_template

            try:
                filled = fill_docx_template(
                    st.session_state["template_bytes"],
                    merged,
                    addressee=addressee,
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

        st.divider()
        st.caption("Or use the built-in letter generator below:")

    # --- Built-in Letter Generator (always available) ---
    if st.button("Generate ADR Letter"):
        # Use first line of addressee for the built-in template
        addressee_first_line = addressee.strip().splitlines()[0] if addressee.strip() else ""
        letter_text = generate_letter(merged, addressee=addressee_first_line)
        st.session_state["generated_letter"] = letter_text

    if st.session_state.get("generated_letter") is not None:
        edited_letter = st.text_area(
            "Edit Letter",
            value=st.session_state["generated_letter"],
            height=500,
            key="letter_editor",
        )
        st.session_state["generated_letter"] = edited_letter

        filename_base = _get_filename_base()

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download as .txt",
                data=edited_letter,
                file_name=f"{filename_base}.txt",
                mime="text/plain",
            )
        with col2:
            # Use the PDF-formatted template for proper alignment
            merged = st.session_state.get("merged_data")
            addressee_val = st.session_state.get("letter_addressee", "").strip().splitlines()
            addressee_first = addressee_val[0] if addressee_val else ""
            pdf_text = generate_letter_for_pdf(merged, addressee=addressee_first)
            pdf_bytes = _generate_pdf(pdf_text)
            if pdf_bytes:
                st.download_button(
                    label="Download as .pdf",
                    data=pdf_bytes,
                    file_name=f"{filename_base}.pdf",
                    mime="application/pdf",
                )
            else:
                st.caption("PDF generation failed. Check the app logs for details.")
