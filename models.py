"""Pydantic data models and merge logic for extracted document data."""

from typing import List, Optional

from pydantic import BaseModel


class ClaimFormData(BaseModel):
    patient_name: Optional[str] = None
    patient_name_page: Optional[str] = None
    dob: Optional[str] = None
    dob_page: Optional[str] = None
    city: Optional[str] = None
    city_page: Optional[str] = None
    state: Optional[str] = None
    state_page: Optional[str] = None
    zip_code: Optional[str] = None
    zip_code_page: Optional[str] = None
    primary_diagnosis_code: Optional[str] = None
    primary_diagnosis_code_page: Optional[str] = None
    secondary_diagnoses: Optional[str] = None
    secondary_diagnoses_page: Optional[str] = None


class ProgressNoteData(BaseModel):
    patient_name: Optional[str] = None
    patient_name_page: Optional[str] = None
    dob: Optional[str] = None
    dob_page: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_mrn_page: Optional[str] = None
    hospice_status: Optional[str] = None
    hospice_status_page: Optional[str] = None
    wound_length: Optional[str] = None
    wound_length_page: Optional[str] = None
    wound_width: Optional[str] = None
    wound_width_page: Optional[str] = None
    wound_depth: Optional[str] = None
    wound_depth_page: Optional[str] = None


class HospiceSectionContent(BaseModel):
    dates: List[str] = []
    diagnoses: List[str] = []
    identifiers: List[str] = []


class HospiceSection(BaseModel):
    section_name: str
    page_numbers: str
    description: str
    key_content: Optional[HospiceSectionContent] = None


class HospiceDocumentMap(BaseModel):
    sections: List[HospiceSection] = []


class CertificationPeriod(BaseModel):
    period_name: str
    start_date: str
    end_date: str
    page: Optional[str] = None


class HospiceData(BaseModel):
    noe_date: Optional[str] = None
    noe_date_page: Optional[str] = None
    noe_date_source: Optional[str] = None
    terminal_diagnosis: Optional[str] = None
    terminal_diagnosis_page: Optional[str] = None
    hospice_secondary_diagnoses: Optional[str] = None
    hospice_secondary_diagnoses_page: Optional[str] = None
    certification_periods: List[CertificationPeriod] = []


class MergedData(BaseModel):
    # Patient info (Progress Note priority, fallback to Claim Form)
    patient_name: Optional[str] = None
    patient_name_page: Optional[str] = None
    dob: Optional[str] = None
    dob_page: Optional[str] = None

    # From Progress Note only
    patient_mrn: Optional[str] = None
    patient_mrn_page: Optional[str] = None
    hospice_status: Optional[str] = None
    hospice_status_page: Optional[str] = None
    wound_length: Optional[str] = None
    wound_length_page: Optional[str] = None
    wound_width: Optional[str] = None
    wound_width_page: Optional[str] = None
    wound_depth: Optional[str] = None
    wound_depth_page: Optional[str] = None

    # From Claim Form only
    city: Optional[str] = None
    city_page: Optional[str] = None
    state: Optional[str] = None
    state_page: Optional[str] = None
    zip_code: Optional[str] = None
    zip_code_page: Optional[str] = None
    primary_diagnosis_code: Optional[str] = None
    primary_diagnosis_code_page: Optional[str] = None
    secondary_diagnoses: Optional[str] = None
    secondary_diagnoses_page: Optional[str] = None

    # From Hospice Document
    noe_date: Optional[str] = None
    noe_date_page: Optional[str] = None
    noe_date_source: Optional[str] = None
    terminal_diagnosis: Optional[str] = None
    terminal_diagnosis_page: Optional[str] = None
    hospice_secondary_diagnoses: Optional[str] = None
    hospice_secondary_diagnoses_page: Optional[str] = None
    certification_periods: List[CertificationPeriod] = []


def merge_data(
    claim: Optional[ClaimFormData],
    progress: Optional[ProgressNoteData],
    hospice: Optional[HospiceData],
) -> MergedData:
    """Merge extracted data with Progress Note priority over Claim Form for shared fields."""
    merged = MergedData()

    # Patient name & DOB: Progress Note takes priority
    if progress and progress.patient_name:
        merged.patient_name = progress.patient_name
        merged.patient_name_page = progress.patient_name_page
    elif claim and claim.patient_name:
        merged.patient_name = claim.patient_name
        merged.patient_name_page = claim.patient_name_page

    if progress and progress.dob:
        merged.dob = progress.dob
        merged.dob_page = progress.dob_page
    elif claim and claim.dob:
        merged.dob = claim.dob
        merged.dob_page = claim.dob_page

    # Progress Note only fields
    if progress:
        merged.patient_mrn = progress.patient_mrn
        merged.patient_mrn_page = progress.patient_mrn_page
        merged.hospice_status = progress.hospice_status
        merged.hospice_status_page = progress.hospice_status_page
        merged.wound_length = progress.wound_length
        merged.wound_length_page = progress.wound_length_page
        merged.wound_width = progress.wound_width
        merged.wound_width_page = progress.wound_width_page
        merged.wound_depth = progress.wound_depth
        merged.wound_depth_page = progress.wound_depth_page

    # Claim Form only fields
    if claim:
        merged.city = claim.city
        merged.city_page = claim.city_page
        merged.state = claim.state
        merged.state_page = claim.state_page
        merged.zip_code = claim.zip_code
        merged.zip_code_page = claim.zip_code_page
        merged.primary_diagnosis_code = claim.primary_diagnosis_code
        merged.primary_diagnosis_code_page = claim.primary_diagnosis_code_page
        merged.secondary_diagnoses = claim.secondary_diagnoses
        merged.secondary_diagnoses_page = claim.secondary_diagnoses_page

    # Hospice fields
    if hospice:
        merged.noe_date = hospice.noe_date
        merged.noe_date_page = hospice.noe_date_page
        merged.noe_date_source = hospice.noe_date_source
        merged.terminal_diagnosis = hospice.terminal_diagnosis
        merged.terminal_diagnosis_page = hospice.terminal_diagnosis_page
        merged.hospice_secondary_diagnoses = hospice.hospice_secondary_diagnoses
        merged.hospice_secondary_diagnoses_page = hospice.hospice_secondary_diagnoses_page
        merged.certification_periods = hospice.certification_periods

    return merged
