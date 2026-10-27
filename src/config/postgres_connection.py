from src.config.constants import CONNECT_TIMEOUT_S
from src.config.env import DATABASE_URL
import psycopg


class PostgresConnection:
    """Opens PostgreSQL connections with psycopg 3 from a single database URL."""

    def __init__(self, database_url = DATABASE_URL, connect_timeout = CONNECT_TIMEOUT_S) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is not set: define the POSTGRES_* variables in .env")
        self.database_url = database_url
        self.connect_timeout = connect_timeout

    def connect(self) -> psycopg.Connection:
        """Opens a connection that commits on a clean exit and rolls back on an error."""
        return psycopg.connect(self.database_url, connect_timeout=self.connect_timeout)

    def execute(self, query, params = None) -> list[tuple]:
        """Runs a one-off read query on its own connection and returns every row."""
        with self.connect() as connection:
            return connection.execute(query, params).fetchall()
