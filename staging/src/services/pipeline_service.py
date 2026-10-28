from staging.src.resources.schema_manager import SchemaManager
from staging.src.config.postgres_connection import PostgresConnection
from staging.src.resources.data_factory import DataFactory
from staging.src.resources.key_resolver import KeyResolver
from staging.src.resources.table_loader import TableLoader
from staging.src.resources.validator import Validator
from staging.src.resources.raw_reader import RawReader
from staging.src.config.constants import CATALOG_KEYS
from staging.src.config.logger import get_logger
import psycopg
import pandas as pd

logger = get_logger(__name__)


class PipelineService:
    """Builds the core tables from raw one chunk at a time, loading only what is new."""

    def __init__(
        self,
        connection: PostgresConnection,
        schema_manager: SchemaManager,
        reader: RawReader,
        resolver: KeyResolver,
        loader: TableLoader,
    ) -> None:
        self._connection = connection
        self._schema_manager = schema_manager
        self._reader = reader
        self._resolver = resolver
        self._loader = loader

    def setup(self) -> None:
        """Creates the core schema and its tables if they do not exist."""
        self._schema_manager.create_schema()
        logger.info("core schema ready")

    def run(self) -> None:
        """Reads raw in chunks and loads each chunk in its own transaction."""
        read = loaded = 0
        for number, chunk in enumerate(self._reader.iter_chunks(), start=1):
            with self._connection.connect() as connection:
                new_jobs = self.load_chunk(connection, chunk)
            read += len(chunk)
            loaded += new_jobs
            logger.info("chunk %d: %d rows read, %d new jobs", number, len(chunk), new_jobs)
        logger.info("staging finished: %d rows read, %d new jobs", read, loaded)

    def load_chunk(self, connection: psycopg.Connection, chunk: pd.DataFrame) -> int:
        """Loads the jobs of a chunk that are not in core yet and returns how many were new."""
        clean = DataFactory.clean_chunk(chunk)
        known_jobs = self._resolver.lookup(connection, "jobs", clean["row_hash"])
        clean = clean[~clean["row_hash"].isin(known_jobs)].drop_duplicates("row_hash")
        if clean.empty:
            return 0

        ids = {
            table: self.sync_catalog(connection, table, frame)
            for table, frame in DataFactory.catalog_frames(clean).items()
        }
        companies = DataFactory.companies_frame(clean)
        ids["companies"] = self.sync_catalog(connection, "companies", companies)
        locations = DataFactory.search_locations_frame(clean, ids["countries"])
        ids["search_locations"] = self.sync_catalog(connection, "search_locations", locations)
        self.sync_skill_skill_types(connection, clean, ids["skills"], ids["skill_types"])

        jobs = DataFactory.jobs_frame(clean, ids)
        self.write(connection, "jobs", jobs)
        job_ids = self._resolver.lookup(connection, "jobs", jobs["source_row_hash"])
        job_skills = DataFactory.bridge_frame(clean, "skills", job_ids, ids["skills"], "skill_id")
        self.write(connection, "job_skills", job_skills)
        schedules = DataFactory.bridge_frame(
            clean, "schedule_types", job_ids, ids["schedule_types"], "schedule_type_id"
        )
        self.write(connection, "job_schedule_types", schedules)
        return len(jobs)

    def sync_catalog(
        self, connection: psycopg.Connection, table: str, frame: pd.DataFrame
    ) -> dict[str, int]:
        """Inserts the rows of a catalog that are new and returns the id of every key in frame."""
        key_column = CATALOG_KEYS[table][1]
        ids = self._resolver.lookup(connection, table, frame[key_column])
        new = frame[~frame[key_column].isin(ids)]
        if new.empty:
            return ids
        self.write(connection, table, new)
        return self._resolver.lookup(connection, table, frame[key_column])

    def sync_skill_skill_types(
        self,
        connection: psycopg.Connection,
        clean: pd.DataFrame,
        skill_ids: dict[str, int],
        skill_type_ids: dict[str, int],
    ) -> None:
        """Inserts the skill and skill type pairs of the chunk that are not in core yet."""
        pairs = DataFactory.skill_pairs_frame(clean)
        frame = DataFactory.skill_skill_types_frame(pairs, skill_ids, skill_type_ids)
        known = self._resolver.skill_skill_types(connection)
        is_new = [pair not in known for pair in frame.itertuples(index=False, name=None)]
        self.write(connection, "skill_skill_types", frame[is_new])

    def write(self, connection: psycopg.Connection, table: str, frame: pd.DataFrame) -> None:
        """Validates a frame against the schema of its table and copies it into the table."""
        if frame.empty:
            return
        Validator.validate_table(table, frame)
        self._loader.load(connection, table, frame)
