"""Tests for the staging Validator."""

import pandas as pd
import pytest

from staging.src.resources.schemas.schema import CORE_SCHEMAS
from staging.src.resources.validator import Validator


def test_validate_table_accepts_a_valid_dataframe() -> None:
    df = pd.DataFrame({"skill_name": pd.array(["sql", "python"], dtype="string")})

    Validator.validate_table("skills", df)


@pytest.mark.parametrize(
    ("table", "data"),
    [
        ("skills", {"skill_name": ["sql", "sql"]}),
        ("skills", {"skill_name": ["sql", None]}),
        ("skills", {"other": ["sql"]}),
        ("job_skills", {"job_id": [1, 1], "skill_id": [2, 2]}),
    ],
)
def test_validate_table_rejects_duplicates_nulls_and_wrong_columns(table: str, data: dict) -> None:
    dtype = "string" if table == "skills" else "Int64"
    df = pd.DataFrame({column: pd.array(values, dtype=dtype) for column, values in data.items()})

    with pytest.raises(ValueError, match=f"core.{table}"):
        Validator.validate_table(table, df)


def test_there_is_one_schema_for_each_core_table() -> None:
    assert len(CORE_SCHEMAS) == 14
