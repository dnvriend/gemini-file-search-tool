"""CLI commands for querying documents.

This module provides Click commands for querying documents in Gemini file search stores
using natural language with automatic citations.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import sys
from typing import Any, Literal

import click

from gemini_file_search_tool.core.client import MissingConfigurationError
from gemini_file_search_tool.core.query import QueryError
from gemini_file_search_tool.core.query import query_store as core_query
from gemini_file_search_tool.core.query_enhancement import (
    QueryEnhancementError,
    enhance_query,
    get_enhancement_metadata,
)
from gemini_file_search_tool.utils import (
    aggregate_costs,
    estimate_cost,
    normalize_store_name,
    output_json,
    print_verbose,
)


@click.command("query")
@click.argument("prompt", required=True)
@click.option(
    "--store",
    "-s",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
@click.option(
    "--enhance-mode",
    type=click.Choice(["generic", "code-rag", "obsidian"], case_sensitive=False),
    help="Query enhancement mode: generic (general docs), code-rag (code search), obsidian (PKM)",
)
@click.option(
    "--enhancement-model",
    type=click.Choice(["flash", "pro"], case_sensitive=False),
    default="flash",
    help="Model for query enhancement (default: flash)",
)
@click.option(
    "--query-model",
    type=click.Choice(["flash", "pro"], case_sensitive=False),
    default="flash",
    help="Model for RAG query (default: flash)",
)
@click.option(
    "--metadata-filter",
    help="Metadata filter expression (e.g., 'author=Robert Graves')",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (-v INFO, -vv DEBUG, -vvv TRACE)",
)
@click.option(
    "--query-grounding-metadata",
    is_flag=True,
    default=False,
    help="Include grounding metadata in the response JSON",
)
@click.option(
    "--show-cost",
    is_flag=True,
    default=False,
    help="Include estimated cost calculation in the response JSON",
)
@click.option(
    "--show-enhancement",
    is_flag=True,
    help="Display enhanced query before execution",
)
@click.option(
    "--dry-run-enhancement",
    is_flag=True,
    help="Show enhancement without executing RAG query",
)
def query(
    prompt: str,
    store_name: str,
    enhance_mode: str | None,
    enhancement_model: str,
    query_model: str,
    metadata_filter: str | None,
    verbose: int,
    query_grounding_metadata: bool,
    show_cost: bool,
    show_enhancement: bool,
    dry_run_enhancement: bool,
) -> None:
    """Query documents in a file search store using natural language.

    PROMPT is the natural language query to ask (positional argument).

    Returns AI-generated answers with automatic citations from your documents.
    Supports query enhancement for improved RAG retrieval results.

    Examples:

    \b
        # Basic query with Flash model (default)
        gemini-file-search-tool query "What are the main findings?" \\
            --store "research-papers"

    \b
        # Use Pro model for complex queries
        gemini-file-search-tool query "Compare methodologies" \\
            --store "papers" --query-model pro

    \b
        # Query with generic enhancement
        gemini-file-search-tool query "How does authentication work?" \\
            --store "docs" --enhance-mode generic

    \b
        # Code-specific enhancement with Pro model
        gemini-file-search-tool query "Find login code" \\
            --store "codebase" --enhance-mode code-rag --enhancement-model pro

    \b
        # Obsidian enhancement with cost tracking
        gemini-file-search-tool query "productivity tips" \\
            --store "notes" --enhance-mode obsidian --show-cost -v

    \b
        # Preview enhancement without executing query
        gemini-file-search-tool query "database schema" \\
            --store "docs" --enhance-mode generic --dry-run-enhancement

    \b
        # Query with metadata filter
        gemini-file-search-tool query "Summarize the results" \\
            --store "papers" --metadata-filter "author=Robert Graves"

    \b
    Output Format:
        Returns JSON with answer, token usage, and optional fields:
        {
          "response_text": "The main findings are...",
          "enhancement": {...},         // if enhancement used
          "usage_metadata": {
            "prompt_token_count": 150,
            "candidates_token_count": 320,
            "total_token_count": 470
          },
          "grounding_metadata": {...},  // if --query-grounding-metadata used
          "estimated_cost": {            // if --show-cost used
            "enhancement": {...},
            "query": {...},
            "total_cost_usd": 0.000135,
            "currency": "USD"
          }
        }
    """
    try:
        normalized_name = normalize_store_name(store_name)

        # Map enhance_mode to internal enhancement_mode_type
        enhancement_mode_type: Literal["generic", "code-rag", "obsidian"] | None = None
        if enhance_mode:
            enhancement_mode_type = enhance_mode  # type: ignore

        # Enhancement phase
        enhancement_metadata: dict[str, Any] | None = None
        enhancement_cost_estimate: dict[str, Any] | None = None
        original_prompt = prompt
        query_prompt = prompt  # This will be updated if enhancement is used

        if enhancement_mode_type:
            # Map model names to full model identifiers
            enhancement_model_name: Literal["gemini-2.5-flash", "gemini-2.5-pro"] = (
                "gemini-2.5-pro" if enhancement_model == "pro" else "gemini-2.5-flash"
            )

            print_verbose(f'Original query: "{original_prompt}"', verbose > 0)
            print_verbose(
                f"Enhancement mode: {enhancement_mode_type} ({enhancement_model_name})",
                verbose > 0,
            )

            try:
                # Enhance query
                enhanced_query, enhancement_usage = enhance_query(
                    query=original_prompt,
                    enhancement_mode=enhancement_mode_type,
                    model=enhancement_model_name,
                )
                query_prompt = enhanced_query

                # Build enhancement metadata
                enhancement_metadata = get_enhancement_metadata(
                    original_query=original_prompt,
                    enhanced_query=enhanced_query,
                    mode=enhancement_mode_type,
                    model=enhancement_model_name,
                    usage_metadata=enhancement_usage,
                )

                # Display enhanced query if requested
                if show_enhancement or verbose > 0:
                    click.echo(f'[INFO] Enhanced query: "{enhanced_query}"', err=True)

                # Display enhancement token usage
                if verbose > 0:
                    prompt_tokens = enhancement_usage.get("prompt_token_count", 0)
                    candidates_tokens = enhancement_usage.get("candidates_token_count", 0)
                    total_tokens = enhancement_usage.get("total_token_count", 0)
                    click.echo(
                        f"[INFO] Enhancement tokens: {prompt_tokens} input + "
                        f"{candidates_tokens} output = {total_tokens} total",
                        err=True,
                    )

                # Calculate enhancement cost if requested
                if show_cost:
                    enhancement_cost_estimate = estimate_cost(
                        enhancement_usage, enhancement_model_name
                    )
                    if enhancement_cost_estimate and verbose > 0:
                        cost = enhancement_cost_estimate["total_cost_usd"]
                        click.echo(f"[INFO] Enhancement cost: ${cost:.8f} USD", err=True)

            except QueryEnhancementError as e:
                click.echo(f"Error: Query enhancement failed: {str(e)}", err=True)
                sys.exit(1)

            # Dry-run enhancement mode: show enhancement and exit
            if dry_run_enhancement:
                output_data: dict[str, Any] = {"enhancement": enhancement_metadata}
                if show_cost and enhancement_cost_estimate:
                    output_data["estimated_cost"] = enhancement_cost_estimate
                output_json(output_data)
                return

        # Execute RAG query phase
        query_model_name: Literal["gemini-2.5-flash", "gemini-2.5-pro"] = (
            "gemini-2.5-pro" if query_model == "pro" else "gemini-2.5-flash"
        )
        print_verbose("Executing RAG query...", verbose > 0)
        print_verbose(
            f"Querying store '{normalized_name}' with model '{query_model_name}'", verbose > 0
        )

        if metadata_filter:
            print_verbose(f"Using metadata filter: {metadata_filter}", verbose > 0)

        # Query store with (possibly enhanced) prompt
        result = core_query(
            store_name=normalized_name,
            prompt=query_prompt,
            model=query_model_name,
            metadata_filter=metadata_filter,
            include_grounding=query_grounding_metadata,
        )

        # Add enhancement metadata to result if present
        if enhancement_metadata:
            result["enhancement"] = enhancement_metadata

        # Display query token usage if available
        usage_metadata = result.get("usage_metadata")
        if usage_metadata and verbose > 0:
            prompt_tokens = usage_metadata.get("prompt_token_count", 0)
            candidates_tokens = usage_metadata.get("candidates_token_count", 0)
            total_tokens = usage_metadata.get("total_token_count", 0)
            click.echo(
                f"[INFO] Query tokens: {prompt_tokens} prompt + {candidates_tokens} "
                f"candidates = {total_tokens} total",
                err=True,
            )

        # Calculate and add estimated cost if requested
        if show_cost:
            query_cost_estimate = estimate_cost(usage_metadata, query_model_name)

            # Aggregate costs if enhancement was used
            if enhancement_cost_estimate or query_cost_estimate:
                aggregated_cost = aggregate_costs(enhancement_cost_estimate, query_cost_estimate)
                result["estimated_cost"] = aggregated_cost

                if verbose > 0:
                    total_cost = aggregated_cost.get("total_cost_usd", 0.0)
                    if enhancement_cost_estimate:
                        click.echo(
                            f"[INFO] Query cost: ${query_cost_estimate['total_cost_usd']:.8f} USD"
                            if query_cost_estimate
                            else "[WARN] Query cost unavailable",
                            err=True,
                        )
                    click.echo(f"[INFO] Total cost: ${total_cost:.8f} USD", err=True)
            elif verbose > 0:
                click.echo("[WARN] Cost estimation unavailable: no usage metadata", err=True)

        print_verbose("Query completed successfully", verbose > 0)
        output_json(result)

    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, QueryError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
