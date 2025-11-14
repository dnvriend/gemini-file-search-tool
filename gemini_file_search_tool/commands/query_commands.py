"""CLI commands for querying documents.

This module provides Click commands for querying documents in Gemini file search stores
using natural language with automatic citations.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import sys

import click

from gemini_file_search_tool.core.client import MissingConfigurationError
from gemini_file_search_tool.core.query import QueryError
from gemini_file_search_tool.core.query import query_store as core_query
from gemini_file_search_tool.utils import (
    normalize_store_name,
    output_json,
    print_verbose,
)


@click.command("query")
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
@click.option(
    "--prompt",
    required=True,
    help="Query prompt",
)
@click.option(
    "--pro",
    is_flag=True,
    help="Use gemini-2.5-pro model (default: gemini-2.5-flash)",
)
@click.option(
    "--metadata-filter",
    help="Metadata filter expression (e.g., 'author=Robert Graves')",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--query-grounding-metadata",
    is_flag=True,
    default=False,
    help="Include grounding metadata in the response JSON",
)
def query(
    store_name: str,
    prompt: str,
    pro: bool,
    metadata_filter: str | None,
    verbose: bool,
    query_grounding_metadata: bool,
) -> None:
    """Query documents in a file search store using natural language.

    Returns AI-generated answers with automatic citations from your documents.

    Examples:

    \b
        # Basic query with Flash model (default)
        gemini-file-search-tool query --store "research-papers" \\
            --prompt "What are the main findings?"

    \b
        # Use Pro model for complex queries
        gemini-file-search-tool query --store "papers" \\
            --prompt "Compare and contrast the methodologies" --pro

    \b
        # Query with metadata filter
        gemini-file-search-tool query --store "papers" \\
            --prompt "Summarize the results" \\
            --metadata-filter "author=Robert Graves"

    \b
        # Include grounding metadata in response
        gemini-file-search-tool query --store "papers" \\
            --prompt "What is the conclusion?" --query-grounding-metadata

    \b
    Output Format:
        Returns JSON with answer and optional citations:
        {
          "answer": "The main findings are...",
          "model": "gemini-2.5-flash",
          "grounding_metadata": {...}  // if --query-grounding-metadata used
        }
    """
    try:
        normalized_name = normalize_store_name(store_name)

        # Select model
        model = "gemini-2.5-pro" if pro else "gemini-2.5-flash"
        print_verbose(f"Querying store '{normalized_name}' with model '{model}'", verbose)

        if metadata_filter:
            print_verbose(f"Using metadata filter: {metadata_filter}", verbose)

        # Query store
        result = core_query(
            store_name=normalized_name,
            prompt=prompt,
            model=model,
            metadata_filter=metadata_filter,
            include_grounding=query_grounding_metadata,
        )

        print_verbose("Query completed successfully", verbose)
        output_json(result)

    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, QueryError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
