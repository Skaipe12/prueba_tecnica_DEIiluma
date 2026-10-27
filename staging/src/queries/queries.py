from staging.src.config.constants import SQL_DIR


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
