from raw.src.config.constants import SQL_DIR


class PipelineQueries:
    """Reads the SQL statements of the pipeline from the .sql files."""

    def __init__(self, sql_dir = SQL_DIR) -> None:
        self.sql_dir = sql_dir

    def read_sql(self, name: str) -> str:
        """Returns the text of a .sql file, given its path relative to the sql directory."""
        return (self.sql_dir / name).read_text(encoding="utf-8")

    def create_schema(self) -> str:
        """Creates the raw schema with its table, if they do not exist."""
        return self.read_sql("schema.sql")

    def drop_schemas(self) -> str:
        """Drops the raw schema with everything inside."""
        return self.read_sql("drop_schemas.sql")

    def truncate_job_postings(self) -> str:
        """Empties raw.job_postings and restarts its identity."""
        return self.read_sql("raw/truncate_job_postings.sql")

    def copy_job_postings(self) -> str:
        """Copies rows from the client into raw.job_postings."""
        return self.read_sql("raw/copy_job_postings.sql")
