"""Tests for Validator."""

from pathlib import Path

import pandas as pd
import pytest

from src.config.constants import CSV_COLUMNS
from src.resources.data_factory import DataFactory
from src.resources.validator import Validator


def make_row(**overrides: str) -> dict[str, str]:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        job_title="Data Analyst",
        job_posted_date="2023-01-14 13:18:07",
        job_work_from_home="False",
    )
    row.update(overrides)
    return row


def make_typed(rows: list[dict[str, str]]) -> pd.DataFrame:
    return DataFactory.to_typed(pd.DataFrame(rows, columns=list(CSV_COLUMNS), dtype=str))


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


def test_split_valid_invalid_keeps_a_clean_dataframe_whole() -> None:
    typed = make_typed([make_row(), make_row(job_skills="['sql']")])

    valid, rejected = Validator.split_valid_invalid(typed)

    assert len(valid) == 2
    assert rejected.empty


def test_split_valid_invalid_drops_parse_errors_from_valid_rows() -> None:
    valid, _ = Validator.split_valid_invalid(make_typed([make_row()]))

    assert list(valid.columns) == [*CSV_COLUMNS, "row_hash"]


def test_split_valid_invalid_rejects_rows_that_could_not_be_converted() -> None:
    typed = make_typed([make_row(), make_row(job_posted_date="not-a-date"), make_row()])

    valid, rejected = Validator.split_valid_invalid(typed)

    assert list(valid.index) == [0, 2]
    assert list(rejected.index) == [1]
    assert rejected.loc[1, "errors"] == "job_posted_date"


def test_split_valid_invalid_reports_every_failed_column_of_a_row() -> None:
    typed = make_typed([make_row(job_work_from_home="yes", job_skills="['sql'")])

    _, rejected = Validator.split_valid_invalid(typed)

    assert rejected.loc[0, "errors"] == "job_work_from_home,job_skills"


def test_split_valid_invalid_keeps_rows_with_empty_values() -> None:
    typed = make_typed([make_row(job_title="", salary_year_avg="-5")])

    valid, rejected = Validator.split_valid_invalid(typed)

    assert len(valid) == 1
    assert rejected.empty


def test_split_valid_invalid_accepts_an_empty_dataframe() -> None:
    typed = make_typed([make_row()]).iloc[0:0]

    valid, rejected = Validator.split_valid_invalid(typed)

    assert valid.empty
    assert rejected.empty


def test_validate_schema_accepts_the_valid_rows() -> None:
    valid, _ = Validator.split_valid_invalid(make_typed([make_row(), make_row()]))

    Validator.validate_schema(valid)


def test_validate_schema_names_the_column_that_does_not_match() -> None:
    valid, _ = Validator.split_valid_invalid(make_typed([make_row()]))
    valid["job_work_from_home"] = valid["job_work_from_home"].astype(object)

    with pytest.raises(ValueError, match="job_work_from_home"):
        Validator.validate_schema(valid)


def test_validate_schema_rejects_the_dataframe_that_still_has_parse_errors() -> None:
    with pytest.raises(ValueError, match="parse_errors"):
        Validator.validate_schema(make_typed([make_row()]))


@pytest.mark.parametrize(("rejected", "total"), [(0, 100), (1, 100), (0, 0)])
def test_validate_reject_ratio_accepts_ratios_up_to_the_maximum(rejected: int, total: int) -> None:
    Validator.validate_reject_ratio(rejected, total, max_ratio=0.01)


def test_validate_reject_ratio_rejects_ratios_above_the_maximum() -> None:
    with pytest.raises(ValueError, match="Too many rejected rows: 2 of 100"):
        Validator.validate_reject_ratio(2, 100, max_ratio=0.01)
