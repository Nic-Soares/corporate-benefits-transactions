# Runbook — Local setup

From a fresh clone to a database filled with reference data and entities.

---

## 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) — `brew install uv` on macOS. It installs
  Python 3.14 (`.python-version`) when missing.
- Docker with Docker Compose (Docker Desktop, OrbStack, Colima…).

## 2. Dependencies and offline checks

```bash
make install    # uv sync: .venv from uv.lock, the project installed as a package
make check      # ruff check, ruff format --check, pytest
```

The default test run needs neither network nor Docker. It loads every
generated table into the OLTP schema on an in-memory DuckDB, so a green run
already means config, generators and schema fit together.

## 3. Database

```bash
make db         # docker compose up -d --wait: returns once Postgres accepts connections
make test-db    # connection, schema, setup, simulate, etl (scratch schema, rolled back)
```

No `.env` is needed: user `benefits`, password `change-me` by default; copy
`.env.example` to `.env` to change them. Postgres 18 keeps its data in the
`corporate_benefits_postgres_data` volume and starts only when asked
(`make db`), not at every boot. `make db-stop` stops it; `make db-wipe`
deletes its data.

## 4. The dataset

```bash
make dataset                         # a year: SEED=42 TODAY=2026-09-01 DAYS=365 SCALE=1
make dataset SCALE=4                 # 4× the companies, establishments and terminals
make dataset DAYS=90 TODAY=2026-10-30
```

`make dataset` runs `uv run benefits setup | simulate | etl | export` (the
same as `python -m src.main …`), keeping a Mac awake (`caffeinate -i`). The
window is the `DAYS` before `TODAY`: `TODAY=2026-09-01 DAYS=365` is
2025-09-01 to 2026-08-31.

| Scale | Transactions (a year) | `simulate` | Memory | Parquet |
|---|---|---|---|---|
| 1 | about 2.5 million | 2.5 min | 1.6 GB | 280 MB |
| 4 | about 5.7 million | 7 min | 3 GB | 840 MB |

- `setup` creates the 17 OLTP tables (and `run_metadata`), loads the reference
  tables from `config/reference.yaml` and writes the generated entities. The
  public sources (CNAE, municipalities, population, municipal GDP from the
  IBGE API, the MCC list) are versioned in `data/raw/`, so the same seed gives
  the same dataset anywhere. Options: `--seed`, `--today`, `--scale`,
  `--reset` (drops and recreates every table).
- `simulate` takes `--seed`, `--today` (the same as `setup`'s) and `--days`. It
  plans every attempt, then builds, answers and writes one month at a time
  (memory follows a month), printing each month's approval. It runs once per
  setup: the balances move, so another run starts with `setup --reset`.
- `etl` writes a new `data/olap/olap_corporate_benefits.duckdb` every run
  (close it in DBeaver first). Start from the views: `SELECT * FROM v_declines`.
- `export` runs the quality checks and the statistical profile (each against
  `quality_profile` in `config/simulation.yaml`) and, only if all pass, writes
  `data/dataset/`: one Parquet file per table, `data_dictionary.md`,
  `quality_report.md` and `dataset_metadata.json` (seed, window, code commit,
  config and source hashes, row counts).

Another set of rules: copy `config/` and run `uv run benefits --config DIR …`.

After changing `database/olap/dictionary.yaml`, regenerate the copy in `docs/`:

```bash
uv run python -c "from src.pipeline.export import render_dictionary; open('docs/data-dictionary.md', 'w').write(render_dictionary())"
```

## 5. Network sources (optional)

```bash
uv run pytest -m network
```

Calls the IBGE CNAE, municipalities, population and GDP APIs. To download a
source again, delete its file in `data/raw/` and run `setup`.

## 6. Reset

```bash
make clean      # the OLAP file and the dataset (data/raw stays)
make db-wipe    # the Postgres data
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `connection refused` on 5432 | Container not up yet, or Docker not running (`orb start` with OrbStack) | `make db` |
| `password authentication failed` | `.env` changed after the volume was created | `make db-wipe`, then `make db` |
| Container exits right after start with a data-directory error | Volume created by another Postgres major version | `docker compose down -v` (local data is regenerable) |
| `ModuleNotFoundError: src` | Running outside the uv environment | Prefix with `uv run`, or `uv sync` again |
| `db` or `network` tests don't run | Their markers are left out of the default run | `make test-db` (or `uv run pytest -m network`) |
| `The database already has entities` | `setup` ran before | `--reset` to replace them |
| `The database already has transactions` | `simulate` ran before | `setup --reset`, then `simulate` |
| `--today … is before the generated data` | `simulate` got a different `--today` than `setup` | Use `setup`'s `--today` |
| `server closed the connection unexpectedly` right after `up` | Postgres still initializing | `docker compose up -d --wait` |
| A long run (a year) stalls for minutes | The Mac slept (on battery, idle) | `make dataset` keeps it awake; by hand, prefix with `caffeinate -i` |
| `column "…" of relation "…" does not exist` | The schema changed since the tables were created | `setup --reset` (it recreates the tables) |
| `Quality checks failed: …` on `export` | The data breaks a rule (the message names it) | Look at that check's query in `src/pipeline/export.py`; a rate out of range usually means a config change |
| `No OLAP database` on `export` | `etl` didn't run | `uv run benefits etl` |
| `Could not set lock on file` on `etl` | DBeaver (or another program) has the DuckDB file open | Disconnect it in DBeaver, run again |
| A source fails to download | No network, or the API is down | Run again later; once in `data/raw/` it isn't downloaded again |
