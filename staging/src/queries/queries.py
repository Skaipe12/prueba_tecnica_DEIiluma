from staging.src.config.constants import CATALOG_KEYS, SQL_DIR
from collections.abc import Sequence
from psycopg import sql


class PipelineQueries:
    """Reads the SQL statements of the staging layer from the .sql files."""

    def __init__(self, sql_dir = SQL_DIR) -> None:
        self.sql_dir = sql_dir

    def read_sql(self, name: str) -> str:
        """Returns the text of a .sql file, given its path relative to the sql directory."""
        return (self.sql_dir / name).read_text(encoding="utf-8")

    def create_schema(self) -> str:
        """Creates the core schema with all its tables, if they do not exist."""
        return self.read_sql("schema.sql")

    def drop_schemas(self) -> str:
        """Drops the core schema with everything inside."""
        return self.read_sql("drop_schemas.sql")

    def select_job_postings(self) -> str:
        """Reads every row of raw.job_postings in the order they were loaded."""
        return self.read_sql("raw/select_job_postings.sql")

    def copy_table(self, table: str, columns: Sequence[str]) -> sql.Composed:
        """Copies rows from the client into the given columns of a core table."""
        return sql.SQL("COPY core.{} ({}) FROM STDIN").format(
            sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, columns))
        )

    def lookup_ids(self, table: str) -> sql.Composed:
        """Reads the key and the id of the rows of a core table whose key is in a list."""
        id_column, key_column = CATALOG_KEYS[table]
        return sql.SQL("SELECT {}, {} FROM core.{} WHERE {} = ANY(%s)").format(
            sql.Identifier(key_column),
            sql.Identifier(id_column),
            sql.Identifier(table),
            sql.Identifier(key_column),
        )

    def select_skill_skill_types(self) -> str:
        """Reads the skill and skill type ids of every row of core.skill_skill_types."""
        return self.read_sql("core/select_skill_skill_types.sql")
