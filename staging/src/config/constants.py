from decimal import Decimal
from pathlib import Path

LAYER_DIR: Path = Path(__file__).resolve().parents[2]
ROOT_DIR: Path = LAYER_DIR.parent
SQL_DIR: Path = LAYER_DIR / "sql"
LOG_FILE: Path = ROOT_DIR / "logs" / "staging.log"
LOG_MAX_BYTES: int = 5_242_880
LOG_BACKUP_COUNT: int = 3
CHUNK_SIZE: int = 10_000
CONNECT_TIMEOUT_S: int = 5
SALARY_QUANTUM: Decimal = Decimal("0.01")
MOJIBAKE_MARKERS: tuple[str, ...] = ("Ã", "Â")
VIA_PREFIX: str = "via "
COMPANY_KEY_TRAILING: str = " .,;"
SCHEDULE_SPLIT_PATTERN: str = r",\s*and\s+|,\s*|\s+and\s+"
SCHEDULE_ALIASES: dict[str, str] = {"Kontraktor": "Contractor"}

# Id column and natural key column of each core table that other tables point to.
CATALOG_KEYS: dict[str, tuple[str, str]] = {
    "countries": ("country_id", "country_name"),
    "locations": ("location_id", "location_name"),
    "search_locations": ("search_location_id", "search_location_name"),
    "companies": ("company_id", "company_name_key"),
    "platforms": ("platform_id", "platform_name"),
    "schedule_types": ("schedule_type_id", "schedule_type_name"),
    "job_categories": ("job_category_id", "job_category_name"),
    "salary_rates": ("salary_rate_id", "salary_rate_name"),
    "skills": ("skill_id", "skill_name"),
    "skill_types": ("skill_type_id", "skill_type_name"),
    "jobs": ("job_id", "source_row_hash"),
}
