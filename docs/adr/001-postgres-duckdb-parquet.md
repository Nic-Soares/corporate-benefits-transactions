# ADR-001 — PostgreSQL for OLTP, DuckDB for OLAP, Parquet to distribute

## Status
Accepted (retroactive, recorded 2026-10-30)

## Context
The project simulates an issuer's operational database — many small writes,
foreign keys, balances that change per transaction — and then publishes an
analytical dataset. One engine serves the first badly or the second badly.

## Decision
- **PostgreSQL** (Docker, version pinned in `docker-compose.yaml`) holds the
  normalized OLTP model the simulation writes to (`database/oltp_postgres/`).
- **DuckDB** holds a star schema built from it (`database/olap_duck/`):
  eight dimensions and `fact_transactions`.
- **Parquet** files exported from DuckDB are what goes to Kaggle.
- `database/model/*.dbml` documents both models and must match the SQL.

## Consequences
- Two schemas to keep in step; `tests/test_schema.py` applies both.
- DuckDB also runs the OLTP SQL, so the offline tests check the foreign keys
  without Docker. Only `pytest -m db` needs Postgres.
- DuckDB reads Polars DataFrames through `pyarrow`, which is a dependency.
