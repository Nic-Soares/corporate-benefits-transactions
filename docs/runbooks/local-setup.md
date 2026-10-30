# Runbook — Local setup

From a fresh clone to a database with the schema created.

---

## 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) — `brew install uv` on macOS. It installs
  Python 3.14 (`.python-version`) when missing.
- Docker with Docker Compose (Docker Desktop, OrbStack, Colima…).

## 2. Dependencies

```bash
uv sync
```

Creates `.venv` from `uv.lock` and installs the project as a package, so
`from src…` imports work from anywhere.

## 3. Offline checks

```bash
uv run ruff check
uv run pytest
```

The default run needs neither network nor Docker. It loads every generated
table into the OLTP schema on an in-memory DuckDB, so a green run already
means config, generators and schema fit together.

## 4. Database

```bash
cp .env.example .env     # set DB_PASSWORD (DB_USER defaults to "benefits")
docker compose up -d
docker exec corporate_benefits_db pg_isready
```

Postgres 18 keeps its data in the `corporate_benefits_postgres_data` volume,
mounted at `/var/lib/postgresql` (18 stores data in a versioned subfolder).

```bash
uv run pytest -m db                                       # connection + schema
uv run python -m src.infrastructure.schema.schema_creator # create both schemas
```

The schema creator builds the 14 OLTP tables in Postgres and the DuckDB file
`database/olap_duck/olap_corporate_benefits.duckdb` (git-ignored).

## 5. Network sources (optional)

```bash
uv run pytest -m network
```

Calls the IBGE municipalities API. The CNAE dataset comes from Kaggle
(`src/extractors/kaggle_downloader.py`) and needs Kaggle credentials
(`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME` / `KAGGLE_KEY`).

## 6. Reset

```bash
docker compose down -v                                    # drops the volume
rm -f database/olap_duck/olap_corporate_benefits.duckdb
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on 5432 | Container not up yet, or Docker not running | `docker compose up -d`, wait for `pg_isready` |
| `password authentication failed` | `.env` changed after the volume was created | `docker compose down -v`, then up again |
| Container exits right after start with a data-directory error | Volume created by another Postgres major version | `docker compose down -v` (local data is regenerable) |
| `ModuleNotFoundError: src` | Running outside the uv environment | Prefix with `uv run`, or `uv sync` again |
| `db` or `network` tests don't run | Their markers are left out of the default run | `uv run pytest -m db` (or `-m network`) |
