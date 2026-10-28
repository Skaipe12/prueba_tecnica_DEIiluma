from staging.src.config.postgres_connection import PostgresConnection
from staging.src.services.pipeline_service import PipelineService
from staging.src.resources.schema_manager import SchemaManager
from staging.src.resources.key_resolver import KeyResolver
from staging.src.resources.table_loader import TableLoader
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.raw_reader import RawReader


def build_pipeline() -> PipelineService:
    """Builds the PipelineService of the staging layer injecting all its dependencies."""
    connection = PostgresConnection()
    queries = PipelineQueries()
    return PipelineService(
        connection=connection,
        schema_manager=SchemaManager(connection, queries),
        reader=RawReader(connection, queries),
        resolver=KeyResolver(queries),
        loader=TableLoader(queries),
    )


if __name__ == "__main__":
    pipeline = build_pipeline()
    pipeline.setup()
    pipeline.run()
