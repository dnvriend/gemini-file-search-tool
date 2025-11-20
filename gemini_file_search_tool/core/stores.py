"""File search store management operations.

This module provides functions for creating, listing, retrieving, updating,
and deleting Gemini file search stores.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from typing import Any

from gemini_file_search_tool.core.client import get_client


class StoreError(Exception):
    """Base exception for store-related errors."""

    pass


class StoreNotFoundError(StoreError):
    """Raised when a store is not found."""

    def __init__(self, store_name: str) -> None:
        super().__init__(f"Store '{store_name}' not found")
        self.store_name = store_name


def create_store(name: str) -> dict[str, Any]:
    """Create a new file search store.

    Args:
        name: Display name for the file search store

    Returns:
        Dictionary containing:
            - name: Full resource name (e.g., 'fileSearchStores/xxx')
            - display_name: Display name of the store

    Raises:
        StoreError: If store creation fails
    """
    try:
        client = get_client()
        file_search_store = client.file_search_stores.create(config={"display_name": name})

        return {
            "name": file_search_store.name,
            "display_name": file_search_store.display_name,
        }
    except Exception as e:
        raise StoreError(f"Failed to create store: {str(e)}") from e


def list_stores() -> list[dict[str, Any]]:
    """List all file search stores.

    Returns:
        List of dictionaries, each containing:
            - name: Full resource name
            - display_name: Display name of the store

    Raises:
        StoreError: If listing stores fails
    """
    try:
        client = get_client()
        stores = []
        for store in client.file_search_stores.list():
            stores.append(
                {
                    "name": store.name,
                    "display_name": store.display_name,
                }
            )
        return stores
    except Exception as e:
        raise StoreError(f"Failed to list stores: {str(e)}") from e


def get_store(store_name: str) -> dict[str, Any]:
    """Get details of a specific file search store.

    Args:
        store_name: Store name (full resource name or ID)

    Returns:
        Dictionary containing:
            - name: Full resource name
            - display_name: Display name of the store
            - size_bytes: Store size in bytes (if available)
            - size: Human-readable size (if available)
            - document_count: Number of documents in the store

    Raises:
        StoreNotFoundError: If the store is not found
        StoreError: If retrieving store details fails
    """
    try:
        client = get_client()
        store = client.file_search_stores.get(name=store_name)

        # Build base store info
        store_info: dict[str, Any] = {
            "name": store.name,
            "display_name": store.display_name,
        }

        # Try to extract size information if available
        size_attrs = [
            "size_bytes",
            "storage_size",
            "size",
            "total_size",
            "storage_bytes",
            "bytes_used",
        ]
        for attr in size_attrs:
            if hasattr(store, attr):
                value = getattr(store, attr)
                if value is not None:
                    store_info["size_bytes"] = value
                    # Convert to human-readable format
                    if value >= 1024 * 1024 * 1024:  # GB
                        store_info["size"] = f"{value / (1024 * 1024 * 1024):.2f} GB"
                    elif value >= 1024 * 1024:  # MB
                        store_info["size"] = f"{value / (1024 * 1024):.2f} MB"
                    elif value >= 1024:  # KB
                        store_info["size"] = f"{value / 1024:.2f} KB"
                    else:
                        store_info["size"] = f"{value} bytes"
                    break

        # Count documents in the store
        try:
            document_count = 0
            for _ in client.file_search_stores.documents.list(parent=store_name):
                document_count += 1
            store_info["document_count"] = document_count
        except Exception:  # nosec B110
            # Non-fatal: continue without document count
            pass

        return store_info
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            raise StoreNotFoundError(store_name) from e
        raise StoreError(f"Failed to get store: {error_msg}") from e


def update_store(store_name: str, display_name: str) -> dict[str, Any]:
    """Update a file search store's display name.

    Args:
        store_name: Store name (full resource name or ID)
        display_name: New display name for the store

    Returns:
        Dictionary containing:
            - name: Full resource name
            - display_name: Updated display name

    Raises:
        StoreNotFoundError: If the store is not found
        StoreError: If updating the store fails

    Note:
        The Google GenAI API may not support updating stores directly.
        This implementation attempts to use the update method if available.
    """
    try:
        client = get_client()

        # Get current store
        store = client.file_search_stores.get(name=store_name)

        # Note: The update method may not be available in all versions of the API
        # This is a placeholder that may need adjustment based on actual API capabilities
        if hasattr(client.file_search_stores, "update"):
            # Update display name
            store.display_name = display_name

            # Apply the update
            updated_store = client.file_search_stores.update(
                name=store_name,
                file_search_store=store,
                update_mask="display_name",
            )

            return {
                "name": updated_store.name,
                "display_name": updated_store.display_name,
            }
        else:
            raise StoreError(
                "Update operation is not supported by the current API version. "
                "Consider deleting and recreating the store with the new name."
            )
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            raise StoreNotFoundError(store_name) from e
        raise StoreError(f"Failed to update store: {error_msg}") from e


def delete_store(store_name: str, force: bool = False) -> dict[str, Any]:
    """Delete a file search store.

    Args:
        store_name: Store name (full resource name or ID)
        force: Force deletion without confirmation

    Returns:
        Dictionary containing:
            - status: 'deleted'
            - name: Full resource name of deleted store

    Raises:
        StoreNotFoundError: If the store is not found
        StoreError: If deleting the store fails
    """
    try:
        client = get_client()
        client.file_search_stores.delete(name=store_name, config={"force": force})

        return {"status": "deleted", "name": store_name}
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            raise StoreNotFoundError(store_name) from e
        raise StoreError(f"Failed to delete store: {error_msg}") from e
