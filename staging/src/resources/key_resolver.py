from staging.src.queries.queries import PipelineQueries
import psycopg
import pandas as pd


class KeyResolver:
    """Finds the ids that the database assigned to rows already loaded in the core tables."""

    def __init__(self, queries: PipelineQueries) -> None:
        self._queries = queries

    def lookup(self, connection: psycopg.Connection, table: str, keys: pd.Series) -> dict[str, int]:
        """Returns the id of each key of the list that exists in the table."""
        values = keys.dropna().astype(str).unique().tolist()
        if not values:
            return {}
        rows = connection.execute(self._queries.lookup_ids(table), (values,)).fetchall()
        return dict(rows)

    def skill_skill_types(self, connection: psycopg.Connection) -> set[tuple[int, int]]:
        """Returns the (skill id, skill type id) pairs already loaded."""
        rows = connection.execute(self._queries.select_skill_skill_types()).fetchall()
        return set(rows)
