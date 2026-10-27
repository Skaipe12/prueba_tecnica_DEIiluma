from raw.src.config.constants import (BOOL_COLUMNS,
                                  CSV_COLUMNS,
                                  CSV_TIMESTAMP_FORMAT,
                                  DECIMAL_COLUMNS,
                                  ROW_HASH_SEPARATOR,
                                  TEXT_COLUMNS)
from decimal import Decimal, InvalidOperation
from collections.abc import Callable, Mapping
from datetime import datetime
import pandas as pd
import hashlib
import ast


class DataFactory:
    """Converts raw CSV chunks to typed DataFrames without changing any value."""

    @staticmethod
    def empty_to_none(value: str | None) -> str | None:
        """Returns None for an empty string and any other value unchanged."""
        return None if value is None or value == "" else value

    @staticmethod
    def parse_bool(value: str | None) -> bool | None:
        """Converts "True" or "False" to a bool, empty to None and anything else raises."""
        if value is None or value == "":
            return None
        if value == "True":
            return True
        if value == "False":
            return False
        raise ValueError(f"Invalid boolean: {value!r}")

    @staticmethod
    def parse_timestamp(value: str | None) -> datetime | None:
        """Converts a timestamp in CSV_TIMESTAMP_FORMAT, empty to None and anything else raises."""
        if value is None or value == "":
            return None
        return datetime.strptime(value, CSV_TIMESTAMP_FORMAT)

    @staticmethod
    def parse_decimal(value: str | None) -> Decimal | None:
        """Converts a finite number to a Decimal, empty to None and anything else raises."""
        if value is None or value == "":
            return None
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(f"Invalid decimal: {value!r}") from error
        if not number.is_finite():
            raise ValueError(f"Invalid decimal: {value!r}")
        return number

    @staticmethod
    def parse_skill_list(raw: str | None) -> list[str] | None:
        """Converts a Python list literal of strings keeping order and duplicates, empty to None."""
        if raw is None or raw == "":
            return None
        try:
            parsed = ast.literal_eval(raw)
        except SyntaxError as error:
            raise ValueError(f"Invalid skill list: {raw!r}") from error
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise ValueError(f"Invalid skill list: {raw!r}")
        return parsed

    @staticmethod
    def parse_skill_types(raw: str | None) -> dict[str, list[str]] | None:
        """Converts a Python dict literal of skill types to lists of strings, empty to None."""
        if raw is None or raw == "":
            return None
        try:
            parsed = ast.literal_eval(raw)
        except SyntaxError as error:
            raise ValueError(f"Invalid skill types: {raw!r}") from error
        if not isinstance(parsed, dict) or not all(
            isinstance(key, str)
            and isinstance(items, list)
            and all(isinstance(item, str) for item in items)
            for key, items in parsed.items()
        ):
            raise ValueError(f"Invalid skill types: {raw!r}")
        return parsed

    @staticmethod
    def compute_row_hash(row: Mapping[str, str]) -> str:
        """Returns the sha256 hex digest of the original text values of a CSV row."""
        joined = ROW_HASH_SEPARATOR.join(row[column] for column in CSV_COLUMNS)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    @classmethod
    def column_parsers(cls) -> dict[str, Callable]:
        """Returns the parser that converts each CSV column."""
        return {
            **dict.fromkeys(TEXT_COLUMNS, cls.empty_to_none),
            **dict.fromkeys(BOOL_COLUMNS, cls.parse_bool),
            **dict.fromkeys(DECIMAL_COLUMNS, cls.parse_decimal),
            "job_posted_date": cls.parse_timestamp,
            "job_skills": cls.parse_skill_list,
            "job_type_skills": cls.parse_skill_types,
        }

    @staticmethod
    def convert_column(values: pd.Series, parser: Callable) -> tuple[list, list[int]]:
        """Applies a parser to a column and returns the values and the positions that failed."""
        converted = []
        failed = []
        for position, value in enumerate(values):
            try:
                converted.append(parser(value))
            except ValueError:
                converted.append(None)
                failed.append(position)
        return converted, failed

    @classmethod
    def to_typed(cls, chunk: pd.DataFrame) -> pd.DataFrame:
        """Converts a raw chunk to typed columns without changing any value."""
        parsers = cls.column_parsers()
        errors = [[] for _ in range(len(chunk))]
        data = {}
        for column in CSV_COLUMNS:
            data[column], failed = cls.convert_column(chunk[column], parsers[column])
            for position in failed:
                errors[position].append(column)
        # row_hash uses the raw text, so it is computed from the chunk and not from data
        data["row_hash"] = [cls.compute_row_hash(row) for row in chunk.to_dict("records")]
        data["parse_errors"] = [",".join(columns) or None for columns in errors]
        dtypes = {
            **dict.fromkeys(TEXT_COLUMNS, "string"),
            **dict.fromkeys(BOOL_COLUMNS, "boolean"),
            "job_posted_date": "datetime64[us]",
            "row_hash": "string",
            "parse_errors": "string",
        }
        return pd.DataFrame(data, index=chunk.index, dtype=object).astype(dtypes)
