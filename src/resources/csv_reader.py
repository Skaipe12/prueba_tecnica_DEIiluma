from src.config.constants import CHUNK_SIZE, CSV_ENCODING, CSV_PATH
from collections.abc import Iterator
import pandas as pd


class CsvReader:
    """Reads the jobs CSV in chunks of raw strings."""

    def __init__(self, path = CSV_PATH, chunk_size = CHUNK_SIZE) -> None:
        self.path = path
        self.chunk_size = chunk_size

    def iter_chunks(self) -> Iterator[pd.DataFrame]:
        """Yields the file in chunks of raw strings, keeping empty values as empty strings."""
        with pd.read_csv(
            self.path,
            dtype=str,
            na_filter=False,
            encoding=CSV_ENCODING,
            chunksize=self.chunk_size,
        ) as reader:
            yield from reader
