from staging.src.resources.schemas.schema import CORE_SCHEMAS
import pandera.pandas as pa
import pandas as pd


class Validator:
    """Validates the DataFrames of each core table before they are written."""

    @staticmethod
    def validate_table(table: str, df: pd.DataFrame) -> None:
        """Raises ValueError if the DataFrame does not match the schema of the core table."""
        try:
            CORE_SCHEMAS[table].validate(df, lazy=True)
        except pa.errors.SchemaErrors as error:
            failures = error.failure_cases[["column", "check", "failure_case"]]
            message = f"DataFrame does not match the schema of core.{table}:\n{failures}"
            raise ValueError(message) from error
