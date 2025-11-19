"""CLI commands for file search store management.

This module provides Click commands for creating, listing, retrieving, updating,
and deleting Gemini file search stores.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import sys

import click

from gemini_file_search_tool.core.cache import CacheManager
from gemini_file_search_tool.core.client import MissingConfigurationError
from gemini_file_search_tool.core.stores import (
    StoreError,
    StoreNotFoundError,
)
from gemini_file_search_tool.core.stores import (
    create_store as core_create_store,
)
from gemini_file_search_tool.core.stores import (
    delete_store as core_delete_store,
)
from gemini_file_search_tool.core.stores import (
    get_store as core_get_store,
)
from gemini_file_search_tool.core.stores import (
    list_stores as core_list_stores,
)
from gemini_file_search_tool.core.stores import (
    update_store as core_update_store,
)
from gemini_file_search_tool.utils import (
    normalize_store_name,
    output_json,
    print_verbose,
)


@click.command("create-store")
@click.argument("name", required=True)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def create_store(name: str, verbose: bool) -> None:
    """Create a new file search store.

    NAME is the display name for the file search store (positional argument).

    Examples:

    \b
        # Create a store
        gemini-file-search-tool create-store "research-papers"

    \b
        # Create with verbose output
        gemini-file-search-tool create-store "my-docs" -v
    """
    try:
        print_verbose(f"Creating file search store: {name}", verbose)
        result = core_create_store(name)
        print_verbose(f"Successfully created store: {result['name']}", verbose)
        output_json(result)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except StoreError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("list-stores")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def list_stores(verbose: bool) -> None:
    """List all file search stores.

    Example:

    \b
        gemini-file-search-tool list-stores
    """
    try:
        print_verbose("Listing all file search stores", verbose)
        stores = core_list_stores()
        print_verbose(f"Found {len(stores)} stores", verbose)
        output_json(stores)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except StoreError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("get-store")
@click.argument("store_name", required=True)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def get_store(store_name: str, verbose: bool) -> None:
    """Get details of a specific file search store.

    STORE_NAME is the store name/ID (positional argument).
    Accepts both display names and full resource names.

    Examples:

    \b
        # Get by display name
        gemini-file-search-tool get-store "research-papers"

    \b
        # Get by resource name
        gemini-file-search-tool get-store "fileSearchStores/abc123"
    """
    try:
        normalized_name = normalize_store_name(store_name)
        print_verbose(f"Getting store: {normalized_name}", verbose)
        store_info = core_get_store(normalized_name)

        if "document_count" in store_info:
            print_verbose(f"Found {store_info['document_count']} documents in store", verbose)

        output_json(store_info)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, StoreNotFoundError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except StoreError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("update-store")
@click.argument("store_name", required=True)
@click.option(
    "--display-name",
    required=True,
    help="New display name for the store",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def update_store(store_name: str, display_name: str, verbose: bool) -> None:
    """Update a file search store's display name.

    STORE_NAME is the store name/ID (positional argument).

    Example:

    \b
        # Rename a store
        gemini-file-search-tool update-store "old-name" \\
            --display-name "new-name"
    """
    try:
        normalized_name = normalize_store_name(store_name)
        print_verbose(f"Updating store: {normalized_name}", verbose)
        result = core_update_store(normalized_name, display_name)
        print_verbose(f"Successfully updated store: {result['name']}", verbose)
        output_json(result)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, StoreNotFoundError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except StoreError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("delete-store")
@click.argument("store_name", required=True)
@click.option(
    "--force",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def delete_store(store_name: str, force: bool, verbose: bool) -> None:
    """Delete a file search store.

    STORE_NAME is the store name/ID (positional argument).

    Examples:

    \b
        # Delete with confirmation prompt
        gemini-file-search-tool delete-store "old-store"

    \b
        # Force deletion without prompt
        gemini-file-search-tool delete-store "old-store" --force
    """
    try:
        normalized_name = normalize_store_name(store_name)

        # Check for cache and show stats
        cache_manager = CacheManager()
        cache_stats = cache_manager.get_cache_stats(normalized_name)

        if cache_stats["total_files"] > 0:
            print_verbose(f"Cache found for store '{store_name}':", verbose)
            print_verbose(f"  Total files: {cache_stats['total_files']}", verbose)
            print_verbose(f"  Completed: {cache_stats['completed']}", verbose)
            print_verbose(f"  Pending operations: {cache_stats['pending_operations']}", verbose)
            print_verbose(f"  Failed operations: {cache_stats['failed_operations']}", verbose)

        print_verbose(f"Deleting store: {normalized_name}", verbose)
        result = core_delete_store(normalized_name, force)

        # Remove cache file after successful store deletion
        if cache_stats["total_files"] > 0:
            print_verbose("Removing cache file...", verbose)
            cache_manager.clear_store_cache(normalized_name)
            print_verbose("Cache removed successfully", verbose)

        print_verbose("Store deleted successfully", verbose)
        output_json(result)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, StoreNotFoundError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except StoreError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
