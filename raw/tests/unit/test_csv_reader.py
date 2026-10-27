"""Tests for CsvReader."""

import csv
from pathlib import Path

from raw.src.config.constants import CSV_COLUMNS
from raw.src.resources.csv_reader import CsvReader


def make_row(**overrides: str) -> dict[str, str]:
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(job_title="Data Analyst", company_name="Acme")
    row.update(overrides)
    return row


def write_csv(tmp_path: Path, rows: list[dict[str, str]], encoding: str = "utf-8") -> Path:
    path = tmp_path / "jobs.csv"
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_iter_chunks_splits_rows_by_chunk_size(tmp_path: Path) -> None:
    path = write_csv(tmp_path, [make_row(job_title=f"Job {i}") for i in range(7)])

    chunks = list(CsvReader(path=path, chunk_size=3).iter_chunks())

    assert [len(chunk) for chunk in chunks] == [3, 3, 1]


def test_iter_chunks_keeps_every_row_in_order(tmp_path: Path) -> None:
    path = write_csv(tmp_path, [make_row(job_title=f"Job {i}") for i in range(5)])

    chunks = CsvReader(path=path, chunk_size=2).iter_chunks()

    titles = [title for chunk in chunks for title in chunk["job_title"]]
    assert titles == [f"Job {i}" for i in range(5)]


def test_iter_chunks_keeps_empty_values_as_empty_strings(tmp_path: Path) -> None:
    path = write_csv(tmp_path, [make_row(job_location="")])

    chunk = next(CsvReader(path=path).iter_chunks())

    assert chunk.loc[0, "job_location"] == ""
    assert chunk.loc[0, "salary_year_avg"] == ""


def test_iter_chunks_strips_the_utf8_bom(tmp_path: Path) -> None:
    path = write_csv(tmp_path, [make_row()], encoding="utf-8-sig")

    chunk = next(CsvReader(path=path).iter_chunks())

    assert list(chunk.columns) == list(CSV_COLUMNS)


def test_iter_chunks_reads_quoted_values_with_commas(tmp_path: Path) -> None:
    path = write_csv(tmp_path, [make_row(job_location="Guadalajara, Jalisco, Mexico")])

    chunk = next(CsvReader(path=path).iter_chunks())

    assert chunk.loc[0, "job_location"] == "Guadalajara, Jalisco, Mexico"


def test_iter_chunks_does_not_alter_text_values(tmp_path: Path) -> None:
    row = make_row(job_title="PRINCIPAL  ENGINEER", company_name="  smart inc ")
    path = write_csv(tmp_path, [row])

    chunk = next(CsvReader(path=path).iter_chunks())

    assert chunk.loc[0, "job_title"] == "PRINCIPAL  ENGINEER"
    assert chunk.loc[0, "company_name"] == "  smart inc "
