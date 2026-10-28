from raw.src.config.postgres_connection import PostgresConnection
from raw.src.services.pipeline_service import PipelineService
from raw.src.resources.schema_manager import SchemaManager
from raw.src.queries.queries import PipelineQueries
from raw.src.resources.csv_reader import CsvReader
from raw.src.resources.raw_loader import RawLoader


def build_pipeline() -> PipelineService:
    """Builds the PipelineService of the raw layer injecting all its dependencies."""
    connection = PostgresConnection()
    queries = PipelineQueries()
    return PipelineService(
        connection=connection,
        schema_manager=SchemaManager(connection, queries),
        reader=CsvReader(),
        loader=RawLoader(queries),
    )


if __name__ == "__main__":
    pipeline = build_pipeline()
    pipeline.setup()
    pipeline.run()
