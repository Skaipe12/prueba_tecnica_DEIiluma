from staging.src.config.constants import (COMPANY_KEY_TRAILING,
                                          MOJIBAKE_MARKERS,
                                          SALARY_QUANTUM,
                                          SCHEDULE_ALIASES,
                                          SCHEDULE_SPLIT_PATTERN,
                                          VIA_PREFIX)
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import re


class DataFactory:
    """Cleans and standardizes the typed rows of raw with pandas, one rule per method."""

    @staticmethod
    def clean_text(value: str | None) -> str | None:
        """Trims the text, collapses repeated whitespace and turns an empty text into None."""
        if pd.isna(value):
            return None
        return " ".join(value.split()) or None

    @staticmethod
    def fix_mojibake(value: str | None) -> str | None:
        """Repairs UTF-8 text that was read as LATIN1, leaving it unchanged if it cannot be."""
        if pd.isna(value) or not any(marker in value for marker in MOJIBAKE_MARKERS):
            return value
        try:
            return value.encode("latin-1").decode("utf-8")
        except UnicodeError:
            return value

    @staticmethod
    def strip_via(value: str | None) -> str | None:
        """Removes the "via " prefix of a platform name."""
        if pd.isna(value):
            return None
        return value.removeprefix(VIA_PREFIX) or None

    @staticmethod
    def company_key(name: str | None) -> str | None:
        """Returns the key that groups company spellings: lowercase, no final punctuation."""
        if pd.isna(name):
            return None
        return name.lower().rstrip(COMPANY_KEY_TRAILING) or None

    @staticmethod
    def split_schedule_types(value: str | None) -> list[str]:
        """Splits a schedule type into its atomic values, without repeats and with known aliases."""
        if pd.isna(value):
            return []
        parts = re.split(SCHEDULE_SPLIT_PATTERN, value)
        parts = (SCHEDULE_ALIASES.get(part, part) for part in parts)
        return list(dict.fromkeys(parts))

    @staticmethod
    def clean_skills(skills: list[str] | None) -> list[str]:
        """Lowercases and trims the skills, dropping empty and repeated ones, in order."""
        if skills is None:
            return []
        return list(dict.fromkeys(skill.strip().lower() for skill in skills if skill.strip()))

    @classmethod
    def skill_type_pairs(cls, skill_types: dict[str, list[str]] | None) -> list[tuple[str, str]]:
        """Returns the distinct (skill, skill type) pairs of the skill types dictionary."""
        if skill_types is None:
            return []
        pairs = (
            (skill, skill_type.strip().lower())
            for skill_type, skills in skill_types.items()
            for skill in cls.clean_skills(skills)
        )
        return list(dict.fromkeys(pairs))

    @staticmethod
    def round_salary(value: Decimal | None) -> Decimal | None:
        """Rounds a salary to 2 decimals, half up."""
        return None if pd.isna(value) else value.quantize(SALARY_QUANTUM, rounding=ROUND_HALF_UP)

    @classmethod
    def clean_text_column(cls, values: pd.Series, repair_mojibake: bool = False) -> pd.Series:
        """Applies clean_text to a column, and the mojibake repair before it if asked."""
        if repair_mojibake:
            values = values.map(cls.fix_mojibake)
        return values.map(cls.clean_text)

    @classmethod
    def clean_chunk(cls, chunk: pd.DataFrame) -> pd.DataFrame:
        """Applies every cleaning rule to a raw chunk and names the columns as in core."""
        company = cls.clean_text_column(chunk["company_name"], repair_mojibake=True)
        return pd.DataFrame(
            {
                "job_title_short": cls.clean_text_column(chunk["job_title_short"]),
                "job_title": cls.clean_text_column(chunk["job_title"], repair_mojibake=True),
                "job_location": cls.clean_text_column(chunk["job_location"]),
                "platform_name": cls.clean_text_column(chunk["job_via"]).map(cls.strip_via),
                "search_location": cls.clean_text_column(chunk["search_location"]),
                "country_name": cls.clean_text_column(chunk["job_country"]),
                "salary_rate": cls.clean_text_column(chunk["salary_rate"]),
                "company_name": company,
                "company_key": company.map(cls.company_key),
                "schedule_types": cls.clean_text_column(chunk["job_schedule_type"]).map(
                    cls.split_schedule_types
                ),
                "skills": chunk["job_skills"].map(cls.clean_skills),
                "skill_type_pairs": chunk["job_type_skills"].map(cls.skill_type_pairs),
                "posted_at": chunk["job_posted_date"],
                "work_from_home": chunk["job_work_from_home"],
                "no_degree_mention": chunk["job_no_degree_mention"],
                "health_insurance": chunk["job_health_insurance"],
                "salary_year_avg": chunk["salary_year_avg"].map(cls.round_salary),
                "salary_hour_avg": chunk["salary_hour_avg"].map(cls.round_salary),
                "row_hash": chunk["row_hash"],
            },
            index=chunk.index,
        )

    @staticmethod
    def distinct_frame(values: pd.Series, column: str) -> pd.DataFrame:
        """Returns a one-column frame with the distinct non-null values of a series."""
        distinct = values.dropna().drop_duplicates().reset_index(drop=True)
        return pd.DataFrame({column: distinct.astype("string")})

    @staticmethod
    def skill_pairs_frame(clean: pd.DataFrame) -> pd.DataFrame:
        """Returns the distinct (skill_name, skill_type_name) pairs of a cleaned chunk."""
        pairs = clean["skill_type_pairs"].explode().dropna().drop_duplicates()
        return pd.DataFrame(
            {
                "skill_name": pairs.map(lambda pair: pair[0]),
                "skill_type_name": pairs.map(lambda pair: pair[1]),
            },
            dtype="string",
        ).reset_index(drop=True)

    @classmethod
    def catalog_frames(cls, clean: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Returns the values of the catalogs that do not depend on another table."""
        pairs = cls.skill_pairs_frame(clean)
        skills = pd.concat([clean["skills"].explode(), pairs["skill_name"]])
        return {
            "countries": cls.distinct_frame(clean["country_name"], "country_name"),
            "locations": cls.distinct_frame(clean["job_location"], "location_name"),
            "platforms": cls.distinct_frame(clean["platform_name"], "platform_name"),
            "schedule_types": cls.distinct_frame(
                clean["schedule_types"].explode(), "schedule_type_name"
            ),
            "job_categories": cls.distinct_frame(clean["job_title_short"], "job_category_name"),
            "salary_rates": cls.distinct_frame(clean["salary_rate"], "salary_rate_name"),
            "skills": cls.distinct_frame(skills, "skill_name"),
            "skill_types": cls.distinct_frame(pairs["skill_type_name"], "skill_type_name"),
        }

    @staticmethod
    def companies_frame(clean: pd.DataFrame) -> pd.DataFrame:
        """Returns one row per company key, named with its most frequent spelling in the chunk."""
        companies = clean[["company_name", "company_key"]].dropna()
        names = companies.groupby("company_key")["company_name"].agg(lambda s: s.mode().iloc[0])
        return pd.DataFrame(
            {"company_name": names.to_numpy(), "company_name_key": names.index.to_numpy()},
            dtype="string",
        )

    @staticmethod
    def search_locations_frame(clean: pd.DataFrame, country_ids: dict[str, int]) -> pd.DataFrame:
        """Returns one row per search location with the id of its country."""
        locations = clean.dropna(subset=["search_location"]).drop_duplicates("search_location")
        return pd.DataFrame(
            {
                "search_location_name": locations["search_location"].astype("string"),
                "country_id": locations["country_name"].map(country_ids).astype("Int64"),
            }
        ).reset_index(drop=True)

    @staticmethod
    def skill_skill_types_frame(
        pairs: pd.DataFrame, skill_ids: dict[str, int], skill_type_ids: dict[str, int]
    ) -> pd.DataFrame:
        """Returns the skill and skill type ids of each pair."""
        return pd.DataFrame(
            {
                "skill_id": pairs["skill_name"].map(skill_ids).astype("Int64"),
                "skill_type_id": pairs["skill_type_name"].map(skill_type_ids).astype("Int64"),
            }
        )

    @staticmethod
    def jobs_frame(clean: pd.DataFrame, ids: dict[str, dict[str, int]]) -> pd.DataFrame:
        """Returns the rows of core.jobs, with the foreign keys looked up in the id maps."""

        def foreign_key(column: str, table: str) -> pd.Series:
            return clean[column].map(ids[table]).astype("Int64")

        return pd.DataFrame(
            {
                "source_row_hash": clean["row_hash"].astype("string"),
                "job_title": clean["job_title"].astype("string"),
                "job_category_id": foreign_key("job_title_short", "job_categories"),
                "company_id": foreign_key("company_key", "companies"),
                "job_location_id": foreign_key("job_location", "locations"),
                "search_location_id": foreign_key("search_location", "search_locations"),
                "platform_id": foreign_key("platform_name", "platforms"),
                "salary_rate_id": foreign_key("salary_rate", "salary_rates"),
                "posted_at": clean["posted_at"].astype("datetime64[us]"),
                "work_from_home": clean["work_from_home"].astype("boolean"),
                "no_degree_mention": clean["no_degree_mention"].astype("boolean"),
                "health_insurance": clean["health_insurance"].astype("boolean"),
                "salary_year_avg": clean["salary_year_avg"].astype(object),
                "salary_hour_avg": clean["salary_hour_avg"].astype(object),
            }
        ).reset_index(drop=True)

    @staticmethod
    def bridge_frame(
        clean: pd.DataFrame,
        column: str,
        job_ids: dict[str, int],
        ids: dict[str, int],
        id_column: str,
    ) -> pd.DataFrame:
        """Returns the (job_id, id) rows of a bridge table from a list column of the chunk."""
        exploded = clean.assign(job_id=clean["row_hash"].map(job_ids))[["job_id", column]]
        exploded = exploded.explode(column).dropna()
        frame = pd.DataFrame(
            {
                "job_id": exploded["job_id"].astype("Int64"),
                id_column: exploded[column].map(ids).astype("Int64"),
            }
        )
        return frame.drop_duplicates().reset_index(drop=True)
