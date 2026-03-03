"""Constants, system prompts, and response schemas."""

MODEL_NAME = "gemini-3-flash-preview"

SUPPORTED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "tiff"]

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

DEFAULT_CLAIM_PROMPT = """\
System Persona: You are an expert Medical Billing Auditor specializing in CMS-1500 form analysis.

Task: Analyze the provided OCR text from a Claim Form and extract specific fields into a structured JSON format.

Reference Fields (For UI Display):
- Patient Name: Extract from Box 2.
- Date of Birth: Extract from Box 3 (Format: MM/DD/YYYY).
- Address Components: Extract City, State, and Zip Code from Box 5.

ADR Letter Fields:
- Primary Diagnosis Code: Extract the code associated with 'A' in Box 21.
- Secondary Diagnoses: Extract any codes associated with 'B', 'C', or 'D' in Box 21.

Extraction Rules:
- If a field is illegible or missing, return null.
- Clean any OCR "noise" (e.g., ignore random symbols or partial words like "PICA" or "FICA").
- For each field, also return the page number where the value was found using the "--- Page X ---" markers in the OCR text. Use the field name with a "_page" suffix (e.g., "patient_name_page": "1").
- Return a single JSON object."""

DEFAULT_PROGRESS_PROMPT = """\
System Persona: You are a Clinical Documentation Specialist and CDI Expert.

Task: Analyze the clinical Progress Note OCR text and extract the following clinical and demographic data into JSON.

Reference Fields (For UI Display):
- Patient Identity: Full Patient Name and Date of Birth.
- MRN: Extract the Medical Record Number.
- Hospice Status: Specifically extract the value for "Is this patient in Hospice" (Yes/No).

Clinical Measurements:
- Locate the Focused Wound Exam table.
- Extract the Length (cm), Width (cm), and Depth (cm).

Extraction Rules:
1. Do not "calculate" or "guess" measurements; only extract the literal values provided in the text (e.g., "5.00", "7.50", "0.8").
2. Ensure the "Hospice Status" is captured as a boolean or string based on the document's encounter information.
3. Clean any Tesseract-specific artifacts (e.g., tags) before finalizing the JSON.
4. For each field, also return the page number where the value was found using the "--- Page X ---" markers in the OCR text. Use the field name with a "_page" suffix (e.g., "patient_name_page": "1")."""

HOSPICE_STAGE1_PROMPT = """\
System Persona: You are a medical document analysis specialist.

Task: You are given OCR text from a multi-page Hospice certification document. Create a detailed document map identifying all sections.

For each section found, provide:
- section_name: The name/title of the section (e.g., "Face Sheet", "Certification of Terminal Illness", "Election Statement", "Plan of Care")
- page_numbers: Which page(s) this section spans (based on "--- Page X ---" markers in the text)
- description: A brief description of the section's content
- key_content: Extract the most important data points from each section, including:
  - Any dates mentioned (admission dates, certification dates, benefit period dates)
  - Any diagnosis information
  - Patient identifiers
  - Provider names and NPIs

Pay special attention to identifying sections that contain:
1. "Face Sheet" or admission information
2. "Certification of Terminal Illness" (CTI)
3. "Notice of Election" (NOE) or "Election Statement"
4. Benefit Period information
5. Any sections mentioning "SOC" (Start of Care) dates

Return a JSON object with a "sections" array."""

HOSPICE_STAGE2_PROMPT = """\
System Persona: You are a medical document data extraction specialist.

Task: You are given OCR text from a Hospice certification document, along with a document map that identifies the key sections.

Using the document map as a guide to locate relevant sections, extract the following:

1. CERTIFICATION PERIODS:
   Extract all certification/benefit periods found in the document. For each period, provide:
   - period_name: e.g., "Benefit Period 1", "Benefit Period 2", "Initial Certification"
   - start_date: Start date (MM/DD/YYYY)
   - end_date: End date (MM/DD/YYYY)
   - page: The page number where this period was found

2. TERMINAL DIAGNOSIS:
   - terminal_diagnosis: The primary terminal/hospice diagnosis (the condition qualifying the patient for hospice care). Include the ICD-10 code if present.

3. SECONDARY/RELATED DIAGNOSES:
   - hospice_secondary_diagnoses: Look for sections explicitly labeled "Secondary Diagnoses" or "Related Diagnoses" in the document. Only extract diagnoses (ICD-10 codes and descriptions) from these labeled sections. Return as a comma-separated string. If no section with these exact labels exists, return "N/A".

4. NOE DATE (Notice of Election Date):
   - Apply this logic in order:
     a. Find "Benefit Period 1" in the certification periods. If found, the start_date of Benefit Period 1 is the NOE date.
     b. If Benefit Period 1 is not found, look for a "Start of Care" (SOC) date anywhere in the document and use that as the NOE date.
     c. If neither is found, return null.
   - noe_date: The determined NOE date (MM/DD/YYYY)
   - noe_date_source: Either "Benefit Period 1" or "SOC Date" indicating which was used.

Page Numbers:
- For terminal_diagnosis, hospice_secondary_diagnoses, and noe_date, also return the page number where each was found using the "--- Page X ---" markers. Use the field name with a "_page" suffix (e.g., "terminal_diagnosis_page": "3").

DOCUMENT MAP FOR REFERENCE:
{document_map_json}

Return all fields in a single JSON object."""

