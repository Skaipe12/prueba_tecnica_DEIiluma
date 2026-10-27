from src.config.constants import CSV_COLUMNS, CSV_ENCODING, MAX_REJECT_RATIO
from src.resources.schemas.schema import RAW_JOB_POSTINGS_SCHEMA
from pathlib import Path
import pandera.pandas as pa
import pandas as pd


class Validator:
    """Validates the input file and the typed DataFrames before they are loaded."""

    @staticmethod
    def validate_file(path: Path) -> None:
        """Raises FileNotFoundError if the path is not an existing file."""
        if not path.is_file():
            raise FileNotFoundError(f"CSV file not found: {path}")

    @classmethod
    def validate_header(cls, path: Path) -> None:
        """Raises ValueError if the CSV header differs from the expected columns."""
        cls.validate_file(path)
        header = tuple(pd.read_csv(path, nrows=0, encoding=CSV_ENCODING).columns)
        if header != CSV_COLUMNS:
            missing = [column for column in CSV_COLUMNS if column not in header]
            unexpected = [column for column in header if column not in CSV_COLUMNS]
            raise ValueError(
                f"Unexpected CSV header: missing={missing}, unexpected={unexpected}, "
                f"expected order={list(CSV_COLUMNS)}"
            )

    @staticmethod
    def split_valid_invalid(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Splits a typed DataFrame into the rows ready to load and the rejected rows.

        A row is rejected when DataFactory could not convert one of its values. Rejected rows
        keep every column and get an errors column; valid rows lose parse_errors.
        """
        has_errors = df["parse_errors"].notna()
        valid = df[~has_errors].drop(columns="parse_errors")
        rejected = df[has_errors].rename(columns={"parse_errors": "errors"})
        return valid, rejected

    @staticmethod
    def validate_schema(df: pd.DataFrame) -> None:
        """Raises ValueError if the DataFrame does not match the raw table schema."""
        try:
            RAW_JOB_POSTINGS_SCHEMA.validate(df, lazy=True)
        except pa.errors.SchemaErrors as error:
            failures = error.failure_cases[["column", "check", "failure_case"]]
            message = f"DataFrame does not match the raw table schema:\n{failures}"
            raise ValueError(message) from error

    @staticmethod
    def validate_reject_ratio(rejected: int, total: int, max_ratio = MAX_REJECT_RATIO) -> None:
        """Raises ValueError if the share of rejected rows is above the allowed maximum."""
        if total > 0 and rejected / total > max_ratio:
            raise ValueError(
                f"Too many rejected rows: {rejected} of {total} ({rejected / total:.2%}), "
                f"the maximum is {max_ratio:.2%}"
            )
