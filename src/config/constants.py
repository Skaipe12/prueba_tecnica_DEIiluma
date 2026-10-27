from pathlib import Path

ROOT_DIR: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = ROOT_DIR / "data"
CSV_PATH: Path = DATA_DIR / "data_jobs.csv"
LOG_FILE: Path = ROOT_DIR / "logs" / "pipeline.log"
LOG_MAX_BYTES: int = 5_242_880
LOG_BACKUP_COUNT: int = 3
CHUNK_SIZE: int = 10_000
MAX_REJECT_RATIO: float = 0.01
CONNECT_TIMEOUT_S: int = 5
CSV_ENCODING: str = "utf-8-sig"
CSV_TIMESTAMP_FORMAT: str = "%Y-%m-%d %H:%M:%S"
ROW_HASH_SEPARATOR: str = "\x1f"
CSV_COLUMNS: tuple[str, ...] = (
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "job_work_from_home",
    "search_location",
    "job_posted_date",
    "job_no_degree_mention",
    "job_health_insurance",
    "job_country",
    "salary_rate",
    "salary_year_avg",
    "salary_hour_avg",
    "company_name",
    "job_skills",
    "job_type_skills",
)
TEXT_COLUMNS: tuple[str, ...] = (
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "search_location",
    "job_country",
    "salary_rate",
    "company_name",
)
BOOL_COLUMNS: tuple[str, ...] = (
    "job_work_from_home",
    "job_no_degree_mention",
    "job_health_insurance",
)
DECIMAL_COLUMNS: tuple[str, ...] = ("salary_year_avg", "salary_hour_avg")
