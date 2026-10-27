"""Tests for the logger configuration."""

from raw.src.config.logger import get_logger


def test_get_logger_returns_named_logger() -> None:
    assert get_logger("pipeline.probe").name == "pipeline.probe"
