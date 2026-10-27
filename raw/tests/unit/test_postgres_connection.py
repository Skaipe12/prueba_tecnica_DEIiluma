"""Tests for PostgresConnection without a database."""

import pytest

from raw.src.config.postgres_connection import PostgresConnection


@pytest.mark.parametrize("database_url", [None, ""])
def test_missing_database_url_raises(database_url: str | None) -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        PostgresConnection(database_url=database_url)


def test_constructor_keeps_url_and_timeout() -> None:
    connection = PostgresConnection(database_url="postgresql://u:p@h:1/d", connect_timeout=2)

    assert connection.database_url == "postgresql://u:p@h:1/d"
    assert connection.connect_timeout == 2
