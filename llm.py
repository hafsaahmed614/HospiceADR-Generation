"""Vertex AI Gemini client wrapper with JSON structured output (HIPAA-compliant)."""

import json
import os
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types
from google.oauth2 import service_account

import config

# Resolve paths relative to this file's directory (the project root)
_PROJECT_DIR = Path(__file__).resolve().parent

# Vertex AI configuration
_VERTEX_PROJECT = "gen-lang-client-0813470630"
_VERTEX_LOCATION = "us-central1"
_DEFAULT_KEY_FILE = "gen-lang-client-0813470630-54bcbcbd9e1f.json"


class ExtractionError(Exception):
    """Raised when LLM extraction fails."""


@st.cache_resource
def _get_client() -> genai.Client:
    """Load service account credentials and return a Vertex AI Gemini client."""
    key_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(_PROJECT_DIR / _DEFAULT_KEY_FILE),
    )

    if not Path(key_path).exists():
        raise ExtractionError(
            f"Service account key not found at '{key_path}'. "
            "Place the JSON key in the project root or set GOOGLE_APPLICATION_CREDENTIALS."
        )

    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    return genai.Client(
        vertexai=True,
        project=_VERTEX_PROJECT,
        location=_VERTEX_LOCATION,
        credentials=credentials,
    )


def extract_json(
    system_prompt: str,
    user_content: str,
    response_schema: dict,
    model: str = config.MODEL_NAME,
) -> dict:
    """Send a prompt to Gemini and return parsed JSON matching the schema.

    Parameters
    ----------
    system_prompt : str
        The system instruction for the extraction task.
    user_content : str
        The OCR text or other content to process.
    response_schema : dict
        The expected JSON response schema.
    model : str
        The Gemini model to use.

    Returns
    -------
    dict
        Parsed JSON response from the model.

    Raises
    ------
    ExtractionError
        If the API call or JSON parsing fails.
    """
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Failed to parse LLM response as JSON: {e}") from e
    except Exception as e:
        raise ExtractionError(f"LLM extraction failed: {e}") from e


def generate_text(
    system_prompt: str,
    user_content: str,
    model: str = config.MODEL_NAME,
) -> str:
    """Send a prompt to Gemini and return plain text response.

    Used for letter generation where free-form text is needed.
    """
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
    except Exception as e:
        raise ExtractionError(f"LLM text generation failed: {e}") from e
