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


def test_split_valid_invalid_rejects_missing_required_values_and_rate_without_amount() -> None:
    clean = pd.DataFrame(
        {
            "job_title": ["ok", None, "no amount", "rate and amount"],
            "job_title_short": ["a"] * 4,
            "posted_at": [pd.Timestamp("2023-01-01")] * 4,
            "work_from_home": [False] * 4,
            "no_degree_mention": [False] * 4,
            "health_insurance": [False] * 4,
            "salary_rate": [None, None, "year", "year"],
            "salary_year_avg": [None, None, None, 1],
            "salary_hour_avg": [None] * 4,
        }
    )

    valid, rejected = Validator.split_valid_invalid(clean)

    assert list(valid["job_title"]) == ["ok", "rate and amount"]
    assert dict(zip(rejected["job_title"].fillna("-"), rejected["reason"], strict=True)) == {
        "-": "missing_required_value",
        "no amount": "salary_rate_without_amount",
    }
