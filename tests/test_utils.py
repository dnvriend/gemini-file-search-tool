"""Tests for gemini_file_search_tool.utils module.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

from gemini_file_search_tool.utils import normalize_store_name, output_json


def test_normalize_store_name_full_resource() -> None:
    """Test that full resource names are returned as-is."""
    result = normalize_store_name("fileSearchStores/test-123")
    assert result == "fileSearchStores/test-123"


def test_normalize_store_name_with_slash() -> None:
    """Test that names with slashes are returned as-is."""
    result = normalize_store_name("test/123")
    assert result == "test/123"


def test_normalize_store_name_with_hyphen() -> None:
    """Test that IDs with hyphens are prefixed."""
    result = normalize_store_name("test-123")
    assert result == "fileSearchStores/test-123"


def test_output_json_dict(capsys: object) -> None:
    """Test output_json with a dictionary."""
    test_data = {"name": "test", "value": 123}
    output_json(test_data)
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert '"name": "test"' in captured.out
    assert '"value": 123' in captured.out


def test_output_json_list(capsys: object) -> None:
    """Test output_json with a list of dictionaries."""
    test_data = [{"name": "test1"}, {"name": "test2"}]
    output_json(test_data)
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert '"name": "test1"' in captured.out
    assert '"name": "test2"' in captured.out
