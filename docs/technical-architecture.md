# Technical Architecture

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.14, managed by uv | [ADR-005](adr/005-python-toolchain.md) |
| DataFrames | Polars | [ADR-002](adr/002-polars.md) |
| Fake data | mimesis (pt-BR) + a ported CPF/CNPJ provider | `src/entities/fake.py`, `src/entities/brazil.py` |
| OLTP | PostgreSQL 18 in Docker | [ADR-001](adr/001-postgres-duckdb-parquet.md) |
| OLAP | DuckDB, star schema, plain SQL | [ADR-001](adr/001-postgres-duckdb-parquet.md), [ADR-012](adr/012-olap-plain-sql.md) |
| Distribution | Parquet | [ADR-001](adr/001-postgres-duckdb-parquet.md), [ADR-014](adr/014-public-dataset.md) |
| Rules | YAML in `config/` | [ADR-004](adr/004-reference-data-in-yaml.md) |
| Quality | ruff, pytest, GitHub Actions (with Postgres) | [ADR-005](adr/005-python-toolchain.md) |
| Layout | Flat packages, one config file per purpose | [ADR-019](adr/019-layout.md) |

## Data flow

```
config/reference.yaml ──► reference.py ──────────────┐
data/raw (IBGE, MCC) ──► sources/ ──┐                │
                                    ├─► entities/ ───┤  setup
                       seed, today ─┘                ▼
                                            PostgreSQL (OLTP, 17 tables + run_metadata)
                                                     │
          simulation/ (demand, calendar, pools) ─────┤  simulate, a month at a time
          validators/ (the issuer's checks) ─────────┘
                                                     ▼
                                       DuckDB (data/olap)                etl
                                                     ▼
              quality checks + statistical profile ─► data/dataset      export
                       (Parquet, dictionary, report, dataset_metadata.json)
```

`make dataset` runs the four commands (`uv run benefits setup | simulate | etl | export`).

## Source layout

| Module | Job |
|---|---|
| `main.py` | Command line; `--config DIR` picks the config folder before anything imports it |
| `config.py` | The YAML files, read once: `reference`, `authorization`, `simulation`, `database` |
| `postgres.py` | Connection, typed reads (whole or in chunks), COPY, `bulk_load` (keys and indexes rebuilt after a load) |
| `reference.py` | The reference tables from `reference.yaml`, in the OLTP columns |
| `table.py` | Rows indexed by column: constant-time lookups, values changed in place (balances) |
| `sources/` | IBGE CNAE, municipalities, population, GDP; the MCC list; cached and versioned in `data/raw/` |
| `entities/` | Companies, cardholders, cards, card wallets, establishments, terminals; `fake` (the seeded randomness, the reference day) |
| `domain/` | Rules both the generator and the issuer follow: `acceptance` (which wallet a shop takes), `status` (a record's status on a day) |
| `simulation/` | `demand` (who buys, how often, opening balances), `seasons` (calendar, holidays, the year-end credit), `pools` (terminals near home), `generator` (the attempts), `fraud`, `simulator` (the issuer over time), `balance`, `disputes` |
| `validators/` | The issuer's checks, in the order of `authorization.yaml`; each returns an ISO 8583 code and a reason |
| `pipeline/` | The commands: `setup`, `simulate`, `etl`, `export`; `provenance` (how the data was made), `profile` (its statistical shape) |

## How it scales

`simulate` plans every attempt as three small integers (slot, kind of place,
day), then builds, answers and writes one month at a time; balances and
pending reversals carry over. The load drops the foreign keys and secondary
indexes of `transactions` and `balance_history` and rebuilds them once, in
the same transaction. `etl` copies the two big tables to DuckDB in chunks.
A year at scale 4 (5.7 million transactions) needs about 3 GB.

## Data models

- `database/model/*.dbml` document both models; a test keeps them in line with the SQL.
- OLTP (`database/oltp/oltp_schema.sql`): normalized, `id` primary keys, `*_id` foreign keys, audit columns filled by the database. It is the column contract ([ADR-006](adr/006-oltp-schema-as-column-contract.md)).
- OLAP (`database/olap/`): 10 dimensions, `fact_transactions`, `fact_balance_movements`, 5 reference tables, analytical views; `dictionary.yaml` describes every column.

## Key dependencies between tables

```
card_programs + wallets → card_program_wallets
companies → cardholders → cards (program, modality) → card_wallets
establishments → terminals
transaction_modalities + MCC → mcc_modalities
wallets + CNAE prefixes → cnae_wallets
wallets + MCC → mcc_wallets
cards, card_wallets, establishments, terminals → transactions → balance_history
```

## Testing

- `make check` — lint, format and the offline tests: validators, generators, simulator, schema on in-memory DuckDB, ETL, export with its checks, DBML against SQL, every module imports.
- `make test-db` — Postgres: schema, setup, simulate, etl in a scratch schema, rolled back.
- `uv run pytest -m network` — the IBGE APIs.
- CI runs `make check`'s steps, the database tests and the pipeline on 30 days.
