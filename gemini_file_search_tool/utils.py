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


class DecimalJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that prevents scientific notation for small floats."""

    def encode(self, obj: Any) -> str:
        """Encode with custom float formatting."""
        if isinstance(obj, float):
            # Format floats with 8 decimal places, stripping trailing zeros
            return f"{obj:.8f}".rstrip("0").rstrip(".")
        return super().encode(obj)

    def iterencode(self, obj: Any, _one_shot: bool = False) -> Any:
        """Iterate encoding with custom float formatting."""
        for chunk in super().iterencode(obj, _one_shot):
            # Replace scientific notation in JSON output
            import re

            # Match scientific notation (e.g., 1.5e-07)
            def replace_scientific(match: Any) -> str:
                number = float(match.group(0))
                formatted = f"{number:.8f}".rstrip("0").rstrip(".")
                return formatted

            chunk = re.sub(r"\d+\.?\d*e[+-]?\d+", replace_scientific, chunk)
            yield chunk


def output_json(data: dict[str, Any] | list[dict[str, Any]]) -> None:
    """Output JSON to stdout without scientific notation for small floats.

    Args:
        data: Dictionary or list to output as JSON
    """
    click.echo(json.dumps(data, indent=2, cls=DecimalJSONEncoder))


def print_verbose(message: str, verbose: bool = False) -> None:
    """Print verbose message to stderr.

    Args:
        message: Message to print
        verbose: Whether verbose mode is enabled
    """
    if verbose:
        click.echo(f"[INFO] {message}", err=True)


def estimate_cost(usage_metadata: dict[str, int] | None, model: str) -> dict[str, Any] | None:
    """Estimate query cost based on token usage and model pricing.

    Uses published pricing from Google Gemini API documentation.
    Pricing is subject to change - verify at: https://ai.google.dev/pricing

    Current pricing (as of 2025-01):
    - gemini-2.5-flash: $0.075 input / $0.30 output per 1M tokens
    - gemini-2.5-pro: $1.25 input / $5.00 output per 1M tokens

    Args:
        usage_metadata: Dictionary with prompt_token_count and candidates_token_count
        model: Model name (e.g., 'gemini-2.5-flash', 'gemini-2.5-pro')

    Returns:
        Dictionary with estimated costs in USD, or None if usage_metadata is missing:
            - input_cost_usd: Cost of input tokens
            - output_cost_usd: Cost of output tokens
            - total_cost_usd: Total estimated cost
            - currency: 'USD'
            - model: Model name used for pricing
            - note: Warning that pricing may change

    Raises:
        ValueError: If model is not recognized
    """
    if not usage_metadata:
        return None

    # Pricing per 1M tokens (USD)
    pricing = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    }

    # Normalize model name (remove version suffixes if present)
    model_key = model
    if model not in pricing:
        # Try to match base model name
        for key in pricing:
            if model.startswith(key):
                model_key = key
                break
        else:
            raise ValueError(
                f"Unknown model '{model}'. Supported models: {', '.join(pricing.keys())}"
            )

    prompt_tokens = usage_metadata.get("prompt_token_count", 0)
    candidates_tokens = usage_metadata.get("candidates_token_count", 0)

    input_cost = (prompt_tokens / 1_000_000) * pricing[model_key]["input"]
    output_cost = (candidates_tokens / 1_000_000) * pricing[model_key]["output"]

    return {
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": input_cost + output_cost,
        "currency": "USD",
        "model": model_key,
        "note": "Estimated cost based on current pricing. Subject to change.",
    }
