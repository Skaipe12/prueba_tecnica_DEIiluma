"""Smoke test: the raw layer is importable with the pytest configuration."""

import raw.src


def test_raw_layer_is_importable() -> None:
    """Import the raw.src namespace package from the test runner."""
    assert raw.src.__name__ == "raw.src"
