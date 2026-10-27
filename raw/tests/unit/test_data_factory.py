"""Tests for DataFactory."""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

from raw.src.config.constants import CSV_COLUMNS
from raw.src.resources.data_factory import DataFactory


def make_row(**overrides: str) -> dict[str, str]:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        job_title_short="Data Analyst",
        job_title="Data Analyst",
        job_posted_date="2023-01-14 13:18:07",
        job_work_from_home="False",
        job_no_degree_mention="False",
        job_health_insurance="False",
        company_name="Acme",
    )
    row.update(overrides)
    return row


def make_chunk(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=list(CSV_COLUMNS), dtype=str)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("", None), (None, None), ("x", "x"), (" ", " "), ("A  B", "A  B")],
)
def test_empty_to_none_only_changes_empty_values(value: str | None, expected: str | None) -> None:
    assert DataFactory.empty_to_none(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("True", True), ("False", False), ("", None), (None, None)],
)
def test_parse_bool_converts_valid_values(value: str | None, expected: bool | None) -> None:
    assert DataFactory.parse_bool(value) is expected


@pytest.mark.parametrize("value", ["true", "yes", "1", "TRUE"])
def test_parse_bool_rejects_other_values(value: str) -> None:
    with pytest.raises(ValueError):
        DataFactory.parse_bool(value)


def test_parse_timestamp_converts_the_csv_format() -> None:
    assert DataFactory.parse_timestamp("2023-06-16 13:44:15") == datetime(2023, 6, 16, 13, 44, 15)


@pytest.mark.parametrize("value", ["", None])
def test_parse_timestamp_returns_none_for_empty(value: str | None) -> None:
    assert DataFactory.parse_timestamp(value) is None


@pytest.mark.parametrize("value", ["2023-06-16", "16/06/2023", "garbage"])
def test_parse_timestamp_rejects_other_formats(value: str) -> None:
    with pytest.raises(ValueError):
        DataFactory.parse_timestamp(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("157500.0", Decimal("157500.0")), ("52.5", Decimal("52.5")), ("", None), (None, None)],
)
def test_parse_decimal_converts_valid_values(value: str | None, expected: Decimal | None) -> None:
    assert DataFactory.parse_decimal(value) == expected


@pytest.mark.parametrize("value", ["abc", "NaN", "Infinity", "-Infinity"])
def test_parse_decimal_rejects_non_finite_or_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        DataFactory.parse_decimal(value)


def test_parse_skill_list_keeps_order_duplicates_and_case() -> None:
    parsed = DataFactory.parse_skill_list("['SQL', 'sql', 'Python', 'SQL']")

    assert parsed == ["SQL", "sql", "Python", "SQL"]


@pytest.mark.parametrize(("raw", "expected"), [("", None), (None, None), ("[]", [])])
def test_parse_skill_list_handles_empty_values(raw: str | None, expected: list | None) -> None:
    assert DataFactory.parse_skill_list(raw) == expected


@pytest.mark.parametrize("raw", ["['sql'", "'sql'", "{'a': 1}", "[1, 2]", "not a list"])
def test_parse_skill_list_rejects_malformed_values(raw: str) -> None:
    with pytest.raises(ValueError):
        DataFactory.parse_skill_list(raw)


def test_parse_skill_types_keeps_keys_values_and_duplicates() -> None:
    raw = "{'cloud': ['aws', 'aws'], 'programming': ['SQL']}"

    assert DataFactory.parse_skill_types(raw) == {"cloud": ["aws", "aws"], "programming": ["SQL"]}


@pytest.mark.parametrize(("raw", "expected"), [("", None), (None, None), ("{}", {})])
def test_parse_skill_types_handles_empty_values(raw: str | None, expected: dict | None) -> None:
    assert DataFactory.parse_skill_types(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["['a']", "{'cloud': 'aws'}", "{'cloud': [1]}", "{1: ['a']}", "{'cloud'", "not a dict"],
)
def test_parse_skill_types_rejects_malformed_values(raw: str) -> None:
    with pytest.raises(ValueError):
        DataFactory.parse_skill_types(raw)


def test_compute_row_hash_is_a_sha256_hex_digest() -> None:
    assert len(DataFactory.compute_row_hash(make_row(job_title="Data Analyst"))) == 64


def test_compute_row_hash_is_deterministic_and_ignores_key_order() -> None:
    row = make_row(job_title="Data Analyst", company_name="Acme")
    reordered = dict(reversed(list(row.items())))

    assert DataFactory.compute_row_hash(row) == DataFactory.compute_row_hash(reordered)


