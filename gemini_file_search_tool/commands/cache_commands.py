"""CLI commands for cache management.

This module provides Click commands for managing the local cache,
including syncing pending operations, flushing cache, and generating reports.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click
from google import genai
from tqdm import tqdm

from gemini_file_search_tool.core.cache import CacheManager
from gemini_file_search_tool.core.client import MissingConfigurationError, get_client
from gemini_file_search_tool.logging_config import get_logger, setup_logging
from gemini_file_search_tool.utils import normalize_store_name, output_json, print_verbose


def _sync_single_operation(
    file_path: str, state: dict[str, Any], client: Any, logger: Any
) -> dict[str, Any]:
    """Sync a single pending operation.

    Args:
        file_path: Absolute path to the file
        state: Cached state dict for this file
        client: Gemini client instance
        logger: Logger instance

    Returns:
        Dictionary with sync result:
            - file: File path
            - status: 'synced', 'failed', 'pending', or 'error'
            - cache_update: Dict with fields to update in cache (or None)
            - result: Result dict for JSON output
    """
    operation_obj = state.get("operation", {})
    operation_name = operation_obj.get("name")

    if not operation_name:
        logger.warning(f"Skipping {Path(file_path).name}: Missing operation name")
        return {
            "file": file_path,
            "status": "error",
            "cache_update": None,
            "result": {
                "file": file_path,
                "status": "error",
                "error": {"message": "Missing operation name"},
            },
        }

    try:
        # Fetch operation status
        logger.debug(f"Checking operation: {operation_name}")
        # Create operation object with name for SDK's operations.get()
        # Type stub doesn't reflect runtime behavior, name arg works at runtime
        op_ref = genai.types.UploadToFileSearchStoreOperation(name=operation_name)  # type: ignore[call-arg]
        operation = client.operations.get(op_ref)

        # Store updated operation object
        updated_operation = {
            "name": operation.name if hasattr(operation, "name") else operation_name,
            "done": operation.done if hasattr(operation, "done") else False,
            "metadata": (
                dict(operation.metadata)
                if hasattr(operation, "metadata") and operation.metadata
                else {}
            ),
        }

        # Check if error
        if hasattr(operation, "error") and operation.error:
            error_code = operation.error.code if hasattr(operation.error, "code") else None
            error_message = (
                operation.error.message
                if hasattr(operation.error, "message")
                else str(operation.error)
            )
            updated_operation["error"] = {
                "code": error_code,
                "message": error_message,
            }
            logger.warning(f"Operation failed: {Path(file_path).name}")
            return {
                "file": file_path,
                "status": "failed",
                "cache_update": {
                    "operation": updated_operation,
                    "content_hash": state.get("hash"),
                    "mtime": state.get("mtime"),
                },
                "result": {
                    "file": file_path,
                    "status": "failed",
                    "operation": operation_name,
                    "error": updated_operation["error"],
                },
            }
        # Check if done
        elif hasattr(operation, "done") and operation.done:
            # Extract document name
            doc_name = None
            if hasattr(operation, "response") and operation.response:
                if hasattr(operation.response, "document_name"):
                    doc_name = operation.response.document_name

            if doc_name:
                # Success - will update cache with remote_id
                logger.info(f"Synced: {Path(file_path).name}")
                return {
                    "file": file_path,
                    "status": "synced",
                    "cache_update": {
                        "remote_id": doc_name,
                        "content_hash": state.get("hash"),
                        "mtime": state.get("mtime"),
                    },
                    "result": {
                        "file": file_path,
                        "status": "synced",
                        "remote_id": doc_name,
                    },
                }
            else:
                # Done but no document name? Store as failed
                error_msg = "Operation done but no document_name"
                updated_operation["error"] = {"message": error_msg}
                logger.warning(f"Operation done but no document: {Path(file_path).name}")
                return {
                    "file": file_path,
                    "status": "failed",
                    "cache_update": {
                        "operation": updated_operation,
                        "content_hash": state.get("hash"),
                        "mtime": state.get("mtime"),
                    },
                    "result": {
                        "file": file_path,
                        "status": "failed",
                        "operation": operation_name,
                        "error": updated_operation["error"],
                    },
                }
        else:
            # Still pending - update operation object in cache
            logger.debug(f"Still pending: {Path(file_path).name}")
            return {
                "file": file_path,
                "status": "pending",
                "cache_update": {
                    "operation": updated_operation,
                    "content_hash": state.get("hash"),
                    "mtime": state.get("mtime"),
                },
                "result": {
                    "file": file_path,
                    "status": "pending",
                    "operation": operation_name,
                },
            }

    except Exception as e:
        logger.error(f"Failed to sync {Path(file_path).name}: {str(e)}")
        return {
            "file": file_path,
            "status": "error",
            "cache_update": None,
            "result": {
                "file": file_path,
                "status": "error",
                "operation": operation_name,
                "error": {"message": str(e)},
            },
        }


@click.command("sync-cache")
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID to sync cache for",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose output (use -v for INFO, -vv for DEBUG)",
)
@click.option(
    "--text",
    is_flag=True,
    help="Output human-readable text format instead of JSON",
)
@click.option(
    "--num-workers",
    type=int,
    default=None,
    help="Number of concurrent workers (default: 4)",
)
def sync_cache(store_name: str, verbose: int, text: bool, num_workers: int | None) -> None:
    """Sync pending operations from cache and update with final status.

    Loops through all pending operations in the cache, checks their status,
    and updates the cache with remote_id if the operation completed successfully.

    Examples:

    \b
        # Sync all pending operations for a store
        gemini-file-search-tool sync-cache --store "my-store"

    \b
        # With verbose output
        gemini-file-search-tool sync-cache --store "my-store" -v

    \b
        # Human-readable text output
        gemini-file-search-tool sync-cache --store "my-store" --text
    """
    # Setup logging
    setup_logging(verbose)
    logger = get_logger(__name__)

    try:
        # Normalize store name
        normalized_name = normalize_store_name(store_name)

        # Initialize cache and client
        cache_manager = CacheManager()
        client = get_client()

        # Get all pending operations
        pending_ops = cache_manager.get_pending_operations(normalized_name)

        if not pending_ops:
            if text:
                click.echo("No pending operations to sync.")
            else:
                output_json(
                    {
                        "status": "success",
                        "message": "No pending operations",
                        "synced": 0,
                        "failed": 0,
                        "still_pending": 0,
                    }
                )
            return

        print_verbose(f"Found {len(pending_ops)} pending operation(s) to sync", verbose)

        # Set default num_workers
        if num_workers is None:
            num_workers = 4

        print_verbose(f"Using {num_workers} worker(s)", verbose)

        synced_count = 0
        failed_count = 0
        still_pending_count = 0
        results: list[dict[str, Any]] = []
        cache_updates: list[tuple[str, dict[str, Any]]] = []  # (file_path, update_dict)

        # Process operations concurrently with progress bar
        with tqdm(
            total=len(pending_ops),
            desc="Syncing operations",
            unit="op",
            file=sys.stderr,
            disable=not verbose,
        ) as pbar:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all operations
                future_to_file = {
                    executor.submit(
                        _sync_single_operation, file_path, state, client, logger
                    ): file_path
                    for file_path, state in pending_ops.items()
                }

                # Process completed operations as they finish
                for future in as_completed(future_to_file):
                    try:
                        sync_result = future.result()
                        status = sync_result["status"]

                        # Update counters
                        if status == "synced":
                            synced_count += 1
                        elif status == "failed" or status == "error":
                            failed_count += 1
                        elif status == "pending":
                            still_pending_count += 1

                        # Collect cache update for batch write
                        if sync_result["cache_update"] is not None:
                            cache_updates.append((sync_result["file"], sync_result["cache_update"]))

                        # Collect result for output
                        results.append(sync_result["result"])

                    except Exception as e:
                        file_path = future_to_file[future]
                        logger.error(f"Unexpected error for {Path(file_path).name}: {str(e)}")
                        failed_count += 1
                        results.append(
                            {
                                "file": file_path,
                                "status": "error",
                                "error": {"message": f"Unexpected error: {str(e)}"},
                            }
                        )

                    # Update progress bar
                    pbar.set_postfix(
                        {
                            "synced": synced_count,
                            "failed": failed_count,
                            "pending": still_pending_count,
                        }
                    )
                    pbar.update(1)

        # Batch write all cache updates at once (after all operations complete)
        logger.info(f"Writing {len(cache_updates)} cache update(s)")
        for file_path, update_dict in cache_updates:
            cache_manager.update_file_state(normalized_name, file_path, **update_dict)
        logger.info("Cache write complete")

        # Output results
        if text:
            click.echo("\nSync Summary:")
            click.echo(f"  Total operations: {len(pending_ops)}")
            click.echo(f"  Synced: {synced_count}")
            click.echo(f"  Failed: {failed_count}")
            click.echo(f"  Still pending: {still_pending_count}")
        else:
            output_json(
                {
                    "status": "success",
                    "total": len(pending_ops),
                    "synced": synced_count,
                    "failed": failed_count,
                    "still_pending": still_pending_count,
                    "operations": results,
                }
            )

    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("flush-cache")
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID to flush cache for",
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose output (use -v for INFO, -vv for DEBUG)",
)
def flush_cache(store_name: str, force: bool, verbose: int) -> None:
    """Delete cache file for a specific store.

    Removes all cached state for the specified store, including uploaded files
    and pending operations. Use with caution.

    Examples:

    \b
        # Flush cache for a store (requires confirmation)
        gemini-file-search-tool flush-cache --store "my-store"

    \b
        # Force flush without confirmation
        gemini-file-search-tool flush-cache --store "my-store" --force
    """
    # Setup logging
    setup_logging(verbose)
    logger = get_logger(__name__)

    try:
        # Normalize store name
        normalized_name = normalize_store_name(store_name)

        # Initialize cache
        cache_manager = CacheManager()

        # Get cache stats before deletion
        stats = cache_manager.get_cache_stats(normalized_name)

        if stats["total_files"] == 0:
            click.echo(f"No cache found for store '{store_name}'")
            return

        # Show stats and prompt for confirmation
        if not force:
            click.echo(f"Cache statistics for '{store_name}':")
            click.echo(f"  Total files: {stats['total_files']}")
            click.echo(f"  Completed: {stats['completed']}")
            click.echo(f"  Pending operations: {stats['pending_operations']}")
            click.echo(f"  Failed operations: {stats['failed_operations']}")
            click.echo()

            if not click.confirm("Are you sure you want to delete this cache?"):
                click.echo("Aborted.")
                return

        # Delete cache
        cache_manager.clear_store_cache(normalized_name)
        logger.info(f"Deleted cache for store '{store_name}'")
        click.echo(f"Successfully flushed cache for '{store_name}'")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@click.command("cache-report")
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID to generate report for",
)
@click.option(
    "--pending-only",
    is_flag=True,
    help="Show only files with pending operations",
)
@click.option(
    "--errors-only",
    is_flag=True,
    help="Show only files with errors",
)
@click.option(
    "--completed-only",
    is_flag=True,
    help="Show only completed uploads",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Show all files (overrides other filters)",
)
@click.option(
    "--text",
    is_flag=True,
    help="Output human-readable text format instead of JSON",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose output (use -v for INFO, -vv for DEBUG)",
)
def cache_report(
    store_name: str,
    pending_only: bool,
    errors_only: bool,
    completed_only: bool,
    show_all: bool,
    text: bool,
    verbose: int,
) -> None:
    """Generate a report on cache status for a store.

    By default, shows summary statistics and files with pending operations.
    Use filters to customize the report.

    Examples:

    \b
        # Default report (summary + pending operations)
        gemini-file-search-tool cache-report --store "my-store"

    \b
        # Show only files with errors
        gemini-file-search-tool cache-report --store "my-store" --errors-only

    \b
        # Show all cached files
        gemini-file-search-tool cache-report --store "my-store" --all

    \b
        # Human-readable text output
        gemini-file-search-tool cache-report --store "my-store" --text
    """
    # Setup logging
    setup_logging(verbose)

    try:
        # Normalize store name
        normalized_name = normalize_store_name(store_name)

        # Initialize cache
        cache_manager = CacheManager()

        # Get cache stats
        stats = cache_manager.get_cache_stats(normalized_name)

        if stats["total_files"] == 0:
            if text:
                click.echo(f"No cache found for store '{store_name}'")
            else:
                output_json(
                    {
                        "store": store_name,
                        "stats": stats,
                        "files": [],
                    }
                )
            return

        # Load cache data
        cache_data = cache_manager._load_cache(normalized_name)

        # Filter files based on options
        filtered_files: list[dict[str, Any]] = []

        for file_path, state in cache_data.items():
            file_info: dict[str, Any] = {
                "file": file_path,
                "hash": state.get("hash"),
                "mtime": state.get("mtime"),
                "last_uploaded": state.get("last_uploaded"),
            }

            # Determine file status
            if "remote_id" in state and state["remote_id"]:
                file_info["status"] = "completed"
                file_info["remote_id"] = state["remote_id"]
                if not show_all and not completed_only:
                    continue  # Skip completed files unless explicitly requested
            elif "operation" in state and state["operation"]:
                operation = state["operation"]
                is_done = operation.get("done", False)
                has_error = "error" in operation

                if has_error:
                    file_info["status"] = "failed"
                    file_info["operation"] = operation.get("name")
                    file_info["error"] = operation.get("error")
                    if not show_all and not errors_only:
                        continue  # Skip errors unless explicitly requested
                elif is_done:
                    file_info["status"] = "failed"
                    file_info["operation"] = operation.get("name")
                    file_info["error"] = {"message": "Operation done but no remote_id"}
                    if not show_all and not errors_only:
                        continue
                else:
                    file_info["status"] = "pending"
                    file_info["operation"] = operation.get("name")
                    # Pending operations are shown by default
            else:
                file_info["status"] = "unknown"
                if not show_all:
                    continue

            # Apply specific filters
            if pending_only and file_info["status"] != "pending":
                continue
            if errors_only and file_info["status"] != "failed":
                continue
            if completed_only and file_info["status"] != "completed":
                continue

            filtered_files.append(file_info)

        # Output results
        if text:
            click.echo(f"\nCache Report for '{store_name}'")
            click.echo("=" * 60)
            click.echo("\nSummary Statistics:")
            click.echo(f"  Total files: {stats['total_files']}")
            click.echo(f"  Completed: {stats['completed']}")
            click.echo(f"  Pending operations: {stats['pending_operations']}")
            click.echo(f"  Failed operations: {stats['failed_operations']}")

            if filtered_files:
                click.echo(f"\nFiles ({len(filtered_files)}):")
                for file_info in filtered_files:
                    click.echo(f"\n  File: {Path(file_info['file']).name}")
                    click.echo(f"    Status: {file_info['status']}")
                    if "remote_id" in file_info:
                        click.echo(f"    Remote ID: {file_info['remote_id']}")
                    if "operation" in file_info:
                        click.echo(f"    Operation: {file_info['operation']}")
                    if "error" in file_info:
                        click.echo(f"    Error: {file_info['error']}")
        else:
            output_json(
                {
                    "store": store_name,
                    "stats": stats,
                    "files": filtered_files,
                }
            )

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
