"""Query enhancement for RAG optimization.

This module provides query enhancement functionality using Gemini LLM to optimize
user queries for better RAG retrieval results. Supports three enhancement modes:
- Generic RAG: General document retrieval optimization
- Code-RAG: Code search and semantic code understanding
- Obsidian: Personal knowledge management and note systems

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from typing import Any, Literal

from google.genai import types

from gemini_file_search_tool.core.client import get_client
from gemini_file_search_tool.prompts import (
    CODE_RAG_ENHANCEMENT_TEMPLATE,
    GENERIC_ENHANCEMENT_TEMPLATE,
    OBSIDIAN_ENHANCEMENT_TEMPLATE,
)


class QueryEnhancementError(Exception):
    """Base exception for query enhancement errors."""

    pass


def enhance_query(
    query: str,
    enhancement_mode: Literal["generic", "code-rag", "obsidian"],
    model: Literal["gemini-2.5-flash", "gemini-2.5-pro"] = "gemini-2.5-flash",
) -> tuple[str, dict[str, int]]:
    """Enhance query using Gemini LLM for optimal RAG retrieval.

    Args:
        query: Original user query to enhance
        enhancement_mode: Enhancement strategy to apply:
            - 'generic': General RAG optimization
            - 'code-rag': Code search optimization
            - 'obsidian': Personal knowledge management optimization
        model: Model to use for enhancement (default: gemini-2.5-flash)

    Returns:
        Tuple of (enhanced_query, usage_metadata):
            - enhanced_query: Optimized query string
            - usage_metadata: Dict with prompt_token_count, candidates_token_count,
              total_token_count

    Raises:
        QueryEnhancementError: If enhancement fails
        ValueError: If enhancement_mode is invalid
    """
    # Select appropriate template
    template_map = {
        "generic": GENERIC_ENHANCEMENT_TEMPLATE,
        "code-rag": CODE_RAG_ENHANCEMENT_TEMPLATE,
        "obsidian": OBSIDIAN_ENHANCEMENT_TEMPLATE,
    }

    if enhancement_mode not in template_map:
        raise ValueError(
            f"Invalid enhancement mode '{enhancement_mode}'. "
            f"Must be one of: {', '.join(template_map.keys())}"
        )

    template = template_map[enhancement_mode]
    enhancement_prompt = template.format(user_query=query)

    try:
        client = get_client()

        # Generate enhanced query
        response = client.models.generate_content(
            model=model,
            contents=enhancement_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,  # Lower temperature for consistent enhancement
                max_output_tokens=2048,  # Increased limit for code-rag queries
            ),
        )

        # Extract enhanced query - try multiple methods
        enhanced_query = ""

        # Method 1: Try response.text (convenience property)
        if hasattr(response, "text") and response.text:
            enhanced_query = response.text.strip()

        # Method 2: Try candidates[0].content.parts
        if not enhanced_query and response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                parts = [
                    str(part.text)
                    for part in candidate.content.parts
                    if hasattr(part, "text") and part.text is not None
                ]
                enhanced_query = "".join(parts).strip()

        if not enhanced_query:
            # Provide detailed error for debugging
            error_details = "Enhancement produced empty query. "

            # Check if it was blocked by safety filters
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    error_details += f"Finish reason: {candidate.finish_reason}. "
                if hasattr(candidate, "safety_ratings") and candidate.safety_ratings:
                    error_details += f"Safety ratings: {candidate.safety_ratings}. "

            error_details += "Response structure: "
            if response.candidates:
                candidate = response.candidates[0]
                error_details += f"candidates={len(response.candidates)}, "
                error_details += f"content={candidate.content is not None}, "
                if candidate.content:
                    error_details += (
                        f"parts={len(candidate.content.parts) if candidate.content.parts else 0}"
                    )
            else:
                error_details += "no candidates"

            raise QueryEnhancementError(error_details)

        # Extract usage metadata
        usage_metadata: dict[str, int] = {
            "prompt_token_count": 0,
            "candidates_token_count": 0,
            "total_token_count": 0,
        }

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            usage_metadata = {
                "prompt_token_count": getattr(usage, "prompt_token_count", 0),
                "candidates_token_count": getattr(usage, "candidates_token_count", 0),
                "total_token_count": getattr(usage, "total_token_count", 0),
            }

        return enhanced_query, usage_metadata

    except QueryEnhancementError:
        raise
    except Exception as e:
        error_msg = str(e)
        raise QueryEnhancementError(f"Query enhancement failed: {error_msg}") from e


def get_enhancement_metadata(
    original_query: str,
    enhanced_query: str,
    mode: str,
    model: str,
    usage_metadata: dict[str, int],
) -> dict[str, Any]:
    """Build enhancement metadata dictionary for output.

    Args:
        original_query: Original user query
        enhanced_query: Enhanced query result
        mode: Enhancement mode used
        model: Model used for enhancement
        usage_metadata: Token usage statistics

    Returns:
        Dictionary with enhancement metadata
    """
    return {
        "original_query": original_query,
        "enhanced_query": enhanced_query,
        "mode": mode,
        "model": model,
        "usage_metadata": usage_metadata,
    }
