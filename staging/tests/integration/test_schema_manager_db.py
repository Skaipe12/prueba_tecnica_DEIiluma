"""Integration tests for SchemaManager and the core DDL against a running PostgreSQL."""

import pytest

from staging.src.config.postgres_connection import PostgresConnection
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.schema_manager import SchemaManager

pytestmark = pytest.mark.integration

CORE_TABLES = {
    "countries",
    "locations",
    "search_locations",
    "companies",
    "platforms",
    "schedule_types",
    "job_categories",
    "salary_rates",
    "skills",
    "skill_types",
    "skill_skill_types",
    "jobs",
    "job_skills",
    "job_schedule_types",
}

CORE_FOREIGN_KEYS = {
    ("core.search_locations", "core.countries"),
    ("core.skill_skill_types", "core.skills"),
    ("core.skill_skill_types", "core.skill_types"),
    ("core.jobs", "core.job_categories"),
    ("core.jobs", "core.companies"),
    ("core.jobs", "core.locations"),
    ("core.jobs", "core.search_locations"),
    ("core.jobs", "core.platforms"),
    ("core.jobs", "core.salary_rates"),
    ("core.job_skills", "core.jobs"),
    ("core.job_skills", "core.skills"),
    ("core.job_schedule_types", "core.jobs"),
    ("core.job_schedule_types", "core.schedule_types"),
}


def make_manager(connection: PostgresConnection) -> SchemaManager:
    return SchemaManager(connection, PipelineQueries())


def list_tables(connection: PostgresConnection, schema: str) -> set[str]:
    rows = connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (schema,)
    )
    return {row[0] for row in rows}


def test_create_schema_creates_the_core_tables(test_connection: PostgresConnection) -> None:
    make_manager(test_connection).create_schema()

    assert list_tables(test_connection, "core") == CORE_TABLES


def test_create_schema_can_run_twice(test_connection: PostgresConnection) -> None:
    manager = make_manager(test_connection)

    manager.create_schema()
    manager.create_schema()

    assert list_tables(test_connection, "core") == CORE_TABLES


def test_drop_schemas_removes_core_and_allows_recreating(
    test_connection: PostgresConnection,
) -> None:
    manager = make_manager(test_connection)
    manager.create_schema()

    manager.drop_schemas()

    assert list_tables(test_connection, "core") == set()
    manager.create_schema()
    assert list_tables(test_connection, "core") == CORE_TABLES


def test_core_has_every_foreign_key_of_the_model(test_connection: PostgresConnection) -> None:
    make_manager(test_connection).create_schema()

    rows = test_connection.execute(
        "SELECT conrelid::regclass::text, confrelid::regclass::text FROM pg_constraint "
        "WHERE contype = 'f' AND connamespace = 'core'::regnamespace"
    )

    assert set(rows) == CORE_FOREIGN_KEYS
