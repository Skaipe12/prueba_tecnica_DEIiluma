from staging.src.config.constants import (REJECT_MISSING_VALUE,
                                          REJECT_RATE_WITHOUT_AMOUNT,
                                          REQUIRED_JOB_COLUMNS)
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

    @staticmethod
    def split_valid_invalid(clean: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Splits a cleaned chunk into the rows that can be loaded and the rejected rows.

        A row is rejected when it lacks a value that core.jobs requires, or when it has a salary
        rate but no amount. Rejected rows get a reason column.
        """
        missing = clean[list(REQUIRED_JOB_COLUMNS)].isna().any(axis=1)
        no_amount = (
            clean["salary_rate"].notna()
            & clean["salary_year_avg"].isna()
            & clean["salary_hour_avg"].isna()
        )
        reasons = pd.Series(None, index=clean.index, dtype=object)
        reasons[no_amount] = REJECT_RATE_WITHOUT_AMOUNT
        reasons[missing] = REJECT_MISSING_VALUE
        rejected_rows = missing | no_amount
        return clean[~rejected_rows], clean[rejected_rows].assign(reason=reasons[rejected_rows])
