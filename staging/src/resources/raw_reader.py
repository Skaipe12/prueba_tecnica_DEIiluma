from staging.src.config.postgres_connection import PostgresConnection
from staging.src.config.constants import CHUNK_SIZE
from staging.src.queries.queries import PipelineQueries
from collections.abc import Iterator
import pandas as pd


class RawReader:
    """Reads raw.job_postings in chunks with a server-side cursor."""

    def __init__(
        self, connection: PostgresConnection, queries: PipelineQueries, chunk_size = CHUNK_SIZE
    ) -> None:
        self._connection = connection
        self._queries = queries
        self.chunk_size = chunk_size

    def iter_chunks(self) -> Iterator[pd.DataFrame]:
        """Yields the table in chunks with nulls as None, only one chunk in memory at a time."""
        with (
            self._connection.connect() as connection,
            connection.cursor(name="raw_job_postings") as cursor,
        ):
            cursor.execute(self._queries.select_job_postings())
            columns = [column.name for column in cursor.description]
            while rows := cursor.fetchmany(self.chunk_size):
                chunk = pd.DataFrame(rows, columns=columns).astype(object)
                yield chunk.where(chunk.notna(), None)
