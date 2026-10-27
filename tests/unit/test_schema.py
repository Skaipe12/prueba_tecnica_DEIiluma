"""Tests for the raw table schema."""

import pandas as pd
import pandera.pandas as pa
import pytest

from src.config.constants import CSV_COLUMNS
from src.resources.data_factory import DataFactory
from src.resources.schemas.schema import RAW_JOB_POSTINGS_SCHEMA


def make_typed() -> pd.DataFrame:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        job_title="Data Analyst",
        job_posted_date="2023-01-14 13:18:07",
        job_work_from_home="False",
        salary_year_avg="100000.0",
        job_skills="['sql']",
        job_type_skills="{'programming': ['sql']}",
    )
    chunk = pd.DataFrame([row], columns=list(CSV_COLUMNS), dtype=str)
    return DataFactory.to_typed(chunk).drop(columns="parse_errors")


def test_schema_has_the_csv_columns_followed_by_row_hash() -> None:
    assert list(RAW_JOB_POSTINGS_SCHEMA.columns) == [*CSV_COLUMNS, "row_hash"]


def test_schema_accepts_the_output_of_data_factory() -> None:
    RAW_JOB_POSTINGS_SCHEMA.validate(make_typed())


def test_schema_accepts_null_values() -> None:
    typed = make_typed()
    typed["job_title"] = pd.NA
    typed["job_posted_date"] = pd.NaT

    RAW_JOB_POSTINGS_SCHEMA.validate(typed)


def test_schema_rejects_a_missing_column() -> None:
    with pytest.raises(pa.errors.SchemaErrors):
        RAW_JOB_POSTINGS_SCHEMA.validate(make_typed().drop(columns="job_title"), lazy=True)


def test_schema_rejects_an_extra_column() -> None:
    with pytest.raises(pa.errors.SchemaErrors):
        RAW_JOB_POSTINGS_SCHEMA.validate(make_typed().assign(extra="x"), lazy=True)


def test_schema_rejects_columns_in_a_different_order() -> None:
    reversed_columns = list(reversed(make_typed().columns))

    with pytest.raises(pa.errors.SchemaErrors):
        RAW_JOB_POSTINGS_SCHEMA.validate(make_typed()[reversed_columns], lazy=True)


def test_schema_rejects_a_column_with_another_type() -> None:
    typed = make_typed()
    typed["job_work_from_home"] = typed["job_work_from_home"].astype(object)

    with pytest.raises(pa.errors.SchemaErrors):
        RAW_JOB_POSTINGS_SCHEMA.validate(typed, lazy=True)


def test_schema_requires_a_row_hash_of_64_characters() -> None:
    typed = make_typed()
    typed["row_hash"] = pd.array(["short"], dtype="string")

    with pytest.raises(pa.errors.SchemaErrors):
        RAW_JOB_POSTINGS_SCHEMA.validate(typed, lazy=True)
