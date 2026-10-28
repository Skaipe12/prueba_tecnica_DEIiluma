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
