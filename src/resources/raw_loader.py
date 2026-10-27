from src.config.constants import RAW_COPY_TYPES
from src.queries.queries import PipelineQueries
from psycopg.types.json import Jsonb
from collections.abc import Iterator
import psycopg
import pandas as pd


class RawLoader:
    """Loads typed DataFrames into raw.job_postings with COPY."""

    def __init__(self, queries: PipelineQueries) -> None:
        self._queries = queries

    def truncate(self, connection: psycopg.Connection) -> None:
        """Empties raw.job_postings so that the load replaces its content."""
        connection.execute(self._queries.truncate_job_postings())

    def to_rows(self, df: pd.DataFrame) -> Iterator[tuple]:
        """Yields each row as a tuple of Python values, with nulls as None and dicts as Jsonb."""
        values = df.astype(object).where(df.notna(), None)
        values["job_type_skills"] = values["job_type_skills"].map(
            lambda value: None if value is None else Jsonb(value)
        )
        yield from values.itertuples(index=False, name=None)

    def load(self, connection: psycopg.Connection, df: pd.DataFrame) -> int:
        """Copies a typed DataFrame into raw.job_postings and returns the number of rows."""
        statement = self._queries.copy_job_postings()
        with connection.cursor() as cursor, cursor.copy(statement) as copy:
            copy.set_types(RAW_COPY_TYPES)
            for row in self.to_rows(df):
                copy.write_row(row)
        return len(df)
