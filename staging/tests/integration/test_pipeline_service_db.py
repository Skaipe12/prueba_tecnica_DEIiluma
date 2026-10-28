"""Integration tests for PipelineService: raw sample rows are turned into the core tables."""

from pathlib import Path

import pytest

from raw.src.queries.queries import PipelineQueries as RawQueries
from raw.src.resources.csv_reader import CsvReader
from raw.src.resources.data_factory import DataFactory as RawDataFactory
from raw.src.resources.raw_loader import RawLoader
from raw.src.resources.schema_manager import SchemaManager as RawSchemaManager
from raw.src.resources.validator import Validator as RawValidator
from staging.src.config.postgres_connection import PostgresConnection
from staging.src.queries.queries import PipelineQueries
from staging.src.resources.key_resolver import KeyResolver
from staging.src.resources.raw_reader import RawReader
from staging.src.resources.schema_manager import SchemaManager
from staging.src.resources.table_loader import TableLoader
from staging.src.services.pipeline_service import PipelineService

pytestmark = pytest.mark.integration

SAMPLE_CSV = Path(__file__).resolve().parents[3] / "raw" / "tests" / "fixtures" / "sample_jobs.csv"
CORE_TABLES = (
    "countries",
    "locations",
    "search_locations",
    "companies",
    "platforms",
    "schedule_types",
    "job_categories",
    "salary_rates",
    "skills",
    "skill_types",
    "skill_skill_types",
    "jobs",
    "job_skills",
    "job_schedule_types",
)


def load_sample_into_raw(connection: PostgresConnection) -> None:
    """Loads the sample CSV into raw."""
    RawSchemaManager(connection, RawQueries()).create_schema()
    loader = RawLoader(RawQueries())
    with connection.connect() as db:
        for chunk in CsvReader(SAMPLE_CSV).iter_chunks():
            valid, _ = RawValidator.split_valid_invalid(RawDataFactory.to_typed(chunk))
            loader.load(db, valid)


def make_service(connection: PostgresConnection) -> PipelineService:
    queries = PipelineQueries()
    return PipelineService(
        connection,
        SchemaManager(connection, queries),
        RawReader(connection, queries, chunk_size=5),
        KeyResolver(queries),
        TableLoader(queries),
    )


def count_rows(connection: PostgresConnection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT count(*) FROM core.{table}")[0][0]
        for table in CORE_TABLES
    }


@pytest.fixture
def service(test_connection: PostgresConnection) -> PipelineService:
    load_sample_into_raw(test_connection)
    service = make_service(test_connection)
    service.setup()
    service.run()
    return service


def test_run_builds_the_core_tables_from_raw(
    service: PipelineService, test_connection: PostgresConnection
) -> None:
    loadable = test_connection.execute(
        "SELECT count(DISTINCT row_hash) FROM raw.job_postings WHERE job_title IS NOT NULL "
        "AND NOT (salary_rate IS NOT NULL AND salary_year_avg IS NULL AND salary_hour_avg IS NULL)"
    )
    counts = count_rows(test_connection)

    assert counts["jobs"] == loadable[0][0]
    schedules = test_connection.execute("SELECT schedule_type_name FROM core.schedule_types")
    assert {row[0] for row in schedules} == {"Full-time", "Part-time", "Contractor", "Internship"}
    # the spellings of the same company share one row
    names = test_connection.execute(
        "SELECT company_name FROM core.companies WHERE company_name ILIKE 'philips'"
    )
    assert len(names) == 1
    # repeated skills in one job become one row
    assert test_connection.execute(
        "SELECT count(*) FROM core.job_skills s JOIN core.jobs j USING (job_id) "
        "WHERE j.job_title = 'Repeated Skills'"
    ) == [(2,)]


def test_run_twice_does_not_change_any_table(
    service: PipelineService, test_connection: PostgresConnection
) -> None:
    before = count_rows(test_connection)

    service.run()

    assert count_rows(test_connection) == before


def test_run_loads_only_the_rows_added_to_raw_later(
    service: PipelineService, test_connection: PostgresConnection
) -> None:
    before = count_rows(test_connection)
    with test_connection.connect() as db:
        db.execute(
            "INSERT INTO raw.job_postings (job_title, job_title_short, job_posted_date, "
            "job_work_from_home, job_no_degree_mention, job_health_insurance, job_skills, "
            "job_type_skills, row_hash) VALUES ('New Role', 'Data Analyst', now(), false, false, "
            "false, ARRAY['rust'], '{\"programming\": [\"rust\"]}', %s)",
            ("n" * 64,),
        )

    service.run()

    after = count_rows(test_connection)
    assert after["jobs"] == before["jobs"] + 1
    assert after["skills"] == before["skills"] + 1
    assert after["job_skills"] == before["job_skills"] + 1
    assert after["companies"] == before["companies"]
