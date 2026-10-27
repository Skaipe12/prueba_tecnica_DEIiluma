"""Tests for RawLoader without a database."""

import re
from datetime import datetime
from decimal import Decimal

import pandas as pd
from psycopg.types.json import Jsonb

from raw.src.config.constants import CSV_COLUMNS, RAW_COPY_TYPES
from raw.src.queries.queries import PipelineQueries
from raw.src.resources.data_factory import DataFactory
from raw.src.resources.raw_loader import RawLoader
from raw.src.resources.schemas.schema import RAW_JOB_POSTINGS_SCHEMA
from raw.src.resources.validator import Validator


def make_valid(rows: list[dict[str, str]]) -> pd.DataFrame:
    chunk = pd.DataFrame(rows, columns=list(CSV_COLUMNS), dtype=str)
    valid, _ = Validator.split_valid_invalid(DataFactory.to_typed(chunk))
    return valid


def make_row(**overrides: str) -> dict[str, str]:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        job_title="Data Analyst",
        job_posted_date="2023-01-14 13:18:07",
        job_work_from_home="True",
    )
    row.update(overrides)
    return row


def first_row(valid: pd.DataFrame) -> dict:
    row = next(RawLoader(PipelineQueries()).to_rows(valid))
    return dict(zip(valid.columns, row, strict=True))


def test_copy_statement_lists_the_same_columns_as_the_schema() -> None:
    statement = PipelineQueries().copy_job_postings()
    listed = re.search(r"\((.*)\)", statement, re.DOTALL).group(1)

    columns = [column.strip() for column in listed.split(",")]

    assert columns == list(RAW_JOB_POSTINGS_SCHEMA.columns)


def test_copy_types_has_one_type_per_column() -> None:
    assert len(RAW_COPY_TYPES) == len(RAW_JOB_POSTINGS_SCHEMA.columns)


def test_to_rows_yields_one_tuple_per_row_with_every_column() -> None:
    valid = make_valid([make_row(), make_row()])

    rows = list(RawLoader(PipelineQueries()).to_rows(valid))

    assert len(rows) == 2
    assert all(len(row) == len(RAW_JOB_POSTINGS_SCHEMA.columns) for row in rows)


def test_to_rows_converts_values_to_python_types() -> None:
    valid = make_valid([make_row(salary_year_avg="157500.0", job_skills="['sql', 'sql']")])

    row = first_row(valid)

    assert row["job_title"] == "Data Analyst"
    assert row["job_work_from_home"] is True
    assert row["job_posted_date"] == datetime(2023, 1, 14, 13, 18, 7)
    assert row["salary_year_avg"] == Decimal("157500.0")
    assert row["job_skills"] == ["sql", "sql"]


def test_to_rows_turns_nulls_into_none() -> None:
    valid = make_valid([make_row(job_title="", job_work_from_home="")])

    row = first_row(valid)

    assert row["job_title"] is None
    assert row["job_work_from_home"] is None
    assert row["salary_hour_avg"] is None
    assert row["job_skills"] is None
    assert row["job_type_skills"] is None


def test_to_rows_wraps_skill_types_as_jsonb() -> None:
    valid = make_valid([make_row(job_type_skills="{'cloud': ['aws']}")])

    row = first_row(valid)

    assert isinstance(row["job_type_skills"], Jsonb)
    assert row["job_type_skills"].obj == {"cloud": ["aws"]}
