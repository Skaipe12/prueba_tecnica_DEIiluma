"""Integration tests for SchemaManager and the raw DDL against a running PostgreSQL."""

import pytest

from raw.src.config.postgres_connection import PostgresConnection
from raw.src.queries.queries import PipelineQueries
from raw.src.resources.schema_manager import SchemaManager

pytestmark = pytest.mark.integration

def make_manager(connection: PostgresConnection) -> SchemaManager:
    return SchemaManager(connection, PipelineQueries())


def list_tables(connection: PostgresConnection, schema: str) -> set[str]:
    rows = connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,)
    )
    return {row[0] for row in rows}


def test_create_schema_creates_the_raw_table(test_connection: PostgresConnection) -> None:
    make_manager(test_connection).create_schema()

    assert list_tables(test_connection, "raw") == {"job_postings"}


def test_create_schema_can_run_twice(test_connection: PostgresConnection) -> None:
    manager = make_manager(test_connection)

    manager.create_schema()
    manager.create_schema()

    assert list_tables(test_connection, "raw") == {"job_postings"}


def test_drop_schemas_removes_raw_and_allows_recreating(
    test_connection: PostgresConnection,
) -> None:
    manager = make_manager(test_connection)
    manager.create_schema()

    manager.drop_schemas()

    assert list_tables(test_connection, "raw") == set()
    manager.create_schema()
    assert list_tables(test_connection, "raw") == {"job_postings"}
