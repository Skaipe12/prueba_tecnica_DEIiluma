"""Checks that each expected schema has the columns of its real core table."""

import pytest

from staging.src.config.postgres_connection import PostgresConnection
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.schema_manager import SchemaManager
from staging.src.resources.schemas.schema import CORE_SCHEMAS

pytestmark = pytest.mark.integration

COLUMNS_QUERY = (
    "SELECT table_name, column_name FROM information_schema.columns "
    "WHERE table_schema = 'core' AND is_identity = 'NO' ORDER BY table_name, ordinal_position"
)


def test_each_schema_has_the_columns_of_its_table_without_identity_keys(
    test_connection: PostgresConnection,
) -> None:
    SchemaManager(test_connection, PipelineQueries()).create_schema()

    columns: dict[str, list[str]] = {}
    for table, column in test_connection.execute(COLUMNS_QUERY):
        columns.setdefault(table, []).append(column)

    assert {table: list(schema.columns) for table, schema in CORE_SCHEMAS.items()} == columns
