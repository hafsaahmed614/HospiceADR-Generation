"""Gemini client wrapper with JSON structured output."""

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

import config

# Resolve .env relative to this file's directory (the project root)
_PROJECT_DIR = Path(__file__).resolve().parent


class ExtractionError(Exception):
    """Raised when LLM extraction fails."""


@st.cache_resource
def _get_client() -> genai.Client:
    """Load API key from .env and return a configured Gemini client."""
    # Try .env file first (local dev), then Streamlit secrets (cloud deployment)
    load_dotenv(dotenv_path=_PROJECT_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (KeyError, FileNotFoundError):
            pass
    if not api_key:
        raise ExtractionError(
            "GEMINI_API_KEY not found. Set it in .env (local) or Streamlit Secrets (cloud)."
        )
    return genai.Client(api_key=api_key)


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
