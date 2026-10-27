from raw.src.config.postgres_connection import PostgresConnection
from raw.src.queries.queries import PipelineQueries


class SchemaManager:
    """Creates and drops the raw schema of the pipeline."""

    def __init__(self, connection: PostgresConnection, queries: PipelineQueries) -> None:
        self._connection = connection
        self._queries = queries

    def create_schema(self) -> None:
        """Creates the raw schema in one transaction, if they do not exist."""
        with self._connection.connect() as connection:
            connection.execute(self._queries.create_schema())

    def drop_schemas(self) -> None:
        """Drops the raw schema in one transaction."""
        with self._connection.connect() as connection:
            connection.execute(self._queries.drop_schemas())
