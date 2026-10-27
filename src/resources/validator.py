from src.config.constants import CSV_COLUMNS, CSV_ENCODING
from pathlib import Path
import pandas as pd


class Validator:
    """Validates the input file before it is read."""

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
