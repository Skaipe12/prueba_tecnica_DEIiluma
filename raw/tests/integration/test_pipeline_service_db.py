"""Integration tests for the raw PipelineService against a running PostgreSQL."""

from pathlib import Path

import pandas as pd
import pytest

from raw.src.config.postgres_connection import PostgresConnection
from raw.src.queries.queries import PipelineQueries
from raw.src.resources.csv_reader import CsvReader
from raw.src.resources.raw_loader import RawLoader
from raw.src.resources.schema_manager import SchemaManager
from raw.src.services.pipeline_service import PipelineService

pytestmark = pytest.mark.integration

SAMPLE_CSV = Path(__file__).resolve().parents[1] / "fixtures" / "sample_jobs.csv"


@pytest.fixture
def csv_with_one_bad_row(tmp_path: Path) -> Path:
    """The sample CSV where the first row has an invalid boolean: 1 of 23 rows is rejected."""
    df = pd.read_csv(SAMPLE_CSV, dtype=str, na_filter=False)
    df.loc[0, "job_work_from_home"] = "maybe"
    path = tmp_path / "bad_row.csv"
    df.to_csv(path, index=False)
    return path


def make_service(
    connection: PostgresConnection, path: Path, max_reject_ratio: float
) -> PipelineService:
    queries = PipelineQueries()
    return PipelineService(
        connection,
        SchemaManager(connection, queries),
        CsvReader(path, chunk_size=5),
        RawLoader(queries),
        max_reject_ratio,
    )


def count_raw(connection: PostgresConnection) -> int:
    return connection.execute("SELECT count(*) FROM raw.job_postings")[0][0]


def test_run_loads_the_valid_rows_and_a_second_run_replaces_them(
    test_connection: PostgresConnection, csv_with_one_bad_row: Path
) -> None:
    service = make_service(test_connection, csv_with_one_bad_row, max_reject_ratio=0.10)
    service.setup()

    service.run()
    first = count_raw(test_connection)
    service.run()

    assert first == 22
    assert count_raw(test_connection) == first


def test_run_rolls_back_and_keeps_the_old_content_when_too_many_rows_are_rejected(
    test_connection: PostgresConnection, csv_with_one_bad_row: Path
) -> None:
    tolerant = make_service(test_connection, csv_with_one_bad_row, max_reject_ratio=0.10)
    tolerant.setup()
    tolerant.run()

    with pytest.raises(ValueError, match="Too many rejected rows"):
        make_service(test_connection, csv_with_one_bad_row, max_reject_ratio=0.01).run()

    assert count_raw(test_connection) == 22
