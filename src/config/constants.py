from pathlib import Path

ROOT_DIR: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = ROOT_DIR / "data"
CSV_PATH: Path = DATA_DIR / "data_jobs.csv"
LOG_FILE: Path = ROOT_DIR / "logs" / "pipeline.log"
LOG_MAX_BYTES: int = 5_242_880
LOG_BACKUP_COUNT: int = 3
CHUNK_SIZE: int = 50_000
MAX_REJECT_RATIO: float = 0.01
CONNECT_TIMEOUT_S: int = 5
