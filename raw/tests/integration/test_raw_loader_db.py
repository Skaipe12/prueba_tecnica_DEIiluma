"""Integration tests for RawLoader against a running PostgreSQL."""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

from raw.src.config.constants import CSV_COLUMNS
from raw.src.config.postgres_connection import PostgresConnection
from raw.src.queries.queries import PipelineQueries
from raw.src.resources.data_factory import DataFactory
from raw.src.resources.raw_loader import RawLoader
from raw.src.resources.schema_manager import SchemaManager
from raw.src.resources.schemas.schema import RAW_JOB_POSTINGS_SCHEMA
from raw.src.resources.validator import Validator

pytestmark = pytest.mark.integration

PANDERA_TO_POSTGRES = {
    "string[python]": {"text", "character"},
    "boolean": {"boolean"},
    "datetime64[ns]": {"timestamp without time zone"},
}
OBJECT_COLUMNS_TO_POSTGRES = {
    "salary_year_avg": "numeric",
    "salary_hour_avg": "numeric",
    "job_skills": "ARRAY",
    "job_type_skills": "jsonb",
}


def make_row(**overrides: str) -> dict[str, str]:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        job_title="Data Analyst",
        job_posted_date="2023-01-14 13:18:07",
        job_work_from_home="True",
    )
    row.update(overrides)
    return row


def make_valid(rows: list[dict[str, str]]) -> pd.DataFrame:
    chunk = pd.DataFrame(rows, columns=list(CSV_COLUMNS), dtype=str)
    valid, _ = Validator.split_valid_invalid(DataFactory.to_typed(chunk))
    return valid


def count_rows(connection: PostgresConnection) -> int:
    return connection.execute("SELECT count(*) FROM raw.job_postings")[0][0]


@pytest.fixture
def connection(test_connection: PostgresConnection) -> PostgresConnection:
    SchemaManager(test_connection, PipelineQueries()).create_schema()
    return test_connection


@pytest.fixture
def loader() -> RawLoader:
    return RawLoader(PipelineQueries())


def test_raw_table_columns_match_the_schema(connection: PostgresConnection) -> None:
    rows = connection.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND table_name = 'job_postings' ORDER BY ordinal_position"
    )
    table = [(name, data_type) for name, data_type in rows if name not in ("raw_id", "loaded_at")]

    schema_columns = RAW_JOB_POSTINGS_SCHEMA.columns
    assert [name for name, _ in table] == list(schema_columns)
    for name, data_type in table:
        dtype = str(schema_columns[name].dtype)
        if dtype == "object":
            assert data_type == OBJECT_COLUMNS_TO_POSTGRES[name], name
        else:
            assert data_type in PANDERA_TO_POSTGRES[dtype], name


def test_load_returns_the_number_of_rows(connection: PostgresConnection, loader: RawLoader) -> None:
    valid = make_valid([make_row(), make_row(job_title="Data Engineer")])

    with connection.connect() as conn:
        loaded = loader.load(conn, valid)

    assert loaded == 2
    assert count_rows(connection) == 2


def test_load_round_trips_every_column_type(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    valid = make_valid(
        [
            make_row(
                salary_year_avg="157500.0",
                job_skills="['sql', 'python']",
                job_type_skills="{'programming': ['sql', 'python']}",
            )
        ]
    )

    with connection.connect() as conn:
        loader.load(conn, valid)

    (row,) = connection.execute(
        "SELECT job_title, job_work_from_home, job_posted_date, salary_year_avg, "
        "job_skills, job_type_skills, row_hash FROM raw.job_postings"
    )
    assert row[0] == "Data Analyst"
    assert row[1] is True
    assert row[2] == datetime(2023, 1, 14, 13, 18, 7)
    assert row[3] == Decimal("157500.0")
    assert row[4] == ["sql", "python"]
    assert row[5] == {"programming": ["sql", "python"]}
    assert row[6] == valid.iloc[0]["row_hash"]


def test_load_stores_empty_values_as_null(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    valid = make_valid([make_row(job_title="", job_work_from_home="")])

    with connection.connect() as conn:
        loader.load(conn, valid)

    (row,) = connection.execute(
        "SELECT job_title, job_work_from_home, salary_hour_avg, job_skills, job_type_skills "
        "FROM raw.job_postings"
    )
    assert row == (None, None, None, None, None)


def test_load_keeps_the_source_values_untouched(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    valid = make_valid(
        [
            make_row(
                job_title="PRINCIPAL  ENGINEER",
                company_name="smart folks inc",
                job_via="via BeBee MÃ©xico",
                job_skills="['SQL', 'sql', 'SQL']",
            )
        ]
    )

    with connection.connect() as conn:
        loader.load(conn, valid)

    (row,) = connection.execute(
        "SELECT job_title, company_name, job_via, job_skills FROM raw.job_postings"
    )
    assert row == (
        "PRINCIPAL  ENGINEER",
        "smart folks inc",
        "via BeBee MÃ©xico",
        ["SQL", "sql", "SQL"],
    )


def test_load_keeps_duplicate_rows(connection: PostgresConnection, loader: RawLoader) -> None:
    valid = make_valid([make_row(), make_row()])

    with connection.connect() as conn:
        loader.load(conn, valid)

    hashes = connection.execute("SELECT row_hash FROM raw.job_postings")
    assert len(hashes) == 2
    assert hashes[0] == hashes[1]


def test_load_can_be_called_once_per_chunk(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    first = make_valid([make_row(job_title="A")])
    second = make_valid([make_row(job_title="B")])

    with connection.connect() as conn:
        loader.load(conn, first)
        loader.load(conn, second)

    titles = connection.execute("SELECT job_title FROM raw.job_postings ORDER BY raw_id")
    assert titles == [("A",), ("B",)]


def test_truncate_empties_the_table_and_restarts_the_identity(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    with connection.connect() as conn:
        loader.load(conn, make_valid([make_row(), make_row()]))
    with connection.connect() as conn:
        loader.truncate(conn)
        loader.load(conn, make_valid([make_row()]))

    assert connection.execute("SELECT raw_id FROM raw.job_postings") == [(1,)]


def test_load_is_rolled_back_when_the_transaction_fails(
    connection: PostgresConnection, loader: RawLoader
) -> None:
    with pytest.raises(RuntimeError), connection.connect() as conn:
        loader.load(conn, make_valid([make_row()]))
        raise RuntimeError("boom")

    assert count_rows(connection) == 0
