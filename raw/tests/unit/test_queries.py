"""Tests for PipelineQueries."""

from pathlib import Path

from raw.src.queries.queries import PipelineQueries


def write_sql(sql_dir: Path, name: str, text: str) -> None:
    path = sql_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_read_sql_returns_the_text_of_the_file(tmp_path: Path) -> None:
    write_sql(tmp_path, "some.sql", "SELECT 1;\n")

    assert PipelineQueries(sql_dir=tmp_path).read_sql("some.sql") == "SELECT 1;\n"


def test_read_sql_accepts_a_path_inside_a_subfolder(tmp_path: Path) -> None:
    write_sql(tmp_path, "raw/some.sql", "SELECT 2;")

    assert PipelineQueries(sql_dir=tmp_path).read_sql("raw/some.sql") == "SELECT 2;"


def test_each_query_reads_its_own_file(tmp_path: Path) -> None:
    files = {
        "schema.sql": "create",
        "drop_schemas.sql": "drop",
        "raw/truncate_job_postings.sql": "truncate",
        "raw/copy_job_postings.sql": "copy",
    }
    for name, text in files.items():
        write_sql(tmp_path, name, text)

    queries = PipelineQueries(sql_dir=tmp_path)

    assert queries.create_schema() == "create"
    assert queries.drop_schemas() == "drop"
    assert queries.truncate_job_postings() == "truncate"
    assert queries.copy_job_postings() == "copy"


def test_the_project_sql_files_exist_and_are_not_empty() -> None:
    queries = PipelineQueries()

    assert "CREATE SCHEMA IF NOT EXISTS raw" in queries.create_schema()
    assert "DROP SCHEMA IF EXISTS core" in queries.drop_schemas()
    assert "TRUNCATE TABLE raw.job_postings" in queries.truncate_job_postings()
    assert "COPY raw.job_postings" in queries.copy_job_postings()
