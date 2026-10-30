# ADR-004 — Business rules and reference data in YAML

## Status
Accepted (retroactive, recorded 2026-10-30)

## Context
Products, modalities, acquirers, CNAE and MCC acceptance, response codes,
validation rules and generation weights change more often than the code that
applies them, and should be readable without reading Python.

## Decision
`config/` is the source of truth for business rules:

| File | Holds |
|---|---|
| `pre_populated_data.yaml` | Reference tables, CNAE × products, terminal models, response codes |
| `validation_rules.yaml` | Validation order, error codes, MCC × brands, not-found codes |
| `business_rules.yaml` | Valid statuses per entity, product and network descriptions |
| `simulation_config.yaml` | Volumes, status weights, date ranges, usage patterns |
| `database.yaml` | Connection settings and schema paths |

Code reads it through `src/utils/read_yamls.py`, with paths relative to the
repository, never hard-coding a value the config defines. Where `docs/`
disagrees with the YAML, the docs change.

## Consequences
- Tests check the config against itself (every code a validator returns is
  described) and run the generators against the real files.
- Sections not read by the code yet are marked as such in the YAML.
- Business data values (product names, response descriptions) stay in
  Portuguese; keys, comments and descriptions are in English.
