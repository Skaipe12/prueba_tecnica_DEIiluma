# Data Jobs Pipeline

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
