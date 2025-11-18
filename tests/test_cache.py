import shutil
import tempfile
import unittest
from pathlib import Path

from gemini_file_search_tool.core.cache import CacheManager


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(app_name="test-app")
        # Override cache dir for testing
        self.cache_manager.cache_dir = self.test_dir
        self.cache_manager.cache_file = self.test_dir / "cache.json"
        self.cache_manager.cache = {"stores": {}}

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_calculate_hash(self):
        test_file = self.test_dir / "test.txt"
        with open(test_file, "w") as f:
            f.write("hello world")

        # echo -n "hello world" | shasum -a 256
        expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        calculated_hash = self.cache_manager.calculate_hash(test_file)
        self.assertEqual(calculated_hash, expected_hash)

    def test_update_and_get_state(self):
        store = "test-store"
        file_path = "/path/to/file.py"
        remote_id = "documents/123"
        content_hash = "abc123hash"
        mtime = 1731969000.0

        self.cache_manager.update_file_state(store, file_path, remote_id, content_hash, mtime)

        state = self.cache_manager.get_file_state(store, file_path)
        self.assertIsNotNone(state)
        self.assertEqual(state["remote_id"], remote_id)
        self.assertEqual(state["hash"], content_hash)
        self.assertEqual(state["mtime"], mtime)
        self.assertIn("last_uploaded", state)

    def test_persistence(self):
        store = "test-store"
        file_path = "/path/to/file.py"

        self.cache_manager.update_file_state(store, file_path, "doc/1", "hash1")

        # Create new manager instance to verify load from disk
        new_manager = CacheManager(app_name="test-app")
        new_manager.cache_dir = self.test_dir
        new_manager.cache_file = self.test_dir / "cache.json"
        new_manager.cache = new_manager._load_cache()

        state = new_manager.get_file_state(store, file_path)
        self.assertIsNotNone(state)
        self.assertEqual(state["remote_id"], "doc/1")


if __name__ == "__main__":
    unittest.main()
