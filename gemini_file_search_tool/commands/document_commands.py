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

from gemini_file_search_tool.core.cache import CacheManager
from gemini_file_search_tool.core.client import MissingConfigurationError
from gemini_file_search_tool.core.documents import (
    DocumentError,
    delete_document,
    upload_files_concurrent,
)
from gemini_file_search_tool.core.documents import (
    list_documents as core_list_documents,
)
from gemini_file_search_tool.logging_config import get_logger, setup_logging
from gemini_file_search_tool.utils import (
    normalize_store_name,
    output_json,
    print_verbose,
)

# System files and directories to skip during upload
# These files are typically not useful for RAG/search and may cause issues
SKIP_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dylib",
    ".DS_Store",
    ".git",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    ".env/",
    "node_modules",
    ".egg-info",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
]


def _load_gitignore_patterns(start_path: Path) -> list[str]:
    """Load patterns from .gitignore file if it exists.

    Searches for .gitignore starting from start_path up to root.

    Args:
        start_path: Path to start searching for .gitignore

    Returns:
        List of gitignore patterns (empty if no .gitignore found)
    """
    patterns: list[str] = []

    # Search from current path up to root
    current = start_path.resolve()
    while current != current.parent:
        gitignore = current / ".gitignore"
        if gitignore.exists():
            try:
                with open(gitignore) as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except Exception:
                pass  # Ignore read errors
            break  # Only use first .gitignore found
        current = current.parent

    return patterns


def _matches_gitignore_pattern(file_path: Path, pattern: str, gitignore_dir: Path) -> bool:
    """Check if file matches a gitignore pattern.

    Args:
        file_path: Path to check
        pattern: Gitignore pattern
        gitignore_dir: Directory containing .gitignore

    Returns:
        True if file matches pattern, False otherwise
    """
    import fnmatch

    try:
        # Get relative path from gitignore directory
        rel_path = file_path.relative_to(gitignore_dir)
        rel_path_str = str(rel_path)

        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            # Check if any parent directory matches
            for parent in rel_path.parents:
                if parent.name and fnmatch.fnmatch(str(parent.name), pattern):
                    return True
            return False

        # Handle patterns with / (path-specific)
        if "/" in pattern:
            return fnmatch.fnmatch(rel_path_str, pattern)

        # Handle simple patterns (match anywhere in path)
        # Check filename
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

        # Check if pattern matches any part of the path
        for part in rel_path.parts:
            if fnmatch.fnmatch(part, pattern):
                return True

        return False
    except ValueError:
        # File is not relative to gitignore_dir
        return False


def _should_skip_file(
    file_path: Path, gitignore_patterns: list[str] = [], gitignore_dir: Path | None = None
) -> bool:
    """Check if a file should be skipped based on skip patterns and gitignore.

    Args:
        file_path: Path to check
        gitignore_patterns: List of gitignore patterns to check
        gitignore_dir: Directory containing .gitignore (for relative path matching)

    Returns:
        True if file should be skipped, False otherwise
    """
    file_str = str(file_path)
    file_name = file_path.name

    # Check built-in skip patterns
    for pattern in SKIP_PATTERNS:
        # Check if pattern is in path (for directories like __pycache__)
        if pattern in file_str:
            return True
        # Check if file ends with pattern (for extensions like .pyc)
        if file_name.endswith(pattern):
            return True

    # Check gitignore patterns
    if gitignore_patterns and gitignore_dir:
        for pattern in gitignore_patterns:
            if _matches_gitignore_pattern(file_path, pattern, gitignore_dir):
                return True

    return False


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
    count=True,
    help="Enable verbose output (use -v for INFO, -vv for DEBUG, -vvv for TRACE)",
)
def list_documents(store_name: str, verbose: int) -> None:
    """List all documents in a file search store.

    Example:

    \b
        gemini-file-search-tool list-documents --store "research-papers"
    """
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


def _expand_file_patterns(
    patterns: list[str], verbose: bool | int, ignore_gitignore: bool = False
) -> list[Path]:
    """Expand file patterns (including globs) to a list of file paths.

    Args:
        patterns: List of file patterns (can include globs)
        verbose: Whether to print verbose messages
        ignore_gitignore: If True, skip gitignore pattern matching

    Returns:
        List of resolved file paths
    """
    all_files: list[Path] = []

    # Load gitignore patterns if not ignoring
    gitignore_patterns: list[str] = []
    gitignore_dir: Path | None = None
    if not ignore_gitignore:
        gitignore_dir = Path.cwd()
        gitignore_patterns = _load_gitignore_patterns(gitignore_dir)
        if gitignore_patterns:
            print_verbose(f"Loaded {len(gitignore_patterns)} patterns from .gitignore", verbose)

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
            if (
                file_path.exists()
                and file_path.is_file()
                and not _should_skip_file(file_path, gitignore_patterns, gitignore_dir)
            ):
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

                # Filter to only include files (not directories)
                found_files = [f for f in found_files if f.is_file()]
                print_verbose(f"After filtering: {len(found_files)} files", verbose)

                # Filter out system files and gitignore patterns
                found_files = [
                    f
                    for f in found_files
                    if not _should_skip_file(f, gitignore_patterns, gitignore_dir)
                ]
                print_verbose(
                    f"After skipping system files and gitignore: {len(found_files)} files",
                    verbose,
                )

                all_files.extend(found_files)
            except Exception as e:
                print_verbose(f"Glob failed: {str(e)}", verbose)

    return all_files


