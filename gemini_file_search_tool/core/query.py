"""Query operations for file search stores.

This module provides functions for querying documents in Gemini file search stores
using natural language with automatic citations. Enables both traditional document
RAG and Code-RAG (semantic code search).

Key Features:
- Natural language queries with contextual answers
- Automatic source attribution and grounding metadata
- Support for Flash (fast) and Pro (complex) models
- Metadata filtering for targeted searches
- Token usage tracking and cost estimation

Code-RAG Use Case:
Query uploaded codebases with natural language to understand architecture,
find implementations, and discover patterns without manual code search.
Perfect for codebase onboarding, architecture analysis, and AI coding assistants.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from typing import Any

from google.genai import types

from gemini_file_search_tool.core.client import get_client


class QueryError(Exception):
    """Base exception for query-related errors."""

    pass


def query_store(
    store_name: str,
    prompt: str,
    model: str = "gemini-2.5-flash",
    metadata_filter: str | None = None,
    include_grounding: bool = False,
) -> dict[str, Any]:
    """Query documents in a file search store.

    Args:
        store_name: Store name (full resource name or ID)
        prompt: Query prompt
        model: Model to use (default: 'gemini-2.5-flash', or 'gemini-2.5-pro')
        metadata_filter: Metadata filter expression (optional, e.g., 'author=Robert Graves')
        include_grounding: Include grounding metadata in response (default: False)

    Returns:
        Dictionary containing:
            - response_text: Generated response text
            - usage_metadata: Token usage statistics (prompt, candidates, total counts)
            - grounding_metadata: Grounding metadata with citations (if include_grounding=True)

    Raises:
        QueryError: If query fails
    """
    try:
        client = get_client()

        # Build file search config
        file_search_config = types.FileSearch(file_search_store_names=[store_name])

        # Add metadata filter if provided
        if metadata_filter:
            file_search_config.metadata_filter = metadata_filter

        # Generate content
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(file_search=file_search_config)]),
        )

        # Extract response text
        response_text = ""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                parts = [
                    str(part.text)
                    for part in candidate.content.parts
                    if hasattr(part, "text") and part.text is not None
                ]
                response_text = "".join(parts)

        # Build output
        output: dict[str, Any] = {
            "response_text": response_text,
        }

        # Extract usage metadata
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            output["usage_metadata"] = {
                "prompt_token_count": getattr(usage, "prompt_token_count", 0),
                "candidates_token_count": getattr(usage, "candidates_token_count", 0),
                "total_token_count": getattr(usage, "total_token_count", 0),
            }
        else:
            output["usage_metadata"] = None

        # Extract grounding metadata if requested
        if include_grounding and response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata"):
                grounding_metadata = candidate.grounding_metadata

                # Convert grounding metadata to dict
                grounding_dict: dict[str, Any] = {}
                if grounding_metadata is not None and hasattr(
                    grounding_metadata, "grounding_chunks"
                ):
                    grounding_chunks = grounding_metadata.grounding_chunks
                    if grounding_chunks is not None:
                        chunks = []
                        for chunk in grounding_chunks:
                            chunk_dict: dict[str, Any] = {}
                            if hasattr(chunk, "retrieved_context"):
                                ctx = chunk.retrieved_context
                                chunk_dict["retrieved_context"] = {
                                    "title": getattr(ctx, "title", None),
                                    "text": getattr(ctx, "text", None),
                                }
                            if hasattr(chunk, "score"):
                                chunk_dict["score"] = chunk.score
                            chunks.append(chunk_dict)
                        grounding_dict["grounding_chunks"] = chunks
                output["grounding_metadata"] = grounding_dict

        return output
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            raise QueryError(f"Store '{store_name}' not found") from e
        raise QueryError(f"Query failed: {error_msg}") from e
