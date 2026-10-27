"""Integration tests for PostgresConnection against a running PostgreSQL."""

import pytest

from raw.src.config.postgres_connection import PostgresConnection

pytestmark = pytest.mark.integration


def test_execute_returns_rows() -> None:
    connection = PostgresConnection()

    assert connection.execute("SELECT 1") == [(1,)]


def test_execute_passes_parameters() -> None:
    connection = PostgresConnection()

    assert connection.execute("SELECT %s::int + 1", (41,)) == [(42,)]


def test_connect_rolls_back_on_error() -> None:
    connection = PostgresConnection()

    with pytest.raises(RuntimeError), connection.connect() as conn:
        conn.execute("CREATE TABLE rollback_probe (x int)")
        raise RuntimeError("boom")

    assert connection.execute("SELECT to_regclass('rollback_probe')") == [(None,)]


def test_connect_commits_on_clean_exit() -> None:
    connection = PostgresConnection()

    try:
        with connection.connect() as conn:
            conn.execute("CREATE TABLE commit_probe (x int)")

        assert connection.execute("SELECT to_regclass('commit_probe')") == [("commit_probe",)]
    finally:
        with connection.connect() as conn:
            conn.execute("DROP TABLE IF EXISTS commit_probe")
