# Runbook — Local setup

From a fresh clone to a database filled with reference data and entities.

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
docker compose up -d --wait   # returns once Postgres accepts connections
```

Postgres 18 keeps its data in the `corporate_benefits_postgres_data` volume,
mounted at `/var/lib/postgresql` (18 stores data in a versioned subfolder).

```bash
uv run pytest -m db                       # connection, schema, setup (scratch schema, rolled back)
uv run python -m src.main setup --seed 42 --today 2026-10-30    # schema + reference + entities
uv run python -m src.main simulate --seed 42 --today 2026-10-30 # 90 days of transactions
```

A full year, from 2025-09-01 to 2026-08-31: the window is the `--days` before
`--today`, so `--today 2026-09-01 --days 365` (same `--today` in `setup`).
About 2.5 minutes for `simulate` and 1.6 GB of memory; 2.5 million transactions
and about 280 MB of Parquet. For more volume, `setup --scale 4` (4× the companies,
establishments and terminals): 5.7 million transactions, about 7 minutes and
3 GB, 840 MB of Parquet. `simulate` works a month at a time, so memory follows
a month, not the window; prefix long runs with `caffeinate -i` on a Mac.

```bash
uv run python -m src.main setup --seed 42 --today 2026-09-01 --reset
uv run python -m src.main simulate --seed 42 --today 2026-09-01 --days 365
```

`setup` creates the 17 OLTP tables (and `run_metadata`), upserts the reference tables from
`config/` and writes the generated entities, then prints the rows per table.
The public sources (CNAE, municipalities, population and municipal GDP from the IBGE
API, the MCC list from GitHub) are versioned in `data/raw/`, so the same seed gives the
same dataset anywhere; a missing file is downloaded.

| Option | Effect |
|---|---|
| `--seed N` | Random seed (default 42) |
| `--today YYYY-MM-DD` | Reference day of every generated date (default today); with the seed, fixes the data |
| `--reset` | Drop and recreate every table, then generate again (replaces entities and transactions) |
| `--scale N` | World size: companies (so cardholders), establishments and terminals × N (default 1) |

Without `--reset`, a second run stops: `The database already has entities`.

`simulate` takes `--seed`, `--today` (the same as `setup`'s) and `--days`
(default `simulation.days`, 90). It prints each month as it goes, then the rows
written, the approval rate and the commonest answers. It runs once per setup: the balances move, so
another run starts with `setup --reset`.

```bash
uv run python -m src.main etl   # DuckDB star schema from the OLTP database
```

`etl` writes a new `database/olap_duck/olap_corporate_benefits.duckdb`
(git-ignored) every run. Open it with `duckdb` or Python and start from the
views: `SELECT * FROM v_declines`.

```bash
uv run python -m src.main export   # quality checks, then data/final_datasets/
```

`export` writes one Parquet file per table, `data_dictionary.md`,
`quality_report.md` (the checks and the statistical profile, each against
`quality_profile` in the config) and `dataset_metadata.json` (seed, reference day, window, code
commit, config and source hashes, row counts) into `data/final_datasets/` (git-ignored). If a check
fails it writes nothing and names the check. After changing
`database/olap_duck/dictionary.yaml`, regenerate the copy in `docs/`:

```bash
uv run python -c "from src.pipeline.export import render_dictionary; open('docs/data-dictionary.md', 'w').write(render_dictionary())"
```

## 5. Network sources (optional)

```bash
uv run pytest -m network
```

Calls the IBGE CNAE, municipalities, population and GDP APIs. No credentials
needed. To download a source again, delete its file in `data/raw/`.

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
| `The database already has entities` | `setup` ran before | `--reset` to replace them |
| `The database already has transactions` | `simulate` ran before | `setup --reset`, then `simulate` |
| `--today … is before the generated data` | `simulate` got a different `--today` than `setup` | Use `setup`'s `--today` |
| `server closed the connection unexpectedly` right after `up` | Postgres still initializing | `docker compose up -d --wait` |
| A long run (a year) stalls for minutes | The Mac slept (on battery, idle) | Prefix the command with `caffeinate -i` |
| `column "…" of relation "…" does not exist` | The schema changed since the tables were created | `setup --reset` (it recreates the tables) |
| `Quality checks failed: …` on `export` | The data breaks a rule (the message names it) | Look at that check's query in `src/pipeline/export.py`; a rate out of range usually means a config change |
| `No OLAP database` on `export` | `etl` didn't run | `uv run python -m src.main etl` |
| A source fails to download | No network, or the API is down | Run again later; once in `data/raw/` it isn't downloaded again |
