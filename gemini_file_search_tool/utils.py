"""Utility functions for gemini-file-search-tool.

This module provides utility functions for store name normalization,
JSON output formatting, and verbose logging.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import json
from typing import Any

import click

from gemini_file_search_tool.core.stores import list_stores


def normalize_store_name(store_name: str) -> str:
    """Normalize store name to full resource name format.

    Accepts multiple formats:
    - Full resource name: 'fileSearchStores/xxx' → returns as-is
    - Store ID with slash: 'xxx/yyy' → assumes full format, returns as-is
    - Store ID: 'xxx-yyyyyyy' → prepends 'fileSearchStores/'
    - Display name: 'obsidian' → looks up by display_name and returns full resource name

    If the store_name doesn't contain '/', it will try to resolve it as a display_name
    by listing all stores and finding a match.

    Args:
        store_name: Store name in any supported format

    Returns:
        str: Full resource name (e.g., 'fileSearchStores/xxx-yyyyyyy')

    Raises:
        ValueError: If no store matches the provided name
    """
    # If it already looks like a full resource name, return as-is
    if store_name.startswith("fileSearchStores/"):
        return store_name

    # If it contains a slash, assume it's already in some form of resource name
    if "/" in store_name:
        return store_name

    # Try to resolve by display_name first (most reliable)
    try:
        stores = list_stores()
        for store in stores:
            # Exact display_name match
            store_display_name = store.get("display_name")
            store_full_name = store.get("name", "")
            if store_display_name == store_name and isinstance(store_full_name, str):
                return store_full_name

            # If store_name matches the base part before any hyphen suffix
            # e.g., "aws-apk-docs" matches "aws-apk-docs-abc123def"
            if isinstance(store_full_name, str) and "fileSearchStores/" in store_full_name:
                store_base = store_full_name.split("fileSearchStores/")[1]  # Remove prefix
                if "-" in store_base:
                    # Check if requested name matches the base part before suffix
                    base_part = store_base.rsplit("-", 1)[0]  # Split on last hyphen
                    if base_part == store_name:
                        return store_full_name

        # If no display_name match found, then check if it looks like a full ID
        # If it contains a hyphen and looks like an ID (e.g., 'obsidian-9vy4hvvsiddm'),
        # assume it's a complete store ID and prepend the prefix
        if "-" in store_name:
            return f"fileSearchStores/{store_name}"

        # If we get here, no match found at all
        raise ValueError(
            f"No store found with display_name or base name '{store_name}'. "
            f"Use 'list-stores' to see available stores."
        )
    except Exception as e:
        # If listing fails, fall back to the old logic
        if "No store found" in str(e):
            raise
        # If it contains a hyphen, assume it's a full ID
        if "-" in store_name:
            return f"fileSearchStores/{store_name}"
        return f"fileSearchStores/{store_name}"


def output_json(data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Output JSON to stdout.

    Args:
        data: Dictionary or list to output as JSON
    """
    click.echo(json.dumps(data, indent=2))


def print_verbose(message: str, verbose: bool = False) -> None:
    """Print verbose message to stderr.

    Args:
        message: Message to print
        verbose: Whether verbose mode is enabled
    """
    if verbose:
        click.echo(f"[INFO] {message}", err=True)
