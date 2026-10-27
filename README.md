# Data Jobs Pipeline

[![CI](https://github.com/Skaipe12/prueba_tecnica_DEIiluma/actions/workflows/ci.yml/badge.svg)](https://github.com/Skaipe12/prueba_tecnica_DEIiluma/actions/workflows/ci.yml)

ELT pipeline that loads ~786K job postings (`data_jobs.csv`) into PostgreSQL and models them in third normal form (3NF).

## Status

| Done | Pending |
|---|---|
| Project setup: uv, Docker Compose, pre-commit, GitHub Actions (lint + unit tests) | SQL transformations from `raw` to `core` (the 3NF tables exist but are empty) |
| Configuration (`.env`), logging, PostgreSQL connection | `Pipeline` class and command line entry point (`src/main.py`) |
| Extraction: chunked CSV reader and type conversion | Integration tests in CI |
| Validation with Pandera | ERD (`docs/erd.dbml`), OLAP design section |
| DDL for `raw` and `core` (`sql/schema.sql`) | |
| Load into `raw` with `COPY` (verified on the full file: 785,741 rows) | |

There is no end-to-end command yet. Until the `Pipeline` exists, the pieces are exercised by the test suite.

## How it works

```
data_jobs.csv
   │  CsvReader     reads the file in chunks of 10,000 rows (never the whole file)
   │  DataFactory   converts each text to its real type; no value is cleaned
   │  Validator     checks the DataFrame against the schema of the raw table
   │  RawLoader     writes with COPY
   ▼
raw.job_postings    faithful copy of the CSV, only typed (TEXT[] skills, JSONB skill types)
   │  SQL           cleaning and standardization (pending)
   ▼
core.*              3NF model: 14 tables with primary and foreign keys
```

```
src/config/      constants, .env reading, logging, PostgresConnection (psycopg 3)
src/queries/     PipelineQueries: the only class that reads the .sql files
src/resources/   CsvReader, DataFactory, Validator, SchemaManager, RawLoader, schemas/schema.py
sql/             schema.sql (raw + core DDL), raw/*.sql, drop_schemas.sql, transform/ (pending)
tests/           unit/ (no database) and integration/ (PostgreSQL)
```

## Setup

You need [uv](https://docs.astral.sh/uv/) (Python 3.12 is pinned in `.python-version`) and Docker.

```bash
uv sync                          # creates .venv with runtime + dev dependencies
cp .env.example .env             # then replace every xxxx
docker compose up -d             # PostgreSQL 16; wait until `docker compose ps` shows "healthy"
```

Put `data_jobs.csv` in `data/` (it is not versioned).

| Variable | Suggested local value |
|---|---|
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432`. If another PostgreSQL already uses it, set `5433`; Docker maps it to the container's 5432 |
| `POSTGRES_USER` | any user name, for example `jobs` |
| `POSTGRES_PASSWORD` | a password of your choice |
| `POSTGRES_DB` | any database name, for example `jobs` |

Database commands: `docker compose stop` (keep data), `docker compose down` (remove container, keep volume), `docker compose down -v` (delete the volume, full reset).

The schema is created by `SchemaManager.create_schema()` from `sql/schema.sql`, not by Docker, so the same flow works locally and in CI. The script is idempotent.

`requirements.txt` and `requirements-dev.txt` are exported from `uv.lock`. Regenerate them after changing dependencies:

```bash
uv export --format requirements-txt --no-dev --no-hashes --no-emit-project -o requirements.txt
uv export --format requirements-txt --only-dev --no-hashes --no-emit-project -o requirements-dev.txt
```

## Data model (3NF)

| Group | Tables |
|---|---|
| Centre | `jobs` |
| Catalogs | `companies`, `platforms`, `locations`, `search_locations`, `countries`, `job_categories`, `salary_rates`, `schedule_types`, `skills`, `skill_types` |
| Bridge tables | `job_skills`, `job_schedule_types`, `skill_skill_types` |

- **One-to-many:** each job points to one company, platform, location, search location, category and salary rate through foreign keys.
- **Many-to-many:** a job has several skills and a skill appears in many jobs. A bridge table with two foreign keys and a composite primary key resolves it, and the key prevents duplicate pairs. The same pattern is used for schedule types and for skills and skill types (`mongodb` is both a database and a programming skill).
- **Identifier:** the file has no job id, so `jobs.source_row_hash` stores a SHA-256 of the 17 original values. It identifies a posting across layers, removes exact duplicates and keeps the transformation idempotent.

## Design decisions

- **ELT with a faithful `raw` layer.** Python only converts types. Every change to a value (encoding repair, whitespace, case, duplicates, company names) is done later in SQL. A cleaning rule can then change without re-reading the 231 MB file.
- **The country belongs to `search_locations`, not to `jobs`.** On the full file, the country depends on the search location (0 of 173 have more than one) but not on the job location (1,167 of 17,218 do). Keeping it in `jobs` would be a transitive dependency.
- **`job_schedule_type` is split into atomic values.** `"Full-time and Part-time"` is a list written as text, which breaks first normal form. Six combinations also appear in two different orders.
- **Memory is bounded.** The file is read in chunks of 10,000 rows.
- **Business rules live in the database,** as `NOT NULL` and `CHECK` constraints of `core`, not in Python. The Pandera schema only describes the shape of the table that is written (same columns, order and types), and a test compares it with the real table.
- **SQL lives in `.sql` files,** read by a single class.

### What the load into `raw` changes and what it does not

| Changed (type conversion only) | Kept exactly as in the file |
|---|---|
| Empty text becomes `NULL` | Encoding errors (`MÃ©xico`), double spaces, upper and lower case |
| `"True"`/`"False"` become booleans | The `via ` prefix of platforms |
| Date text becomes `TIMESTAMP` (no time zone, the file has none) | Repeated skills inside a list and their order |
| Salaries become exact `NUMERIC` through `Decimal`, never `float` | The 101 duplicate rows |
| Skill list becomes `TEXT[]`, skill types become `JSONB` | Every row: nothing is dropped, filled or rounded |

Values are never interpreted while reading, so a company literally named `NA` is not turned into a missing value.

## Testing

```bash
uv run ruff check .                  # lint
uv run pytest -m "not integration"   # unit tests, no database needed
uv run pytest -m integration         # needs `docker compose up -d`
uv run pre-commit run --all-files    # same hooks that run on commit
```

Each integration test creates its own throwaway database and drops it at the end, so the tests never touch the data you loaded. CI runs the lint and the unit tests; adding PostgreSQL to CI for the integration tests is pending.

## Known limitations

- Rows that are identical in all 17 columns are treated as one job. Two real openings with exactly the same values cannot be told apart from a scraper duplicate.
- 402 rows have a `salary_rate` (`month`, `week`, `day`) but no salary amount in the source.
- `platforms` has about 7,900 variants (`BeBee`, `BeBee India`...) and they are not merged. Some company names look like people (possible recruiters).
- `core.fix_mojibake` repairs a text only when the whole value is valid UTF-8 read as LATIN1. Of 72 values containing `Ã` or `Â`, it repairs 27. The rest are legitimate letters (`SÃO PAULO`, `ROMÂNIA`) or truncated text and are left as they are.
- Titles cut with `...` in the source (about 2%) cannot be recovered.
- In `raw`, an empty value and a missing value are both `NULL`, and `JSONB` does not keep the key order of a dictionary.
