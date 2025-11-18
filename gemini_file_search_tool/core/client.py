"""Gemini API client management.

This module provides functions for creating and managing the Gemini API client
instance used throughout the application.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import os

from google import genai
from google.genai import types

# Global client instance for singleton pattern
_client: genai.Client | None = None


class ClientError(Exception):
    """Base exception for client-related errors."""

    pass


class MissingConfigurationError(ClientError):
    """Raised when required configuration is missing."""

    pass


def _is_vertex_ai_configured() -> bool:
    """Check if Vertex AI configuration is present.

    Returns:
        bool: True if GOOGLE_GENAI_USE_VERTEXAI is set to 'true' (case-insensitive)
    """
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower()
    return use_vertex in ("true", "1", "yes")


def _validate_vertex_ai_config() -> None:
    """Validate Vertex AI configuration.

    Raises:
        MissingConfigurationError: If required Vertex AI env vars are missing
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")

    missing = []
    if not project:
        missing.append("GOOGLE_CLOUD_PROJECT")
    if not location:
        missing.append("GOOGLE_CLOUD_LOCATION")

    if missing:
        raise MissingConfigurationError(
            f"Vertex AI configuration incomplete. Missing: {', '.join(missing)}\n"
            "Set them with:\n"
            f"  export GOOGLE_CLOUD_PROJECT='your-project-id'\n"
            f"  export GOOGLE_CLOUD_LOCATION='us-central1'"
        )


def _validate_developer_api_config() -> None:
    """Validate Developer API configuration.

    Raises:
        MissingConfigurationError: If API key is missing
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise MissingConfigurationError(
            "API key not found. Set one of:\n"
            "  export GEMINI_API_KEY='your-api-key'\n"
            "  export GOOGLE_API_KEY='your-api-key'\n\n"
            "Get your API key from: https://aistudio.google.com/app/apikey"
        )


def get_client() -> genai.Client:
    """Get or create the Gemini API client.

    Returns a singleton instance of the Gemini API client. The client is initialized
    on first call and reused for subsequent calls.

    Supports two authentication modes:
    1. Gemini Developer API: Requires GEMINI_API_KEY or GOOGLE_API_KEY
    2. Vertex AI: Requires GOOGLE_GENAI_USE_VERTEXAI=true, GOOGLE_CLOUD_PROJECT,
       and GOOGLE_CLOUD_LOCATION

    Returns:
        genai.Client: The Gemini API client instance

    Raises:
        MissingConfigurationError: If required configuration is missing
    """
    global _client
    if _client is None:
        # Configure retry options to handle transient errors but fail fast on 400s
        http_options = types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                attempts=3,
                initial_delay=1.0,
                http_status_codes=[429, 500, 502, 503, 504],  # Retry only transient errors
            )
        )

        # Check which configuration mode is being used
        if _is_vertex_ai_configured():
            # Vertex AI mode
            _validate_vertex_ai_config()
            # Client will automatically use Vertex AI env vars
            _client = genai.Client(http_options=http_options)
        else:
            # Developer API mode
            _validate_developer_api_config()
            # Get API key (GOOGLE_API_KEY takes precedence)
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            _client = genai.Client(api_key=api_key, http_options=http_options)

    return _client


def reset_client() -> None:
    """Reset the global client instance.

    This function is primarily useful for testing, allowing tests to reset
    the client state between test cases.
    """
    global _client
    _client = None
