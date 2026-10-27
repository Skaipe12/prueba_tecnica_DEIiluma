from pathlib import Path

LAYER_DIR: Path = Path(__file__).resolve().parents[2]
ROOT_DIR: Path = LAYER_DIR.parent
SQL_DIR: Path = LAYER_DIR / "sql"
LOG_FILE: Path = ROOT_DIR / "logs" / "staging.log"
LOG_MAX_BYTES: int = 5_242_880
LOG_BACKUP_COUNT: int = 3
CHUNK_SIZE: int = 10_000
CONNECT_TIMEOUT_S: int = 5
