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
