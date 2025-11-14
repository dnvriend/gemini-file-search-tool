"""CLI commands for document management.

This module provides Click commands for listing and uploading documents
to Gemini file search stores.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import os
import sys
from pathlib import Path
from typing import Any

import click
import requests
from tqdm import tqdm

from gemini_file_search_tool.core.client import MissingConfigurationError
from gemini_file_search_tool.core.documents import (
    DocumentError,
    delete_document,
    upload_files_concurrent,
)
from gemini_file_search_tool.core.documents import (
    list_documents as core_list_documents,
)
from gemini_file_search_tool.utils import (
    normalize_store_name,
    output_json,
    print_verbose,
)


@click.command("list-documents")
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
def list_documents(store_name: str, verbose: bool) -> None:
    """List all documents in a file search store."""
    try:
        normalized_name = normalize_store_name(store_name)
        print_verbose(f"Listing documents in store: {normalized_name}", verbose)
        documents = core_list_documents(normalized_name)
        print_verbose(f"Found {len(documents)} documents", verbose)
        output_json(documents)
    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, DocumentError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


def _expand_file_patterns(patterns: list[str], verbose: bool) -> list[Path]:
    """Expand file patterns (including globs) to a list of file paths.

    Args:
        patterns: List of file patterns (can include globs)
        verbose: Whether to print verbose messages

    Returns:
        List of resolved file paths
    """
    all_files: list[Path] = []

    for pattern in patterns:
        # Step 1: Expand environment variables
        expanded = os.path.expandvars(pattern)
        print_verbose(f"After env expansion: {expanded}", verbose)

        # Step 2: Expand ~ (tilde)
        expanded = str(Path(expanded).expanduser())
        print_verbose(f"After ~ expansion: {expanded}", verbose)

        # Step 3: Check if pattern contains wildcards
        has_wildcards = any(c in expanded for c in ["*", "?", "["])

        if not has_wildcards:
            # No wildcards - treat as direct file path
            file_path = Path(expanded).resolve()
            if file_path.exists() and file_path.is_file():
                all_files.append(file_path)
        else:
            # Has wildcards - split base dir and pattern
            first_wildcard_pos = min(
                (expanded.find(c) for c in ["*", "?", "["] if expanded.find(c) != -1),
                default=len(expanded),
            )

            # Find last / before first wildcard
            base_end = expanded.rfind("/", 0, first_wildcard_pos)

            if base_end == -1:
                # No / before wildcard, use current directory
                base_dir = Path.cwd()
                glob_pattern = expanded
            else:
                # Split at last / before wildcard
                base_dir_str = expanded[:base_end]
                glob_pattern = expanded[base_end + 1 :]  # Skip the /
                base_dir = Path(base_dir_str).resolve()

            print_verbose(f"Base dir: {base_dir}", verbose)
            print_verbose(f"Glob pattern: {glob_pattern}", verbose)

            # Expand glob pattern
            try:
                found_files = list(base_dir.glob(glob_pattern))
                print_verbose(f"Glob found {len(found_files)} items", verbose)

                # Filter to only include files
                found_files = [f for f in found_files if f.is_file()]
                print_verbose(f"After filtering: {len(found_files)} files", verbose)

                all_files.extend(found_files)
            except Exception as e:
                print_verbose(f"Glob failed: {str(e)}", verbose)

    return all_files


def _fetch_existing_documents(store_name: str, verbose: bool) -> dict[str, dict[str, Any]]:
    """Fetch existing documents from a store for duplicate detection.

    Args:
        store_name: Normalized store name
        verbose: Whether to print verbose messages

    Returns:
        Dict mapping display_name to document metadata
    """
    existing_documents: dict[str, dict[str, Any]] = {}

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return existing_documents

        base_url = "https://generativelanguage.googleapis.com/v1alpha"
        url = f"{base_url}/{store_name}/documents"

        page_token = None
        while True:
            params: dict[str, str] = {"key": api_key}
            if page_token:
                params["pageToken"] = page_token

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if "documents" in data:
                for doc in data["documents"]:
                    display_name = doc.get("displayName", "")
                    if display_name:
                        existing_documents[display_name] = {
                            "name": doc.get("name", ""),
                            "sizeBytes": int(doc.get("sizeBytes", "0")),
                            "updateTime": doc.get("updateTime", ""),
                        }

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        print_verbose(f"Found {len(existing_documents)} existing documents in store", verbose)
    except Exception as e:
        print_verbose(f"Warning: Could not fetch existing documents: {str(e)}", verbose)

    return existing_documents


@click.command("upload")
@click.argument("files", nargs=-1, required=True)
@click.option(
    "--store-name",
    "--store",
    "store_name",
    required=True,
    help="Store name/ID (accepts both full resource names or just IDs)",
)
@click.option(
    "--title",
    default=None,
    help="Custom metadata title (optional)",
)
@click.option(
    "--url",
    default=None,
    help="Custom metadata URL (optional)",
)
@click.option(
    "--file-name",
    default=None,
    help="Custom metadata file_name (optional)",
)
@click.option(
    "--max-tokens",
    type=int,
    default=200,
    help="Max tokens per chunk (default: 200)",
)
@click.option(
    "--max-overlap",
    type=int,
    default=20,
    help="Max overlap tokens (default: 20)",
)
@click.option(
    "--num-workers",
    type=int,
    default=None,
    help="Number of concurrent workers (default: CPU core count)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (shows upload progress)",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip file validation (size and base64 image checks)",
)
def upload(
    files: tuple[str, ...],
    store_name: str,
    title: str | None,
    url: str | None,
    file_name: str | None,
    max_tokens: int,
    max_overlap: int,
    num_workers: int | None,
    verbose: bool,
    skip_validation: bool,
) -> None:
    """Upload file(s) to a file search store. Supports glob patterns."""
    try:
        # Expand file patterns
        files_to_upload = _expand_file_patterns(list(files), verbose)

        if not files_to_upload:
            click.echo(
                f"Error: No files found matching patterns: {', '.join(files)}",
                err=True,
            )
            sys.exit(1)

        # Normalize store name
        normalized_name = normalize_store_name(store_name)

        # Fetch existing documents for duplicate detection
        existing_documents = _fetch_existing_documents(normalized_name, verbose)

        # Categorize files: new, unchanged, or changed
        files_to_actually_upload: list[Path] = []
        skipped_files: list[Path] = []
        files_to_update: list[tuple[Path, str]] = []

        for file_path in files_to_upload:
            display_name = str(file_path)

            if display_name in existing_documents:
                # File exists, check if changed
                existing_doc = existing_documents[display_name]
                file_size = file_path.stat().st_size
                api_size = existing_doc["sizeBytes"]

                if api_size == file_size:
                    # Same size, assume unchanged
                    skipped_files.append(file_path)
                    print_verbose(f"Skipping (unchanged): {display_name}", verbose)
                else:
                    # Size changed, needs update
                    files_to_update.append((file_path, existing_doc["name"]))
                    print_verbose(
                        f"Update needed (size changed: {api_size} -> {file_size}): {display_name}",
                        verbose,
                    )
            else:
                # New file
                files_to_actually_upload.append(file_path)

        print_verbose(
            f"Found {len(files_to_upload)} file(s): "
            f"{len(files_to_actually_upload)} new, "
            f"{len(files_to_update)} to update, "
            f"{len(skipped_files)} unchanged",
            verbose,
        )

        # Delete old versions of files that need updating
        updated_files = []
        if files_to_update:
            print_verbose(
                f"Deleting {len(files_to_update)} old document(s) before re-uploading...",
                verbose,
            )

            for file_path, doc_name in files_to_update:
                try:
                    print_verbose(f"Deleting: {doc_name}", verbose)
                    delete_document(doc_name, force=True)
                    files_to_actually_upload.append(file_path)
                    updated_files.append(file_path)
                    print_verbose(f"Successfully deleted old version: {file_path}", verbose)
                except Exception as e:
                    click.echo(f"Warning: Failed to delete {doc_name}: {str(e)}", err=True)

        # Prepare results
        results: list[dict[str, Any]] = []

        # Add skipped files to results
        for skipped_file in skipped_files:
            results.append(
                {
                    "file": str(skipped_file),
                    "status": "skipped",
                    "reason": "Already exists in store",
                }
            )

        # Set default num_workers
        if num_workers is None:
            num_workers = os.cpu_count() or 1

        print_verbose(f"Using {num_workers} worker(s)", verbose)

        # Upload files if any
        if files_to_actually_upload:
            # Counters for progress tracking
            success_count = 0
            failure_count = 0
            updated_count = 0
            skipped_count = len(skipped_files)

            # Progress bar
            with tqdm(
                total=len(files_to_actually_upload),
                desc="Uploading files",
                unit="file",
                file=sys.stderr,
            ) as pbar:

                def progress_callback(result: dict[str, Any]) -> None:
                    nonlocal success_count, failure_count, updated_count
                    file_path = Path(result["file"])

                    if file_path in updated_files and result["status"] == "completed":
                        result["status"] = "updated"
                        updated_count += 1
                    elif result["status"] == "completed":
                        success_count += 1
                    else:
                        failure_count += 1

                    pbar.set_postfix(
                        {
                            "new": success_count,
                            "updated": updated_count,
                            "failed": failure_count,
                            "skipped": skipped_count,
                            "current": file_path.name,
                        }
                    )
                    pbar.update(1)

                upload_results = upload_files_concurrent(
                    files=files_to_actually_upload,
                    store_name=normalized_name,
                    title=title,
                    url=url,
                    file_name=file_name,
                    max_tokens=max_tokens,
                    max_overlap=max_overlap,
                    skip_validation=skip_validation,
                    num_workers=num_workers,
                    progress_callback=progress_callback,
                )

                results.extend(upload_results)

            # Exit with error if all uploads failed
            if failure_count == len(files_to_actually_upload):
                click.echo(
                    f"Error: All {len(files_to_actually_upload)} attempted upload(s) failed",
                    err=True,
                )
                output_json(results)
                sys.exit(1)
        else:
            print_verbose("No new files to upload (all files already exist)", verbose)

        # Output results
        output_json(results)

    except MissingConfigurationError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except (ValueError, DocumentError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
