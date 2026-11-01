# ADR-012 — OLAP load in plain SQL on DuckDB, full refresh

## Status
Accepted (2026-11-01; roadmap `EP-09`). dbt was left out of the dependencies
in `ST-01.2` pending this decision.

## Context
The analytical model is small (10 dimensions, 2 facts, a few views) and built
once per dataset, from a database the pipeline itself fills. It must be
testable without Postgres.

## Decision
- **Plain SQL, no dbt.** The OLTP tables are read with psycopg and registered
  in DuckDB as `stg_<table>`; `03_load.sql` fills the star schema with
  `INSERT … BY NAME SELECT …`, and `04_views.sql` adds the views. dbt would
  bring a framework, profiles and a second runtime for one batch of SQL.
- **Full refresh.** `etl` writes a new DuckDB file each run; there is no
  incremental load to keep consistent.
- **Denormalized fact.** `fact_transactions` carries the keys users would
  otherwise join for (cardholder, company, program, network, wallet,
  acquirer) and the response message. Balance movements get their own fact.
- **No personal hashes.** CPF and card number hashes stay in the OLTP.

## Consequences
- The same SQL runs in the tests on DataFrames from the simulator, in memory.
- The OLAP schema files are the column contract of the exported dataset
  (`EP-10`), as the OLTP schema is for the generators (ADR-006).
- Revisit dbt if the model grows into many layered transformations.
