# Data Jobs Pipeline

[![CI](https://github.com/Skaipe12/prueba_tecnica_DEIiluma/actions/workflows/ci.yml/badge.svg)](https://github.com/Skaipe12/prueba_tecnica_DEIiluma/actions/workflows/ci.yml)

ELT pipeline that loads job postings into PostgreSQL and models them in 3NF.

Work in progress.

## Setup (provisional)

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Python 3.12 is pinned in `.python-version`.

```bash
uv sync                # creates .venv and installs runtime + dev dependencies
uv run python --version
```

### Regenerating the requirements files

`requirements.txt` (runtime) and `requirements-dev.txt` (dev) are exported from `uv.lock`. Run these after changing dependencies with `uv add` / `uv remove`:

```bash
uv export --format requirements-txt --no-dev --no-hashes --no-emit-project -o requirements.txt
uv export --format requirements-txt --only-dev --no-hashes --no-emit-project -o requirements-dev.txt
```

Commit `uv.lock` together with the regenerated files.

## Database (PostgreSQL with Docker Compose)

Create your local `.env` from the template and replace every `xxxx`:

```bash
cp .env.example .env
```

| Variable | Suggested local value |
|---|---|
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` (see the note below if it is taken) |
| `POSTGRES_USER` | any user name, for example `jobs` |
| `POSTGRES_PASSWORD` | a password of your choice |
| `POSTGRES_DB` | any database name, for example `jobs` |

Commands (run from the repository root):

```bash
docker compose up -d        # start PostgreSQL 16 in the background
docker compose ps           # wait until the db service shows "healthy"
docker compose stop         # stop the container, keep the data
docker compose down         # stop and remove the container, keep the data volume
docker compose down -v      # stop and DELETE the data volume (full reset)
```

If port 5432 is already used by another PostgreSQL on your machine, set `POSTGRES_PORT=5433` in `.env`. Docker maps that port to the container's 5432.

The schema is not created by Docker. It is applied by the pipeline (`init-db`, planned), so the same flow works locally and in CI.