# ---------------------------------------------------------------------------
# Response Schemas (for Gemini JSON mode)
# ---------------------------------------------------------------------------

CLAIM_FORM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "patient_name": {"type": "STRING", "description": "Patient name from Box 2"},
        "patient_name_page": {"type": "STRING", "description": "Page number where patient name was found"},
        "dob": {"type": "STRING", "description": "Date of birth from Box 3 (MM/DD/YYYY)"},
        "dob_page": {"type": "STRING", "description": "Page number where DOB was found"},
        "city": {"type": "STRING", "description": "City from Box 5"},
        "city_page": {"type": "STRING", "description": "Page number where city was found"},
        "state": {"type": "STRING", "description": "State from Box 5"},
        "state_page": {"type": "STRING", "description": "Page number where state was found"},
        "zip_code": {"type": "STRING", "description": "ZIP code from Box 5"},
        "zip_code_page": {"type": "STRING", "description": "Page number where ZIP was found"},
        "primary_diagnosis_code": {
            "type": "STRING",
            "description": "ICD-10 code from Box 21 line A",
        },
        "primary_diagnosis_code_page": {"type": "STRING", "description": "Page number where primary DX was found"},
        "secondary_diagnoses": {
            "type": "STRING",
            "description": "ICD-10 codes from Box 21 lines B/C/D, comma-separated",
        },
        "secondary_diagnoses_page": {"type": "STRING", "description": "Page number where secondary DX was found"},
    },
    "required": [
        "patient_name",
        "dob",
        "city",
        "state",
        "zip_code",
        "primary_diagnosis_code",
        "secondary_diagnoses",
    ],
}

PROGRESS_NOTE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "patient_name": {"type": "STRING", "description": "Full patient name"},
        "patient_name_page": {"type": "STRING", "description": "Page number where patient name was found"},
        "dob": {"type": "STRING", "description": "Date of birth (MM/DD/YYYY)"},
        "dob_page": {"type": "STRING", "description": "Page number where DOB was found"},
        "patient_mrn": {"type": "STRING", "description": "Medical Record Number"},
        "patient_mrn_page": {"type": "STRING", "description": "Page number where MRN was found"},
        "hospice_status": {
            "type": "STRING",
            "description": "Is this patient in Hospice (Yes/No)",
        },
        "hospice_status_page": {"type": "STRING", "description": "Page number where hospice status was found"},
        "wound_length": {"type": "STRING", "description": "Wound length in cm"},
        "wound_length_page": {"type": "STRING", "description": "Page number where wound length was found"},
        "wound_width": {"type": "STRING", "description": "Wound width in cm"},
        "wound_width_page": {"type": "STRING", "description": "Page number where wound width was found"},
        "wound_depth": {"type": "STRING", "description": "Wound depth in cm"},
        "wound_depth_page": {"type": "STRING", "description": "Page number where wound depth was found"},
    },
    "required": [
        "patient_name",
        "dob",
        "patient_mrn",
        "hospice_status",
        "wound_length",
        "wound_width",
        "wound_depth",
    ],
}

HOSPICE_STAGE1_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sections": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "section_name": {"type": "STRING"},
                    "page_numbers": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "key_content": {
                        "type": "OBJECT",
                        "properties": {
                            "dates": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "diagnoses": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                            "identifiers": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                            },
                        },
                    },
                },
                "required": ["section_name", "page_numbers", "description"],
            },
        },
    },
    "required": ["sections"],
}

HOSPICE_STAGE2_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "certification_periods": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "period_name": {"type": "STRING"},
                    "start_date": {"type": "STRING"},
                    "end_date": {"type": "STRING"},
                    "page": {"type": "STRING", "description": "Page number where this period was found"},
                },
                "required": ["period_name", "start_date", "end_date"],
            },
        },
        "terminal_diagnosis": {"type": "STRING"},
        "terminal_diagnosis_page": {"type": "STRING", "description": "Page number where terminal diagnosis was found"},
        "hospice_secondary_diagnoses": {
            "type": "STRING",
            "description": "Secondary/related diagnoses from hospice document, comma-separated ICD-10 codes and descriptions",
        },
        "hospice_secondary_diagnoses_page": {"type": "STRING", "description": "Page number where secondary diagnoses were found"},
        "noe_date": {"type": "STRING"},
        "noe_date_page": {"type": "STRING", "description": "Page number where NOE date was found"},
        "noe_date_source": {"type": "STRING"},
    },
    "required": [
        "certification_periods",
        "terminal_diagnosis",
        "noe_date",
        "noe_date_source",
    ],
}
