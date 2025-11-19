"""Local cache management for file search tool.

This module provides the CacheManager class for tracking the state of uploaded files
to avoid unnecessary re-uploads and API calls.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local JSON cache files for uploaded files (one file per store)."""

    def __init__(self, app_name: str = "gemini-file-search-tool"):
        """Initialize the cache manager.

        Args:
            app_name: Name of the application (used for config directory)
        """
        self.app_name = app_name
        self.cache_dir = self._get_cache_dir()
        self.stores_dir = self.cache_dir / "stores"
        self.stores_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_dir(self) -> Path:
        """Get the application cache directory.

        Follows XDG Base Directory specification on Linux, and standard locations
        on macOS/Windows.

        Returns:
            Path to the cache directory (~/.config/<app_name>)
        """
        # Use ~/.config/<app_name> as requested by user
        home = Path.home()
        config_dir = home / ".config" / self.app_name

        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _store_name_to_filename(self, store_name: str) -> str:
        """Convert store name to safe filename.

        Args:
            store_name: Store name (may contain slashes)

        Returns:
            Safe filename with slashes replaced by double underscores
        """
        # Replace / with __ to create safe filename
        # Example: "fileSearchStores/obsidian-abc" -> "fileSearchStores__obsidian-abc.json"
        return store_name.replace("/", "__") + ".json"

    def _load_cache(self, store_name: str) -> dict[str, Any]:
        """Load the cache for a specific store from disk.

        Args:
            store_name: Name of the store

        Returns:
            Dictionary mapping file paths to their cached state
        """
        cache_file = self.stores_dir / self._store_name_to_filename(store_name)

        if not cache_file.exists():
            logger.debug(f"Cache file does not exist for store '{store_name}': {cache_file}")
            return {}

        try:
            with open(cache_file, encoding="utf-8") as f:
                cache_data = cast(dict[str, Any], json.load(f))
                file_count = len(cache_data)
                logger.info(
                    f"Loaded cache for store '{store_name}': {file_count} file(s) from {cache_file}"
                )
                return cache_data
        except Exception as e:
            logger.warning(
                f"Failed to load cache file for '{store_name}': {e}. Starting with empty cache."
            )
            return {}

    def _save_cache(self, store_name: str, cache_data: dict[str, Any]) -> None:
        """Save the cache for a specific store to disk.

        Args:
            store_name: Name of the store
            cache_data: Cache data to save (dict mapping file paths to state)
        """
        cache_file = self.stores_dir / self._store_name_to_filename(store_name)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved cache for store '{store_name}' to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache file for '{store_name}': {e}")

    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of the SHA256 hash
        """
        logger.debug(f"Calculating SHA256 hash for: {file_path}")
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            hash_result = sha256_hash.hexdigest()
            logger.debug(f"Hash calculated: {hash_result[:16]}...")
            return hash_result
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def get_file_state(self, store_name: str, file_path: str) -> dict[str, Any] | None:
        """Get the cached state of a file.

        Args:
            store_name: Name of the store
            file_path: Absolute path to the file

        Returns:
            Dictionary with file state or None if not in cache
        """
        cache_data = self._load_cache(store_name)
        state = cast(dict[str, Any] | None, cache_data.get(file_path))
        if state:
            logger.debug(
                f"Cache hit for {Path(file_path).name}: "
                f"hash={state.get('hash', '')[:8]}..., "
                f"mtime={state.get('mtime', 'N/A')}"
            )
        else:
            logger.debug(f"Cache miss for {Path(file_path).name}")
        return state

    def update_file_state(
        self,
        store_name: str,
        file_path: str,
        remote_id: str | None = None,
        operation: dict[str, Any] | None = None,
        content_hash: str | None = None,
        mtime: float | None = None,
    ) -> None:
        """Update the cached state of a file.

        Uses last-one-wins strategy: New uploads overwrite existing pending operations.

        Args:
            store_name: Name of the store
            file_path: Absolute path to the file
            remote_id: ID of the document in the store (mutually exclusive with operation)
            operation: Operation object for pending uploads (mutually exclusive with remote_id)
            content_hash: SHA256 hash of the file content
            mtime: File modification time (Unix timestamp)

        Note:
            - If remote_id is provided, removes any existing operation object (upload complete)
            - If operation is provided, removes any existing remote_id (new pending upload)
            - Last-one-wins: Re-uploading a file overwrites previous operation/remote_id
        """
        # Load current cache for this store
        cache_data = self._load_cache(store_name)

        # Last-one-wins: Start fresh for this file
        new_state: dict[str, Any] = {}

        # Mutually exclusive: operation OR remote_id
        if remote_id:
            new_state["remote_id"] = remote_id
            logger.debug(f"Setting remote_id for {Path(file_path).name}")
        elif operation:
            new_state["operation"] = operation
            logger.debug(f"Setting operation for {Path(file_path).name}")

        # Always update hash and mtime if provided
        if content_hash:
            new_state["hash"] = content_hash
        if mtime is not None:
            new_state["mtime"] = mtime

        # Always update timestamp
        import datetime

        new_state["last_uploaded"] = datetime.datetime.now(datetime.UTC).isoformat()

        logger.info(
            f"Updating cache for {Path(file_path).name}: "
            f"remote_id={remote_id or 'N/A'}, "
            f"operation={'present' if operation else 'N/A'}, "
            f"hash={content_hash[:8] + '...' if content_hash else 'N/A'}, "
            f"mtime={mtime or 'N/A'}"
        )

        cache_data[file_path] = new_state
        self._save_cache(store_name, cache_data)

    def remove_file_state(self, store_name: str, file_path: str) -> None:
        """Remove a file from the cache.

        Args:
            store_name: Name of the store
            file_path: Absolute path to the file
        """
        cache_data = self._load_cache(store_name)
        if file_path in cache_data:
            logger.info(f"Removing {Path(file_path).name} from cache")
            del cache_data[file_path]
            self._save_cache(store_name, cache_data)

    def clear_store_cache(self, store_name: str) -> None:
        """Clear all cache entries for a specific store.

        Args:
            store_name: Name of the store
        """
        cache_file = self.stores_dir / self._store_name_to_filename(store_name)
        if cache_file.exists():
            cache_data = self._load_cache(store_name)
            file_count = len(cache_data)
            logger.info(f"Clearing cache for store '{store_name}' ({file_count} file(s))")
            cache_file.unlink()  # Delete the file

    def get_pending_operations(self, store_name: str) -> dict[str, dict[str, Any]]:
        """Get all files with pending operations.

        Args:
            store_name: Name of the store

        Returns:
            Dictionary mapping file paths to their operation objects
        """
        cache_data = self._load_cache(store_name)
        pending = {
            path: state
            for path, state in cache_data.items()
            if "operation" in state and state["operation"] is not None
        }
        logger.debug(f"Found {len(pending)} file(s) with pending operations")
        return pending

    def get_cache_stats(self, store_name: str) -> dict[str, Any]:
        """Get statistics about the cache.

        Args:
            store_name: Name of the store

        Returns:
            Dictionary with cache statistics:
            - total_files: Total number of cached files
            - completed: Files with remote_id (upload complete)
            - pending_operations: Files with pending operations
            - failed_operations: Files with failed operations (done=True but no remote_id)
        """
        cache_data = self._load_cache(store_name)
        stats = {
            "total_files": len(cache_data),
            "completed": 0,
            "pending_operations": 0,
            "failed_operations": 0,
        }

        for state in cache_data.values():
            if "remote_id" in state and state["remote_id"]:
                stats["completed"] += 1
            elif "operation" in state and state["operation"]:
                operation = state["operation"]
                # Check if operation is done but failed (no remote_id)
                if isinstance(operation, dict) and operation.get("done", False):
                    stats["failed_operations"] += 1
                else:
                    stats["pending_operations"] += 1

        return stats
