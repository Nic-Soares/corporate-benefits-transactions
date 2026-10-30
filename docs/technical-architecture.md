# Technical Architecture

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.14, managed by uv | [ADR-005](adr/005-python-toolchain.md) |
| DataFrames | Polars | [ADR-002](adr/002-polars.md) |
| Fake data | mimesis (pt-BR) + a ported CPF/CNPJ provider | `src/data_generators/providers/` |
| OLTP | PostgreSQL 18 in Docker | [ADR-001](adr/001-postgres-duckdb-parquet.md) |
| OLAP | DuckDB, star schema | [ADR-001](adr/001-postgres-duckdb-parquet.md) |
| Distribution | Parquet | [ADR-001](adr/001-postgres-duckdb-parquet.md) |
| Rules | YAML in `config/` | [ADR-004](adr/004-reference-data-in-yaml.md) |
| Quality | ruff, pytest, GitHub Actions, Dependabot | [ADR-005](adr/005-python-toolchain.md) |

## Data flow

```
config/*.yaml ─► reference loaders ─┐
IBGE / MCC / CNAE ─► extractors ────┤
                                    ├─► PostgreSQL (OLTP, 14 tables)
seeded generators ─► entities ──────┤
                                    │
simulator ─► validators ────────────┘
                     │
                     ▼
        DuckDB (8 dimensions + fact_transactions) ─► Parquet ─► Kaggle
```

Exists today: config, extractors, loaders, generators, validators, both schemas and the schema creator. Planned: the setup pipeline (`EP-06`), the simulator (`EP-07`), the ETL (`EP-08`), the export (`EP-09`).

## Data models

- `database/model/*.dbml` document both models; they match the SQL column for column (checked in `ST-04.3`).
- OLTP (`database/oltp_postgres/oltp_schema.sql`): normalized, `id` primary keys, `*_id` foreign keys, audit columns filled by the database.
- OLAP (`database/olap_duck/`): `dim_products`, `dim_transaction_modalities`, `dim_acquirers`, `dim_cards`, `dim_cardholders`, `dim_companies`, `dim_establishments`, `dim_terminals` and `fact_transactions`.

## Key dependencies between tables

```
companies → cardholders → cards → card_products
establishments → terminals
products + transaction_modalities → mcc_modalities
products + CNAE prefixes → cnae_products
```

## Testing

- `uv run pytest` — offline: validators (approved + declined per rule), generators (schema columns, statuses, date order, reproducibility), config consistency, and the OLTP schema on in-memory DuckDB with every generated table loaded under foreign keys.
- `uv run pytest -m network` — IBGE API.
- `uv run pytest -m db` — PostgreSQL connection and schema (needs `docker compose up -d`).
