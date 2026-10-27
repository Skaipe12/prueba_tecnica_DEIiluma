"""Smoke test: the src package is importable with the pytest configuration."""

import src


def test_src_package_is_importable() -> None:
    """Import the src namespace package from the test runner."""
    assert src.__name__ == "src"
