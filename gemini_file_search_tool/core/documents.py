"""Document management operations for file search stores.

This module provides functions for listing and uploading documents to
Gemini file search stores.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import logging
import mimetypes
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from gemini_file_search_tool.core.client import get_client

logger = logging.getLogger(__name__)

# Register additional MIME types for common configuration files
# This ensures files with non-standard extensions can be uploaded successfully
mimetypes.add_type("text/toml", ".toml")
mimetypes.add_type("text/plain", ".env")
mimetypes.add_type("text/plain", ".txt")
mimetypes.add_type("text/markdown", ".md")


class DocumentError(Exception):
    """Base exception for document-related errors."""

    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""

    def __init__(self, document_name: str) -> None:
        super().__init__(f"Document '{document_name}' not found")
        self.document_name = document_name


class FileValidationError(DocumentError):
    """Raised when a file fails validation."""

    pass


def list_documents(store_name: str) -> list[dict[str, Any]]:
    """List all documents in a file search store.

    Args:
        store_name: Store name (full resource name or ID)

    Returns:
        List of dictionaries, each containing:
            - name: Full document resource name
            - display_name: Display name of the document

    Raises:
        DocumentError: If listing documents fails

    Note:
        Uses REST API directly as a workaround for SDK bug #1661.
        See: https://github.com/googleapis/python-genai/issues/1661
        The SDK's documents.list() method requires a 'parent' parameter that
        causes issues, so we use the REST API directly with 'key' parameter.
    """
    try:
        # Get API key for REST API call (workaround for SDK bug #1661)
        # Note: This workaround only works with Developer API (not Vertex AI)
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # Check if using Vertex AI
            if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in (
                "true",
                "1",
                "yes",
            ):
                raise DocumentError(
                    "Listing documents with Vertex AI is not supported due to SDK bug #1661. "
                    "Use Developer API (GEMINI_API_KEY or GOOGLE_API_KEY) instead."
                )
            raise DocumentError(
                "API key required for listing documents. "
                "Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
            )

        # REST API endpoint
        base_url = "https://generativelanguage.googleapis.com/v1alpha"
        url = f"{base_url}/{store_name}/documents"

        documents = []
        page_token = None

        while True:
            params: dict[str, str] = {"key": api_key}
            if page_token:
                params["pageToken"] = page_token

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract documents from response
            if "documents" in data:
                for doc in data["documents"]:
                    documents.append(
                        {
                            "name": doc.get("name", ""),
                            "display_name": doc.get("displayName", ""),
                        }
                    )

            # Check for pagination
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return documents
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise DocumentError(f"Store '{store_name}' not found") from e
        raise DocumentError(f"HTTP {e.response.status_code}: {e.response.text}") from e
    except Exception as e:
        raise DocumentError(f"Failed to list documents: {str(e)}") from e


def _validate_file(file_path: Path, skip_validation: bool) -> None:
    """Validate a file before upload.

    Args:
        file_path: Path to the file to validate
        skip_validation: Skip validation checks

    Raises:
        FileValidationError: If validation fails
    """
    # Check file exists
    if not file_path.exists():
        raise FileValidationError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileValidationError(f"Path is not a file: {file_path}")

    if skip_validation:
        return

    # Check file size
    file_size = file_path.stat().st_size

    # Check for empty files (0 bytes)
    # Empty files provide no value for RAG/search and cause API errors
    if file_size == 0:
        raise FileValidationError(
            f"Empty file (0 bytes) - skipping. Empty files provide no value for search: {file_path}"
        )

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise FileValidationError(
            f"File too large ({file_size / (1024 * 1024):.1f}MB > "
            f"{max_size / (1024 * 1024):.0f}MB): {file_path}"
        )

    # Check for base64 images (can cause upload failures)
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read(1024 * 10)  # Read first 10KB
            if "data:image/" in content and ";base64," in content:
                raise FileValidationError(
                    f"File contains base64-encoded images which may cause "
                    f"upload failures. Use --skip-validation to bypass: {file_path}"
                )
    except UnicodeDecodeError:
        # Binary file, skip content check
        pass
    except FileValidationError:
        # Re-raise validation errors
        raise
    except Exception:
        # Non-fatal: continue with upload attempt
        pass


def upload_file(
    file_path: Path,
    store_name: str,
    title: str | None = None,
    url: str | None = None,
    file_name: str | None = None,
    max_tokens: int = 200,
    max_overlap: int = 20,
    skip_validation: bool = False,
) -> dict[str, Any]:
    """Upload a single file to a file search store.

    Args:
        file_path: Path to the file to upload
        store_name: Store name (full resource name or ID)
        title: Custom metadata title (optional)
        url: Custom metadata URL (optional)
        file_name: Custom metadata file_name (optional)
        max_tokens: Max tokens per chunk (default: 200)
        max_overlap: Max overlap tokens (default: 20)
        skip_validation: Skip file validation checks

    Returns:
        Dictionary containing:
            - file: File path (as string)
            - status: 'completed' or 'failed'
            - operation: Operation name (if available)
            - document: Document info dict with name and display_name (if successful)
            - error: Error message (if failed)

    Raises:
        DocumentError: If upload fails
    """
    result: dict[str, Any] = {
        "file": str(file_path),
        "status": "failed",
    }

    try:
        # Log upload start
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"Uploading: {file_path} ({file_size_mb:.2f}MB) to store '{store_name}'")

        # Validate file
        logger.debug(f"Validating file: {file_path}")
        _validate_file(file_path, skip_validation)
        logger.debug(f"File validation passed: {file_path}")

        client = get_client()

        # Use full pathname as display name
        display_name = str(file_path)

        # Build config
        config: dict[str, Any] = {"display_name": display_name}

        # Add chunking config if custom values provided
        if max_tokens != 200 or max_overlap != 20:
            config["chunking_config"] = {
                "white_space_config": {
                    "max_tokens_per_chunk": max_tokens,
                    "max_overlap_tokens": max_overlap,
                }
            }

        # Add custom metadata if provided
        custom_metadata = []
        if title:
            custom_metadata.append({"key": "title", "string_value": title})
        if url:
            custom_metadata.append({"key": "url", "string_value": url})
        if file_name:
            custom_metadata.append({"key": "file_name", "string_value": file_name})

        if custom_metadata:
            config["custom_metadata"] = custom_metadata

        # Upload file
        logger.debug(f"Starting upload operation for: {file_path}")
        operation = client.file_search_stores.upload_to_file_search_store(
            file=str(file_path),
            file_search_store_name=store_name,
            config=config,  # type: ignore[arg-type]
        )

        operation_id = operation.name if hasattr(operation, "name") else "unknown"
        logger.debug(f"Operation started: {operation_id}")

        # Poll for completion with exponential backoff
        poll_interval = 2
        max_interval = 30
        poll_count = 0

        while not operation.done:
            poll_count += 1
            logger.debug(f"Polling operation {operation_id} (attempt {poll_count}) - waiting {poll_interval}s")
            time.sleep(poll_interval)
            operation = client.operations.get(operation)

            # Exponential backoff: increase polling interval up to max
            poll_interval = min(poll_interval * 1.5, max_interval)

        if operation.error:
            error_msg = f"Upload failed: {operation.error}"
            logger.error(f"Operation {operation_id} failed: {operation.error}")
            logger.error(f"File: {file_path}")
            result["error"] = error_msg
            result["operation_id"] = operation_id
            return result

        # Success
        result["status"] = "completed"
        result["operation"] = operation.name if hasattr(operation, "name") else None
        logger.info(f"Upload completed successfully: {file_path}")

        # Try to get document info from operation response
        if hasattr(operation, "response") and operation.response:
            result["document"] = {
                "name": getattr(operation.response, "name", None),
                "display_name": display_name,
            }

        return result
    except FileValidationError as e:
        error_msg = str(e)

        # Check if it's an empty file (should be treated as warning, not error)
        if "Empty file (0 bytes)" in error_msg:
            logger.warning(f"Skipping empty file: {file_path}")
            result["status"] = "skipped"
            result["reason"] = "Empty file (0 bytes) - no content to index"
        else:
            logger.error(f"File validation failed: {file_path}")
            logger.error(f"Validation error: {error_msg}")
            result["error"] = error_msg

        return result
    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        logger.error(f"Upload exception for {file_path}: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.debug(f"Full traceback:", exc_info=True)
        result["error"] = error_msg
        return result


def upload_files_concurrent(
    files: list[Path],
    store_name: str,
    title: str | None = None,
    url: str | None = None,
    file_name: str | None = None,
    max_tokens: int = 200,
    max_overlap: int = 20,
    skip_validation: bool = False,
    num_workers: int | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Upload multiple files concurrently to a file search store.

    Args:
        files: List of file paths to upload
        store_name: Store name (full resource name or ID)
        title: Custom metadata title (optional, applies to all files)
        url: Custom metadata URL (optional, applies to all files)
        file_name: Custom metadata file_name (optional, applies to all files)
        max_tokens: Max tokens per chunk (default: 200)
        max_overlap: Max overlap tokens (default: 20)
        skip_validation: Skip file validation checks
        num_workers: Number of concurrent workers (default: CPU count)
        progress_callback: Optional callback function called after each upload
            completes. Receives the result dict.

    Returns:
        List of dictionaries, one per file, each containing:
            - file: File path (as string)
            - status: 'completed', 'failed', 'skipped', or 'updated'
            - operation: Operation name (if available)
            - document: Document info (if successful)
            - error: Error message (if failed)
            - reason: Reason for skip (if skipped)

    Raises:
        DocumentError: If a critical error occurs
    """
    if not files:
        return []

    # Set default num_workers to conservative value for I/O-bound operations
    # File uploads are network-bound, not CPU-bound, so using CPU count is excessive
    # A conservative default of 4 balances throughput with API stability
    if num_workers is None:
        num_workers = min(4, os.cpu_count() or 1)
        logger.debug(f"Using default num_workers: {num_workers}")

    # Prepare arguments for upload function
    upload_args = [
        (
            file_path,
            store_name,
            title,
            url,
            file_name,
            max_tokens,
            max_overlap,
            skip_validation,
        )
        for file_path in files
    ]

    results: list[dict[str, Any]] = []

    # Process files concurrently
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(upload_file, *args): args[0] for args in upload_args}

        # Process completed tasks
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append(result)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(result)
            except Exception as e:
                # Handle unexpected errors
                error_result: dict[str, Any] = {
                    "file": str(file_path),
                    "status": "failed",
                    "error": f"Unexpected error: {str(e)}",
                }
                results.append(error_result)

                if progress_callback:
                    progress_callback(error_result)

    return results


def delete_document(document_name: str, force: bool = True) -> dict[str, Any]:
    """Delete a document from a file search store.

    Args:
        document_name: Full document resource name
        force: Force deletion (default: True)

    Returns:
        Dictionary containing:
            - status: 'deleted'
            - name: Full resource name of deleted document

    Raises:
        DocumentNotFoundError: If the document is not found
        DocumentError: If deleting the document fails
    """
    try:
        client = get_client()
        client.file_search_stores.documents.delete(name=document_name, config={"force": force})

        return {"status": "deleted", "name": document_name}
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            raise DocumentNotFoundError(document_name) from e
        raise DocumentError(f"Failed to delete document: {error_msg}") from e
