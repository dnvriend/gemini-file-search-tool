"""Tests for query enhancement functionality.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from unittest.mock import MagicMock, patch

import pytest

from gemini_file_search_tool.core.query_enhancement import (
    QueryEnhancementError,
    enhance_query,
    get_enhancement_metadata,
)


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for enhancement."""
    mock_response = MagicMock()

    # Mock response.text (convenience property - Method 1)
    mock_response.text = "Enhanced query with more specific details and source attribution."

    # Mock candidate with enhanced query (Method 2 - fallback)
    mock_part = MagicMock()
    mock_part.text = "Enhanced query with more specific details and source attribution."
    mock_part.has_text = True

    mock_content = MagicMock()
    mock_content.parts = [mock_part]

    mock_candidate = MagicMock()
    mock_candidate.content = mock_content

    mock_response.candidates = [mock_candidate]

    # Mock usage metadata
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 50
    mock_usage.candidates_token_count = 80
    mock_usage.total_token_count = 130

    mock_response.usage_metadata = mock_usage

    return mock_response


def test_enhance_query_generic_mode(mock_gemini_response):
    """Test generic RAG query enhancement."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        enhanced_query, usage_metadata = enhance_query(
            query="How does login work?", enhancement_mode="generic", model="gemini-2.5-flash"
        )

        assert enhanced_query == "Enhanced query with more specific details and source attribution."
        assert usage_metadata["prompt_token_count"] == 50
        assert usage_metadata["candidates_token_count"] == 80
        assert usage_metadata["total_token_count"] == 130

        # Verify API was called
        mock_client.models.generate_content.assert_called_once()


def test_enhance_query_code_rag_mode(mock_gemini_response):
    """Test code-RAG specific query enhancement."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        enhanced_query, usage_metadata = enhance_query(
            query="Where is user data stored?",
            enhancement_mode="code-rag",
            model="gemini-2.5-flash",
        )

        assert len(enhanced_query) > 0
        assert usage_metadata["total_token_count"] == 130


def test_enhance_query_obsidian_mode(mock_gemini_response):
    """Test Obsidian-specific query enhancement."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        enhanced_query, usage_metadata = enhance_query(
            query="Tell me about productivity",
            enhancement_mode="obsidian",
            model="gemini-2.5-flash",
        )

        assert len(enhanced_query) > 0
        assert usage_metadata["total_token_count"] == 130


def test_enhance_query_pro_model(mock_gemini_response):
    """Test enhancement with Pro model."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        enhanced_query, usage_metadata = enhance_query(
            query="Test query", enhancement_mode="generic", model="gemini-2.5-pro"
        )

        # Verify Pro model was passed to API
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]["model"] == "gemini-2.5-pro"


def test_enhance_query_invalid_mode():
    """Test enhancement with invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="Invalid enhancement mode"):
        enhance_query(query="Test query", enhancement_mode="invalid", model="gemini-2.5-flash")


def test_enhance_query_empty_response():
    """Test enhancement with empty response raises QueryEnhancementError."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()

        # Mock empty response - no text and no candidates
        mock_response = MagicMock()
        mock_response.text = None  # No convenience text property
        mock_response.candidates = []  # No candidates
        mock_client.models.generate_content.return_value = mock_response

        mock_get_client.return_value = mock_client

        with pytest.raises(QueryEnhancementError, match="Enhancement produced empty query"):
            enhance_query(query="Test query", enhancement_mode="generic", model="gemini-2.5-flash")


def test_enhance_query_api_failure():
    """Test enhancement with API failure raises QueryEnhancementError."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        with pytest.raises(QueryEnhancementError, match="Query enhancement failed"):
            enhance_query(query="Test query", enhancement_mode="generic", model="gemini-2.5-flash")


def test_get_enhancement_metadata():
    """Test enhancement metadata construction."""
    usage_metadata = {
        "prompt_token_count": 50,
        "candidates_token_count": 80,
        "total_token_count": 130,
    }

    metadata = get_enhancement_metadata(
        original_query="How does login work?",
        enhanced_query="Explain the authentication flow...",
        mode="code-rag",
        model="gemini-2.5-flash",
        usage_metadata=usage_metadata,
    )

    assert metadata["original_query"] == "How does login work?"
    assert metadata["enhanced_query"] == "Explain the authentication flow..."
    assert metadata["mode"] == "code-rag"
    assert metadata["model"] == "gemini-2.5-flash"
    assert metadata["usage_metadata"] == usage_metadata


def test_enhance_query_no_usage_metadata():
    """Test enhancement when API doesn't return usage metadata."""
    with patch("gemini_file_search_tool.core.query_enhancement.get_client") as mock_get_client:
        mock_client = MagicMock()

        # Mock response without usage metadata
        mock_response = MagicMock()
        mock_response.text = "Enhanced query"  # Mock convenience text property
        mock_part = MagicMock()
        mock_part.text = "Enhanced query"
        mock_content = MagicMock()
        mock_content.parts = [mock_part]
        mock_candidate = MagicMock()
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = None

        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        enhanced_query, usage_metadata = enhance_query(
            query="Test query", enhancement_mode="generic", model="gemini-2.5-flash"
        )

        # Should return zero values
        assert usage_metadata["prompt_token_count"] == 0
        assert usage_metadata["candidates_token_count"] == 0
        assert usage_metadata["total_token_count"] == 0
