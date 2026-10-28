"""Tests for the staging DataFactory."""

from decimal import Decimal

import pandas as pd
import pytest

from staging.src.resources.data_factory import DataFactory


@pytest.mark.parametrize(
    ("value", "expected"),
    [(" Senior   Data  Engineer ", "Senior Data Engineer"), ("   ", None), (None, None)],
)
def test_clean_text_collapses_spaces_and_turns_empty_into_none(
    value: str | None, expected: str | None
) -> None:
    assert DataFactory.clean_text(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("MÃ©xico", "México"), ("SÃO PAULO", "SÃO PAULO"), ("Mexico", "Mexico"), (None, None)],
)
def test_fix_mojibake_repairs_only_what_can_be_repaired(
    value: str | None, expected: str | None
) -> None:
    assert DataFactory.fix_mojibake(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("via LinkedIn", "LinkedIn"), ("LinkedIn Jobs", "LinkedIn Jobs"), ("via BeBee", "BeBee")],
)
def test_strip_via_removes_only_the_prefix(value: str, expected: str) -> None:
    assert DataFactory.strip_via(value) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [("PHILIPS", "philips"), ("Miracle Systems, Inc.", "miracle systems, inc"), (None, None)],
)
def test_company_key_ignores_case_and_final_punctuation(
    name: str | None, expected: str | None
) -> None:
    assert DataFactory.company_key(name) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Full-time and Part-time", ["Full-time", "Part-time"]),
        ("Full-time, Part-time, and Internship", ["Full-time", "Part-time", "Internship"]),
        ("Kontraktor", ["Contractor"]),
        (None, []),
    ],
)
def test_split_schedule_types_returns_atomic_values(value: str | None, expected: list[str]) -> None:
    assert DataFactory.split_schedule_types(value) == expected


def test_clean_skills_and_skill_type_pairs_drop_repeats_and_normalize() -> None:
    assert DataFactory.clean_skills([" SQL", "sql", "Python", ""]) == ["sql", "python"]
    skill_types = {"programming": ["sql", "sql"], "Databases": ["Mongodb"]}
    assert DataFactory.skill_type_pairs(skill_types) == [
        ("sql", "programming"),
        ("mongodb", "databases"),
    ]


def test_round_salary_rounds_half_up_to_two_decimals() -> None:
    assert DataFactory.round_salary(Decimal("30.625000000000004")) == Decimal("30.63")
    assert DataFactory.round_salary(None) is None


def test_clean_chunk_applies_every_rule_and_renames_the_columns() -> None:
    chunk = pd.DataFrame(
        {
            "job_title_short": ["Data Analyst"],
            "job_title": ["Data  Engineer MÃ©xico"],
            "job_location": [None],
            "job_via": ["via LinkedIn"],
            "job_schedule_type": ["Full-time and Part-time"],
            "job_work_from_home": [False],
            "search_location": ["Mexico"],
            "job_posted_date": [pd.Timestamp("2023-06-16 13:44:15")],
            "job_no_degree_mention": [False],
            "job_health_insurance": [True],
            "job_country": ["Mexico"],
            "salary_rate": ["year"],
            "salary_year_avg": [Decimal("100.005")],
            "salary_hour_avg": [None],
            "company_name": ["Miracle Systems, Inc."],
            "job_skills": [["SQL", "sql"]],
            "job_type_skills": [{"programming": ["sql"]}],
            "row_hash": ["h" * 64],
        }
    )

    row = DataFactory.clean_chunk(chunk).iloc[0]

    assert row["job_title"] == "Data Engineer México"
    assert row["platform_name"] == "LinkedIn"
    assert row["company_key"] == "miracle systems, inc"
    assert row["schedule_types"] == ["Full-time", "Part-time"]
    assert row["skills"] == ["sql"]
    assert row["skill_type_pairs"] == [("sql", "programming")]
    assert row["salary_year_avg"] == Decimal("100.01")
    assert pd.isna(row["job_location"])
