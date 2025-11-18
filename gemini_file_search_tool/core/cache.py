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
    """Manages a local JSON cache of uploaded files."""

    def __init__(self, app_name: str = "gemini-file-search-tool"):
        """Initialize the cache manager.

        Args:
            app_name: Name of the application (used for config directory)
        """
        self.app_name = app_name
        self.cache_dir = self._get_cache_dir()
        self.cache_file = self.cache_dir / "cache.json"
        self.cache: dict[str, Any] = self._load_cache()

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

    def _load_cache(self) -> dict[str, Any]:
        """Load the cache from disk.

        Returns:
            Dictionary containing cache data with structure {"stores": {...}}
        """
        if not self.cache_file.exists():
            return {"stores": {}}

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                return cast(dict[str, Any], json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}. Starting with empty cache.")
            return {"stores": {}}

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache file: {e}")

    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of the SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
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
        stores = self.cache.get("stores", {})
        store_cache = stores.get(store_name, {})
        return cast(dict[str, Any] | None, store_cache.get(file_path))

    def update_file_state(
        self,
        store_name: str,
        file_path: str,
        remote_id: str | None = None,
        content_hash: str | None = None,
    ) -> None:
        """Update the cached state of a file.

        Args:
            store_name: Name of the store
            file_path: Absolute path to the file
            remote_id: ID of the document in the store
            content_hash: SHA256 hash of the file content
        """
        if "stores" not in self.cache:
            self.cache["stores"] = {}

        if store_name not in self.cache["stores"]:
            self.cache["stores"][store_name] = {}

        # Get existing state to preserve fields if not provided
        current_state = self.cache["stores"][store_name].get(file_path, {})

        new_state = current_state.copy()
        if remote_id:
            new_state["remote_id"] = remote_id
        if content_hash:
            new_state["hash"] = content_hash

        # Always update timestamp
        import datetime

        new_state["last_uploaded"] = datetime.datetime.now(datetime.UTC).isoformat()

        self.cache["stores"][store_name][file_path] = new_state
        self._save_cache()

    def remove_file_state(self, store_name: str, file_path: str) -> None:
        """Remove a file from the cache.

        Args:
            store_name: Name of the store
            file_path: Absolute path to the file
        """
        if (
            "stores" in self.cache
            and store_name in self.cache["stores"]
            and file_path in self.cache["stores"][store_name]
        ):
            del self.cache["stores"][store_name][file_path]
            self._save_cache()

    def clear_store_cache(self, store_name: str) -> None:
        """Clear all cache entries for a specific store.

        Args:
            store_name: Name of the store
        """
        if "stores" in self.cache and store_name in self.cache["stores"]:
            del self.cache["stores"][store_name]
            self._save_cache()
