"""Smoke test: the staging layer is importable with the pytest configuration."""

import staging.src


def test_staging_layer_is_importable() -> None:
    """Import the staging.src namespace package from the test runner."""
    assert staging.src.__name__ == "staging.src"
