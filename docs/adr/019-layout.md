# ADR-019 — A flat layout, config by purpose, outputs under data/

## Status
Accepted (2026-11-03; roadmap `EP-13`). Revises the layout of roadmap `EP-03`.

## Context
The code had grown folders three and four levels deep holding one or two
files (`data_generators/providers/`, `infrastructure/database/`, `utils/`),
five reference loaders of a dozen lines plus a builder elsewhere, and a
leftover empty folder. The config split business rules, reference data and
the issuer's checks across files whose names said little
(`business_rules.yaml` held two keys; the MCC acceptance list sat in
`validation_rules.yaml`). The generated DuckDB file lived next to the SQL that
builds it. Running the pipeline meant remembering four long commands and a
`.env` copy, and Postgres restarted at every boot.

## Decision
- **Packages only where several modules live**: `entities/`, `sources/`,
  `simulation/`, `validators/`, `domain/`, `pipeline/`. Single modules at the
  top: `config.py`, `postgres.py`, `reference.py`, `table.py`, `main.py`.
  Every package has an `__init__.py` (a test checks it).
- **Config by purpose**: `reference.yaml` (what exists: wallets, programs,
  networks, acquirers, acceptance rules, codes, statuses),
  `authorization.yaml` (the issuer's checks and their order),
  `simulation.yaml` (volumes, behaviour, calendar, fraud, the expected
  profile), `database.yaml`.
- **`database/` holds schemas and SQL only**; generated files go under
  `data/`: `raw/` (versioned inputs), `olap/`, `dataset/`.
- **A `Makefile`** (`make help`) and a `benefits` console command; Postgres
  starts with local defaults (no `.env` needed) and only when asked.

## Consequences
- Imports are one level shorter; the old paths in ADRs 001–018 describe the
  layout of their time.
- DBeaver's DuckDB connection points to `data/olap/olap_corporate_benefits.duckdb`.
- Personal editor settings (`.vscode/`) are no longer in git.
