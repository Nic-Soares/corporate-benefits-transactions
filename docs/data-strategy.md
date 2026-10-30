# Data Strategy

Where each table's data comes from. Table and column names are those of `database/oltp_postgres/oltp_schema.sql` ([ADR-006](adr/006-oltp-schema-as-column-contract.md)).

## Reference tables — from the config

| Table | Source | Rows |
|---|---|---|
| `products` | `pre_populated_data.yaml → products` | 6 (VA, VR, VC, VF, VM, PR) |
| `transaction_modalities` | `pre_populated_data.yaml → transaction_modalities` | 4 (OWN, VISA, MASTERCARD, ELO) |
| `acquirers` | `pre_populated_data.yaml → acquirers` | 6 |
| `mcc_modalities` | `validation_rules.yaml → mcc_acceptance_rules` × the public MCC list | one row per MCC × accepting brand |
| `cnae_products` | `pre_populated_data.yaml → cnae_products` | one row per CNAE prefix × product |

Loaders: `src/data_generators/reference_data/`. External sources: the IBGE municipalities API, a public MCC list, and the CNAE 2024 dataset on Kaggle (`src/extractors/`).

## Entity tables — generated

Generated in batches, parents first, by `src/data_generators/entities/`:

```
companies (holdings, then branches)
  └── cardholders            admission ≥ company registration
        └── cards            issue ≥ admission; modality OWN or a brand
              └── card_products   1–3 distinct products; activation ≥ card issue
establishments               CNAE mostly one that accepts a product; category from it
  └── terminals              model and type from the acquirer's list; installation ≥ accreditation
```

- Statuses: weights in `simulation_config.yaml → generation_settings.*_status_distribution`.
- Dates: ranges in `generation_settings.date_ranges`, relative to a reference day.
- CPF and card numbers are generated valid and stored hashed (`cpf_hash`, `card_number_hash`).
- Reproducible: `src/data_generators/providers/fake.py → seed(n, today=…)` fixes every random source.
- Loading order matters: `companies.parent_id` references `companies`, so holdings go in before branches.

## Transactional tables — simulated (planned, `EP-07`)

| Table | Content |
|---|---|
| `transactions` | Every purchase attempt, with its response code |
| `authorizations` | The authorization record of each transaction |
| `balance_history` | Balance movements of approved transactions |

A transaction picks a card product (so the card holds the product it pays with) and a terminal (so the establishment has one), runs the validators in order, and records the first failing code or `00`.

## Pipeline (planned, `EP-06`)

1. Create the schemas (`src/infrastructure/schema/schema_creator.py` — exists).
2. Load the reference tables.
3. Generate and load the entities, at the volumes in `simulation_config.yaml → data_volumes`.
4. Simulate transactions.
5. ETL into the DuckDB star schema (`EP-08`), export Parquet (`EP-09`).
