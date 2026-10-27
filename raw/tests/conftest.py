"""Shared fixtures."""

import uuid
from collections.abc import Iterator
from urllib.parse import urlsplit

import psycopg
import pytest

from raw.src.config.env import DATABASE_URL
from raw.src.config.postgres_connection import PostgresConnection


@pytest.fixture
def test_connection() -> Iterator[PostgresConnection]:
    """Creates a throwaway database for one integration test and drops it afterwards."""
    name = f"jobs_test_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=5) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    test_url = urlsplit(DATABASE_URL)._replace(path=f"/{name}").geturl()
    try:
        yield PostgresConnection(database_url=test_url)
    finally:
        with psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=5) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
