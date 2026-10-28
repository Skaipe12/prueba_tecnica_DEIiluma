from raw.src.config.postgres_connection import PostgresConnection
from raw.src.resources.schema_manager import SchemaManager
from raw.src.resources.data_factory import DataFactory
from raw.src.config.constants import MAX_REJECT_RATIO
from raw.src.resources.csv_reader import CsvReader
from raw.src.resources.raw_loader import RawLoader
from raw.src.resources.validator import Validator
from raw.src.config.logger import get_logger

logger = get_logger(__name__)


class PipelineService:
    """Loads the jobs CSV into raw.job_postings in one transaction, one chunk at a time."""

    def __init__(
        self,
        connection: PostgresConnection,
        schema_manager: SchemaManager,
        reader: CsvReader,
        loader: RawLoader,
        max_reject_ratio = MAX_REJECT_RATIO,
    ) -> None:
        self._connection = connection
        self._schema_manager = schema_manager
        self._reader = reader
        self._loader = loader
        self._max_reject_ratio = max_reject_ratio

    def setup(self) -> None:
        """Checks the CSV header and creates the raw schema if it does not exist."""
        Validator.validate_header(self._reader.path)
        self._schema_manager.create_schema()
        logger.info("raw schema ready, CSV header is valid")

    def run(self) -> None:
        """Replaces the content of raw.job_postings; any error leaves the old content untouched."""
        read = loaded = rejected = 0
        with self._connection.connect() as connection:
            self._loader.truncate(connection)
            for number, chunk in enumerate(self._reader.iter_chunks(), start=1):
                valid, invalid = Validator.split_valid_invalid(DataFactory.to_typed(chunk))
                Validator.validate_schema(valid)
                loaded += self._loader.load(connection, valid)
                read += len(chunk)
                rejected += len(invalid)
                for errors, count in invalid["errors"].value_counts().items():
                    logger.warning("%d rows rejected, columns that failed: %s", count, errors)
                logger.info("chunk %d: %d rows read, %d loaded", number, len(chunk), len(valid))
            Validator.validate_reject_ratio(rejected, read, self._max_reject_ratio)
        logger.info("raw finished: %d rows read, %d loaded, %d rejected", read, loaded, rejected)
