"""CLI commands for file search store management.

This module provides Click commands for creating, listing, retrieving, updating,
and deleting Gemini file search stores.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import sys

import click

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
@click.option(
    "--name",
    required=True,
    help="Display name for the file search store",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def create_store(name: str, verbose: bool) -> None:
    """Create a new file search store."""
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
    """List all file search stores."""
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
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def get_store(store_name: str, verbose: bool) -> None:
    """Get details of a specific file search store."""
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
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
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
    """Update a file search store's display name."""
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
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
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
    """Delete a file search store."""
    try:
        normalized_name = normalize_store_name(store_name)
        print_verbose(f"Deleting store: {normalized_name}", verbose)
        result = core_delete_store(normalized_name, force)
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
