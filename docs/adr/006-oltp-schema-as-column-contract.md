# ADR-006 — The OLTP schema is the column contract

## Status
Accepted (2026-10-30; roadmap assumption 6, `ST-03.1`)

## Context
Three naming sets coexisted: the schema (`cards.id`, `establishments.status`,
`main_cnae`), the generators (`card_id`, `main_cnae`, `terminal_model`) and the
validators (`card_id`, `registration_status`, `main_cnae_id`). Nothing could
flow from one to the next without renaming.

## Decision
`database/oltp_postgres/oltp_schema.sql` defines table and column names and
order. Generators emit exactly a table's columns (audit columns are left to
the database); validators read those names; the OLAP model follows the same
names.

## Consequences
- `tests/test_entity_generators.py` compares each generated table to the
  schema's columns, and `tests/test_schema.py` loads them under foreign keys.
- A schema change is a contract change: update the DBML, the generators and
  the tests in the same commit.
