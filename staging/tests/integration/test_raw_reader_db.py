"""Integration tests for RawReader against a running PostgreSQL."""

from decimal import Decimal

import pytest

from raw.src.queries.queries import PipelineQueries as RawQueries
from staging.src.config.postgres_connection import PostgresConnection
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.raw_reader import RawReader

pytestmark = pytest.mark.integration

INSERT_ROW = (
    "INSERT INTO raw.job_postings (job_title, salary_year_avg, job_skills, job_type_skills, "
    "row_hash) VALUES (%s, %s, %s, %s::jsonb, %s)"
)


@pytest.fixture
def raw_connection(test_connection: PostgresConnection) -> PostgresConnection:
    with test_connection.connect() as connection:
        connection.execute(RawQueries().create_schema())
    return test_connection


def insert_rows(connection: PostgresConnection, count: int) -> None:
    with connection.connect() as db:
        for number in range(count):
            db.execute(
                INSERT_ROW,
                (f"title {number}", Decimal("100.5"), ["sql", "python"], '{"a": ["x"]}', "h" * 64),
            )


def test_iter_chunks_yields_chunks_of_the_given_size_in_load_order(
    raw_connection: PostgresConnection,
) -> None:
    insert_rows(raw_connection, 5)

    chunks = list(RawReader(raw_connection, PipelineQueries(), chunk_size=2).iter_chunks())

    assert [len(chunk) for chunk in chunks] == [2, 2, 1]
    titles = [title for chunk in chunks for title in chunk["job_title"]]
    assert titles == [f"title {number}" for number in range(5)]


def test_iter_chunks_returns_python_values_for_arrays_json_and_numbers(
    raw_connection: PostgresConnection,
) -> None:
    insert_rows(raw_connection, 1)

    chunk = next(RawReader(raw_connection, PipelineQueries()).iter_chunks())

    assert chunk.loc[0, "job_skills"] == ["sql", "python"]
    assert chunk.loc[0, "job_type_skills"] == {"a": ["x"]}
    assert chunk.loc[0, "salary_year_avg"] == Decimal("100.5")
    assert "loaded_at" not in chunk.columns


def test_iter_chunks_of_an_empty_table_yields_nothing(raw_connection: PostgresConnection) -> None:
    assert list(RawReader(raw_connection, PipelineQueries()).iter_chunks()) == []
