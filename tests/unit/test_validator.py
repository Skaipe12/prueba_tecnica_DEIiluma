"""Tests for Validator."""

from pathlib import Path

import pytest

from src.config.constants import CSV_COLUMNS
from src.resources.validator import Validator


def write_header(tmp_path: Path, columns: list[str] | tuple[str, ...]) -> Path:
    path = tmp_path / "jobs.csv"
    path.write_text(",".join(columns) + "\n", encoding="utf-8")
    return path


def test_validate_file_rejects_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        Validator.validate_file(tmp_path / "missing.csv")


def test_validate_header_accepts_the_expected_columns(tmp_path: Path) -> None:
    Validator.validate_header(write_header(tmp_path, CSV_COLUMNS))


def test_validate_header_accepts_a_file_with_bom(tmp_path: Path) -> None:
    path = tmp_path / "jobs.csv"
    path.write_text(",".join(CSV_COLUMNS) + "\n", encoding="utf-8-sig")

    Validator.validate_header(path)


def test_validate_header_reports_a_missing_column(tmp_path: Path) -> None:
    path = write_header(tmp_path, CSV_COLUMNS[:-1])

    with pytest.raises(ValueError, match="missing=.*job_type_skills"):
        Validator.validate_header(path)


def test_validate_header_reports_an_unexpected_column(tmp_path: Path) -> None:
    path = write_header(tmp_path, [*CSV_COLUMNS, "extra_column"])

    with pytest.raises(ValueError, match="unexpected=.*extra_column"):
        Validator.validate_header(path)


def test_validate_header_rejects_columns_in_a_different_order(tmp_path: Path) -> None:
    path = write_header(tmp_path, list(reversed(CSV_COLUMNS)))

    with pytest.raises(ValueError, match="Unexpected CSV header"):
        Validator.validate_header(path)