def _fetch_existing_documents(store_name: str, verbose: bool | int) -> dict[str, dict[str, Any]]:
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
    count=True,
    help="Enable verbose output (use -v for INFO, -vv for DEBUG, -vvv for TRACE)",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip file validation (size and base64 image checks)",
)
@click.option(
    "--ignore-gitignore",
    is_flag=True,
    help="Ignore .gitignore patterns (upload all files matching glob)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show which files would be uploaded without actually uploading",
)
@click.option(
    "--rebuild-cache",
    is_flag=True,
    help="Force re-upload of all files and rebuild the local cache",
)
@click.option(
    "--no-wait",
    is_flag=True,
    help="Don't wait for operations to complete (returns immediately with operation IDs)",
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
    verbose: int,
    skip_validation: bool,
    ignore_gitignore: bool,
    dry_run: bool,
    rebuild_cache: bool,
    no_wait: bool,
) -> None:
    """Upload file(s) to a file search store. Supports glob patterns.

    FILES can be file paths or glob patterns (*.pdf, docs/**/*.md).
    Automatically detects duplicates and skips unchanged files.
    Respects .gitignore patterns by default (use --ignore-gitignore to disable).
    Use -v/-vv/-vvv for progressive logging detail.

    Examples:

    \b
        # Upload single file
        gemini-file-search-tool upload document.pdf --store "research-papers"

    \b
        # Upload multiple files
        gemini-file-search-tool upload doc1.pdf doc2.pdf --store "papers"

    \b
        # Upload with glob pattern - all PDFs in current directory
        gemini-file-search-tool upload "*.pdf" --store "papers"

    \b
        # Upload with recursive glob - all markdown files
        gemini-file-search-tool upload "docs/**/*.md" --store "documentation"

    \b
        # Upload entire codebase for Code-RAG
        gemini-file-search-tool upload "src/**/*.py" --store "my-codebase" -v

    \b
        # With verbose logging (see progress and errors)
        gemini-file-search-tool upload "*.pdf" --store "papers" -v

    \b
        # With debug logging (see API operations)
        gemini-file-search-tool upload "*.pdf" --store "papers" -vv

    \b
        # With custom metadata
        gemini-file-search-tool upload paper.pdf --store "papers" \\
            --title "Research Paper 2024" --url "https://example.com/paper"

    \b
        # With custom chunking and workers
        gemini-file-search-tool upload "*.pdf" --store "papers" \\
            --max-tokens 500 --max-overlap 50 --num-workers 8

    \b
        # Skip validation for faster uploads
        gemini-file-search-tool upload "*.txt" --store "notes" --skip-validation

    \b
        # Ignore .gitignore patterns (upload all files)
        gemini-file-search-tool upload "**/*" --store "everything" --ignore-gitignore

    \b
        # Dry-run to see which files would be uploaded
        gemini-file-search-tool upload "**/*.py" --store "code" --dry-run -v

    \b
    Output Format:
        Returns JSON array with status for each file:
        [
          {"file": "doc.pdf", "status": "completed", "document_name": "..."},
          {"file": "dup.pdf", "status": "skipped", "reason": "Already exists"},
          {"file": "old.pdf", "status": "updated", "document_name": "..."}
        ]
    """
    # Setup logging based on verbosity level
    setup_logging(verbose)
    logger = get_logger(__name__)

    try:
        logger.info("Starting upload operation")

        # Expand file patterns
        files_to_upload = _expand_file_patterns(list(files), verbose, ignore_gitignore)

        if not files_to_upload:
            click.echo(
                f"Error: No files found matching patterns: {', '.join(files)}",
                err=True,
            )
            sys.exit(1)

        # Dry-run mode: just show files and exit
        if dry_run:
            logger.info(f"DRY-RUN: Would upload {len(files_to_upload)} file(s)")
            dry_run_results = [
                {
                    "file": str(f),
                    "size_bytes": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                }
                for f in files_to_upload
            ]
            output_json(dry_run_results)
            return

        # Normalize store name
        normalized_name = normalize_store_name(store_name)

        # Initialize cache manager
        cache_manager = CacheManager()

        if rebuild_cache:
            print_verbose("Rebuild cache requested: Ignoring local cache", verbose)
            # We don't clear the cache immediately, we just ignore it during the check
            # and overwrite entries as we upload.

        # Categorize files: new, unchanged, or changed
        files_to_actually_upload: list[Path] = []
        skipped_files: list[Path] = []
        files_to_update: list[tuple[Path, str]] = []  # (path, remote_id)

        # Pre-calculate hashes for all files to check against cache
        print_verbose("Checking local cache...", verbose)

        for file_path in files_to_upload:
            abs_path = str(file_path.resolve())

            # If rebuilding cache, treat everything as new/changed
            if rebuild_cache:
                files_to_actually_upload.append(file_path)
                continue

            # Check cache first
            cached_state = cache_manager.get_file_state(normalized_name, abs_path)
            current_mtime = file_path.stat().st_mtime

            # Optimization: Check mtime before calculating expensive hash
            needs_hash = True
            if cached_state:
                cached_mtime = cached_state.get("mtime")
                if cached_mtime is not None and cached_mtime == current_mtime:
                    # mtime unchanged, file is likely unchanged - skip hash calculation
                    cached_hash = cached_state.get("hash")
                    if cached_hash:
                        # File definitely unchanged
                        skipped_files.append(file_path)
                        print_verbose(f"Skipping (unchanged in cache): {file_path}", verbose)
                        needs_hash = False

            if needs_hash:
                # Calculate local hash (mtime changed or not in cache)
                local_hash = cache_manager.calculate_hash(file_path)
                if not local_hash:
                    print_verbose(
                        f"Warning: Could not calculate hash for {file_path}, skipping",
                        verbose,
                    )
                    continue

                if cached_state:
                    cached_hash = cached_state.get("hash")
                    if cached_hash == local_hash:
                        # Hash matches despite mtime change (e.g., touch, metadata change)
                        skipped_files.append(file_path)
                        print_verbose(
                            f"Skipping (unchanged content, mtime updated): {file_path}",
                            verbose,
                        )
                    else:
                        # Hash changed, needs update
                        remote_id = cached_state.get("remote_id")
                        if remote_id:
                            files_to_update.append((file_path, remote_id))
                            print_verbose(f"Update needed (content changed): {file_path}", verbose)
                        else:
                            # In cache but no remote ID? Treat as new
                            files_to_actually_upload.append(file_path)
                else:
                    # Not in cache, treat as new
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
                    # If delete fails (e.g. not found), we still try to upload
                    files_to_actually_upload.append(file_path)

        # Prepare results
        results: list[dict[str, Any]] = []

        # Add skipped files to results
        for skipped_file in skipped_files:
            results.append(
                {
                    "file": str(skipped_file),
                    "status": "skipped",
                    "reason": "Already exists in cache (content unchanged)",
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
            pending_count = 0

            # Progress bar
            with tqdm(
                total=len(files_to_actually_upload),
                desc="Uploading files",
                unit="file",
                file=sys.stderr,
            ) as pbar:

                def progress_callback(result: dict[str, Any]) -> None:
                    nonlocal \
                        success_count, \
                        failure_count, \
                        updated_count, \
                        skipped_count, \
                        pending_count
                    file_path = Path(result["file"])
                    abs_path = str(file_path.resolve())

                    if result["status"] in ("completed", "updated"):
                        # Update cache on success with remote_id
                        doc_name = result.get("document", {}).get("name")
                        if doc_name:
                            # Calculate hash again (or we could have passed it through)
                            # Re-calculating is safer to ensure what's on disk matches
                            # what we just uploaded
                            content_hash = cache_manager.calculate_hash(file_path)
                            file_mtime = file_path.stat().st_mtime
                            cache_manager.update_file_state(
                                normalized_name,
                                abs_path,
                                remote_id=doc_name,
                                content_hash=content_hash,
                                mtime=file_mtime,
                            )
                    elif result["status"] == "pending":
                        # Update cache with operation object (no-wait mode)
                        operation = result.get("operation")
                        if operation:
                            content_hash = cache_manager.calculate_hash(file_path)
                            file_mtime = file_path.stat().st_mtime
                            cache_manager.update_file_state(
                                normalized_name,
                                abs_path,
                                operation=operation,
                                content_hash=content_hash,
                                mtime=file_mtime,
                            )

                    if file_path in updated_files and result["status"] == "completed":
                        result["status"] = "updated"
                        updated_count += 1
                    elif result["status"] == "completed":
                        success_count += 1
                    elif result["status"] == "pending":
                        pending_count += 1
                    elif result["status"] == "skipped":
                        skipped_count += 1
                    else:
                        failure_count += 1

                    pbar.set_postfix(
                        {
                            "new": success_count,
                            "updated": updated_count,
                            "pending": pending_count,
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
                    wait_for_completion=not no_wait,
                )

                results.extend(upload_results)

            # Exit with error if all uploads failed (excluding skipped and pending)
            successful_uploads = success_count + updated_count + pending_count
            if failure_count > 0 and successful_uploads == 0 and skipped_count == 0:
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
