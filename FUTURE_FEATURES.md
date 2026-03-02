# Future Features

## DOCX Template Upload & Fill

**Goal**: Allow users to upload their own pre-formatted DOCX template (with logo, letterhead, formatting) containing `[placeholder]` fields, and have the app fill those placeholders with extracted data — preserving the original document formatting.

**Format support**: DOCX only. PDF and DOC templates cannot be reliably edited in-place while preserving formatting.

### New File: `template_filler.py`
- **`PLACEHOLDER_MAP`** — dict mapping normalized placeholder names (e.g. `"patient name"`) to lambdas that resolve values from `MergedData`. Reuses logic from `letter.py:_na()` and `letter.py:_format_certification_periods()`.
- **`fill_docx_template(template_bytes, data, addressee) -> bytes`** — opens the DOCX via `python-docx`, iterates all paragraphs (body, tables, headers, footers), finds `[...]` patterns via regex, replaces with resolved values, returns filled DOCX as bytes.
- **`scan_template_placeholders(template_bytes) -> list[dict]`** — scans the template and returns which placeholders were found and whether they map to known fields (used in sidebar for validation feedback).

Placeholders like `[Patient Name]` can be split across multiple Word "runs". The algorithm concatenates all run texts per paragraph, does regex find-and-replace, then puts the result into the first run and clears the rest.

### Supported Placeholders
| Placeholder | MergedData source |
|---|---|
| `[Patient Name]` | `patient_name` |
| `[DOB]` / `[Date of Birth]` | `dob` |
| `[Primary Diagnosis]` | `primary_diagnosis_code` |
| `[Secondary Diagnosis]` / `[Secondary Diagnoses]` | `secondary_diagnoses` |
| `[NOE Date]` / `[Hospice NOE Date]` | `noe_date` |
| `[Terminal Diagnosis]` / `[Hospice Terminal Diagnosis]` | `terminal_diagnosis` |
| `[Certification Periods]` / `[Certification Date(s)]` / `[Certification Dates]` | formatted certification periods |
| `[Date]` | today's date |
| `[Addressee]` | user-provided addressee |
| `[MRN]` | `patient_mrn` |

### Files to Modify
- **`requirements.txt`** — Add `python-docx>=1.1.0`
- **`app.py`** — Add session state keys: `template_bytes`, `template_filename`, `filled_template_bytes`
- **`ui/sidebar.py`** — Add "Letter Template" section with DOCX file uploader and placeholder validation display
- **`ui/letter_view.py`** — Add "Fill Custom Template" button and DOCX download when a template is uploaded (existing hardcoded letter generation remains as fallback)
