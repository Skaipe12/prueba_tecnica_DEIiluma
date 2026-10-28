from staging.src.queries.queries import PipelineQueries
from collections.abc import Iterator
import psycopg
import pandas as pd


class TableLoader:
    """Writes DataFrames into the core tables with COPY."""

    def __init__(self, queries: PipelineQueries) -> None:
        self._queries = queries

    def to_rows(self, df: pd.DataFrame) -> Iterator[tuple]:
        """Yields each row as a tuple of Python values, with nulls as None."""
        values = df.astype(object).where(df.notna(), None)
        yield from values.itertuples(index=False, name=None)

    def load(self, connection: psycopg.Connection, table: str, df: pd.DataFrame) -> int:
        """Copies a DataFrame into a core table and returns the number of rows."""
        statement = self._queries.copy_table(table, list(df.columns))
        with connection.cursor() as cursor, cursor.copy(statement) as copy:
            for row in self.to_rows(df):
                copy.write_row(row)
        return len(df)