def test_compute_row_hash_changes_with_any_value() -> None:
    base = make_row(job_title="Data Analyst")
    other = make_row(job_title="Data  Analyst")

    assert DataFactory.compute_row_hash(base) != DataFactory.compute_row_hash(other)


def test_column_parsers_cover_exactly_the_csv_columns() -> None:
    assert set(DataFactory.column_parsers()) == set(CSV_COLUMNS)


def test_convert_column_returns_values_and_failed_positions() -> None:
    values = pd.Series(["True", "yes", "", "False"])

    converted, failed = DataFactory.convert_column(values, DataFactory.parse_bool)

    assert converted == [True, None, None, False]
    assert failed == [1]


def test_to_typed_converts_every_column_type() -> None:
    chunk = make_chunk(
        [
            make_row(
                job_work_from_home="True",
                salary_year_avg="157500.0",
                job_skills="['sql', 'python']",
                job_type_skills="{'programming': ['sql', 'python']}",
            )
        ]
    )

    typed = DataFactory.to_typed(chunk)
    row = typed.iloc[0]

    assert typed["job_title"].dtype == "string"
    assert typed["job_work_from_home"].dtype == "boolean"
    assert typed["job_posted_date"].dtype == "datetime64[us]"
    assert row["job_work_from_home"]
    assert not row["job_no_degree_mention"]
    assert row["job_posted_date"] == pd.Timestamp(2023, 1, 14, 13, 18, 7)
    assert row["salary_year_avg"] == Decimal("157500.0")
    assert row["job_skills"] == ["sql", "python"]
    assert row["job_type_skills"] == {"programming": ["sql", "python"]}


def test_to_typed_turns_empty_values_into_nulls() -> None:
    typed = DataFactory.to_typed(make_chunk([make_row(job_location="", job_work_from_home="")]))
    row = typed.iloc[0]

    assert pd.isna(row["job_location"])
    assert pd.isna(row["job_work_from_home"])
    assert pd.isna(row["salary_hour_avg"])
    assert pd.isna(row["job_skills"])
    assert pd.isna(row["parse_errors"])


def test_to_typed_does_not_change_any_text_value() -> None:
    chunk = make_chunk(
        [
            make_row(
                job_title="PRINCIPAL ENGINEER -  DATA...",
                job_location="  Mexico ",
                job_via="via BeBee MÃ©xico",
                company_name="smart folks inc",
                job_skills="['SQL', 'sql', 'SQL']",
            )
        ]
    )

    typed = DataFactory.to_typed(chunk).iloc[0]

    assert typed["job_title"] == "PRINCIPAL ENGINEER -  DATA..."
    assert typed["job_location"] == "  Mexico "
    assert typed["job_via"] == "via BeBee MÃ©xico"
    assert typed["company_name"] == "smart folks inc"
    assert typed["job_skills"] == ["SQL", "sql", "SQL"]


def test_to_typed_flags_values_that_cannot_be_converted() -> None:
    chunk = make_chunk(
        [
            make_row(),
            make_row(job_work_from_home="yes", job_posted_date="not-a-date"),
            make_row(job_skills="['sql'"),
        ]
    )

    typed = DataFactory.to_typed(chunk)

    assert typed["parse_errors"].isna().tolist() == [True, False, False]
    assert typed.loc[1, "parse_errors"] == "job_work_from_home,job_posted_date"
    assert typed.loc[2, "parse_errors"] == "job_skills"
    assert pd.isna(typed.loc[1, "job_work_from_home"])
    assert pd.isna(typed.loc[1, "job_posted_date"])
    assert pd.isna(typed.loc[2, "job_skills"])


def test_to_typed_hashes_the_original_text_values() -> None:
    chunk = make_chunk([make_row(), make_row(), make_row(job_title="Data  Analyst")])

    hashes = list(DataFactory.to_typed(chunk)["row_hash"])

    assert hashes[0] == hashes[1]
    assert hashes[0] != hashes[2]
    assert all(len(value) == 64 for value in hashes)


def test_to_typed_keeps_the_chunk_index_and_row_order() -> None:
    chunk = make_chunk([make_row(job_title=f"Job {i}") for i in range(4)])
    chunk.index = [10, 11, 12, 13]

    typed = DataFactory.to_typed(chunk)

    assert list(typed.index) == [10, 11, 12, 13]
    assert list(typed["job_title"]) == [f"Job {i}" for i in range(4)]
