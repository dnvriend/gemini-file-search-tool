"""Tests for gemini_file_search_tool.utils module.

Note: This code was generated with assistance from AI coding tools
and has been reviewed and tested by a human.
"""

import pytest

from gemini_file_search_tool.utils import estimate_cost, normalize_store_name, output_json


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


def test_estimate_cost_flash_model() -> None:
    """Test cost estimation for gemini-2.5-flash model."""
    usage = {"prompt_token_count": 1000, "candidates_token_count": 2000, "total_token_count": 3000}
    result = estimate_cost(usage, "gemini-2.5-flash")

    assert result is not None
    assert result["model"] == "gemini-2.5-flash"
    assert result["currency"] == "USD"
    # Flash pricing: $0.075 per 1M input, $0.30 per 1M output
    # Input cost: 1000 / 1_000_000 * 0.075 = 0.000075
    # Output cost: 2000 / 1_000_000 * 0.30 = 0.0006
    # Total: 0.000675
    assert result["input_cost_usd"] == pytest.approx(0.000075)
    assert result["output_cost_usd"] == pytest.approx(0.0006)
    assert result["total_cost_usd"] == pytest.approx(0.000675)


def test_estimate_cost_pro_model() -> None:
    """Test cost estimation for gemini-2.5-pro model."""
    usage = {"prompt_token_count": 500, "candidates_token_count": 1000, "total_token_count": 1500}
    result = estimate_cost(usage, "gemini-2.5-pro")

    assert result is not None
    assert result["model"] == "gemini-2.5-pro"
    # Pro pricing: $1.25 per 1M input, $5.00 per 1M output
    # Input cost: 500 / 1_000_000 * 1.25 = 0.000625
    # Output cost: 1000 / 1_000_000 * 5.00 = 0.005
    # Total: 0.005625
    assert result["input_cost_usd"] == pytest.approx(0.000625)
    assert result["output_cost_usd"] == pytest.approx(0.005)
    assert result["total_cost_usd"] == pytest.approx(0.005625)


def test_estimate_cost_none_usage() -> None:
    """Test cost estimation with None usage_metadata."""
    result = estimate_cost(None, "gemini-2.5-flash")
    assert result is None


def test_estimate_cost_unknown_model() -> None:
    """Test cost estimation with unknown model raises ValueError."""
    usage = {"prompt_token_count": 100, "candidates_token_count": 200, "total_token_count": 300}
    with pytest.raises(ValueError, match="Unknown model"):
        estimate_cost(usage, "gemini-unknown-model")


def test_estimate_cost_zero_tokens() -> None:
    """Test cost estimation with zero tokens."""
    usage = {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0}
    result = estimate_cost(usage, "gemini-2.5-flash")

    assert result is not None
    assert result["input_cost_usd"] == 0.0
    assert result["output_cost_usd"] == 0.0
    assert result["total_cost_usd"] == 0.0


def test_output_json_no_scientific_notation(capsys: object) -> None:
    """Test that output_json formats small floats without scientific notation."""
    import json

    # Create data with very small float values
    test_data = {
        "name": "test",
        "cost": 0.00000045,
        "large_cost": 123.456,
        "nested": {"small_value": 8.58e-05, "normal_value": 42},
    }

    output_json(test_data)
    captured = capsys.readouterr()  # type: ignore[attr-defined]

    # Verify no scientific notation in output
    assert "e-" not in captured.out.lower()
    assert "e+" not in captured.out.lower()

    # Verify values are still correct when parsed back
    parsed = json.loads(captured.out)
    assert parsed["cost"] == pytest.approx(0.00000045)
    assert parsed["large_cost"] == pytest.approx(123.456)
    assert parsed["nested"]["small_value"] == pytest.approx(8.58e-05)
    assert parsed["nested"]["normal_value"] == 42
