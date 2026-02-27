"""ADR response letter generation."""

from datetime import date

import config
from models import MergedData


def letter_has_sufficient_data(data: MergedData) -> bool:
    """Check whether minimum fields are populated to generate a meaningful letter."""
    has_patient = bool(data.patient_name)
    has_diagnosis = bool(data.primary_diagnosis_code) or bool(data.terminal_diagnosis)
    has_hospice = bool(data.noe_date)
    return has_patient and has_diagnosis and has_hospice


def _format_certification_periods(data: MergedData) -> str:
    """Format certification periods as date ranges only (no period names)."""
    if not data.certification_periods:
        return "N/A"
    parts = []
    for period in data.certification_periods:
        parts.append(f"{period.start_date} - {period.end_date}")
    return "; ".join(parts)


def _na(value):
    """Return 'N/A' if the value is empty, None, or the string 'null'."""
    if not value or str(value).strip().lower() == "null":
        return "N/A"
    return value


def _fill_template(template: str, data: MergedData, addressee: str) -> str:
    """Fill a letter template string with extracted data."""
    return template.format(
        addressee=addressee or "[Addressee]",
        date=date.today().strftime("%m/%d/%Y"),
        patient_name=_na(data.patient_name),
        dob=_na(data.dob),
        primary_diagnosis=_na(data.primary_diagnosis_code),
        secondary_diagnosis=_na(data.secondary_diagnoses),
        noe_date=_na(data.noe_date),
        terminal_diagnosis=_na(data.terminal_diagnosis),
        certification_periods=_format_certification_periods(data),
    )


def generate_letter(data: MergedData, addressee: str = "") -> str:
    """Generate the clean display version of the letter (for UI text area)."""
    return _fill_template(config.LETTER_DISPLAY_TEMPLATE, data, addressee)


def generate_letter_for_pdf(data: MergedData, addressee: str = "") -> str:
    """Generate the PDF-formatted version with alignment whitespace."""
    return _fill_template(config.LETTER_TEMPLATE, data, addressee)
