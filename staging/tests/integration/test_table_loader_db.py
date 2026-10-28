"""Integration tests for TableLoader against a running PostgreSQL."""

from datetime import datetime
from decimal import Decimal

import pandas as pd
import psycopg
import pytest

from staging.src.config.postgres_connection import PostgresConnection
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.schema_manager import SchemaManager
from staging.src.resources.table_loader import TableLoader

pytestmark = pytest.mark.integration


@pytest.fixture
def loader_and_connection(
    test_connection: PostgresConnection,
) -> tuple[TableLoader, PostgresConnection]:
    queries = PipelineQueries()
    SchemaManager(test_connection, queries).create_schema()
    return TableLoader(queries), test_connection


def test_load_writes_a_catalog_and_returns_the_number_of_rows(
    loader_and_connection: tuple[TableLoader, PostgresConnection],
) -> None:
    loader, connection = loader_and_connection
    df = pd.DataFrame({"skill_name": pd.array(["sql", "python"], dtype="string")})

    with connection.connect() as db:
        assert loader.load(db, "skills", df) == 2

    rows = connection.execute("SELECT skill_id, skill_name FROM core.skills ORDER BY skill_id")
    assert rows == [(1, "sql"), (2, "python")]


def test_load_writes_ids_nulls_dates_booleans_and_decimals_of_jobs(
    loader_and_connection: tuple[TableLoader, PostgresConnection],
) -> None:
    loader, connection = loader_and_connection
    with connection.connect() as db:
        loader.load(db, "job_categories", pd.DataFrame({"job_category_name": ["Data Analyst"]}))
        loader.load(
            db,
            "jobs",
            pd.DataFrame(
                {
                    "source_row_hash": pd.array(["h" * 64], dtype="string"),
                    "job_title": pd.array(["Analyst"], dtype="string"),
                    "job_category_id": pd.array([1], dtype="Int64"),
                    "company_id": pd.array([None], dtype="Int64"),
                    "job_location_id": pd.array([None], dtype="Int64"),
                    "search_location_id": pd.array([None], dtype="Int64"),
                    "platform_id": pd.array([None], dtype="Int64"),
                    "salary_rate_id": pd.array([None], dtype="Int64"),
                    "posted_at": pd.Series([pd.Timestamp("2023-06-16 13:44:15")]).astype(
                        "datetime64[us]"
                    ),
                    "work_from_home": pd.array([False], dtype="boolean"),
                    "no_degree_mention": pd.array([True], dtype="boolean"),
                    "health_insurance": pd.array([False], dtype="boolean"),
                    "salary_year_avg": pd.Series([Decimal("100.01")], dtype=object),
                    "salary_hour_avg": pd.Series([None], dtype=object),
                }
            ),
        )

    row = connection.execute(
        "SELECT job_category_id, company_id, posted_at, no_degree_mention, salary_year_avg, "
        "salary_hour_avg FROM core.jobs"
    )[0]
    assert row == (1, None, datetime(2023, 6, 16, 13, 44, 15), True, Decimal("100.01"), None)


def test_load_rolls_back_with_the_connection_when_a_constraint_fails(
    loader_and_connection: tuple[TableLoader, PostgresConnection],
) -> None:
    loader, connection = loader_and_connection
    df = pd.DataFrame({"skill_name": pd.array(["sql", "sql"], dtype="string")})

    with pytest.raises(psycopg.errors.UniqueViolation), connection.connect() as db:
        loader.load(db, "skills", df)

    assert connection.execute("SELECT count(*) FROM core.skills") == [(0,)]
