# Corporate Benefits Transactions

A synthetic dataset of Brazilian corporate benefits card transactions — food, meal, multi-benefit, mobility and incentive cards — built to behave like the real market: every purchase attempt goes through the checks an issuer runs before approving or declining it.

The goal is a public dataset on Kaggle for studying approval rates, decline reasons and spending patterns in the Brazilian benefits market.

> **Status:** the existing code was refined and made consistent (`EP-01`–`EP-05`), the transaction core was reshaped after how benefits issuers work (`EP-06`), `python -m src.main setup` fills the database (`EP-07`) and `simulate` answers months of purchase attempts, fraud included (`EP-08`), and `etl` builds the DuckDB star schema (`EP-09`) and `export` checks it and writes the dataset as Parquet (`EP-10`). Next: the Kaggle release (`EP-11`). See the [roadmap](docs/planning/ROADMAP.md).

## Business context

In Brazil, employers give employees benefit cards whose balances can only be spent on specific things. A card belongs to a **program**, and the program fixes the **wallets** (*carteiras*) the card holds — one balance each — and the network it runs on:

| Program | Wallets | Network |
|---|---|---|
| Alimentação | Food | Proprietary |
| Refeição | Meal | Proprietary |
| Multibenefícios (rede própria) | Food, Meal, Mobility, Health, Home office, Education, Gift | Proprietary |
| Multibenefícios (bandeirado) | Same seven wallets | Visa, Mastercard or Elo |
| Presente / Premiação | Gift / Premium | Proprietary |
| Combustível | Mobility | Proprietary |

The two networks authorize differently:

- **The issuer's proprietary network** (`OWN`, the 3-party model): the cardholder picks *Food*, *Meal* or *Others* on the terminal, the issuer routes inside that option, and the establishment's **CNAE** (Brazil's economic activity code) must accept the wallet — the most specific code prefix with a rule decides.
- **Brand networks** (Visa, Mastercard, Elo — the 4-party model: acquirer → brand → issuer): the brand must accept the establishment's **MCC** (Merchant Category Code), and the issuer picks the wallet from it (meal first, then food, the other wallets, gift last).

Every decline carries an ISO 8583 response code and a specific reason (wrong PIN, wallet not accepted here, insufficient balance…). An approved purchase spends the wallet's balance, and the benefit is credited again each month. Brand cards can also withdraw cash from the gift wallet.

Fraud is labeled: `is_fraud`, `fraud_scenario` (mobile wallet after an account takeover, online use of a brand card, a card intercepted before delivery, skimming at a point of compromise) and `disputed`, which also catches legit purchases contested by mistake. See [`docs/fraud-scenarios.md`](docs/fraud-scenarios.md).

The data is shaped like the market, with synthetic numbers: lunch and evening peaks, more spending early in the month, small tickets with a long tail, spending that follows each wallet's monthly credit (most cardholders spend nearly all of it, a few let it build up), companies from a handful to thousands of employees (SME up to 250, Middle up to 1,999, Corporate from 2,000, and Public), and declines that are mostly for lack of balance.

Details in [`docs/business-rule.md`](docs/business-rule.md).

## Data sources

Every record is synthetic. The generators draw on public reference data, downloaded once into `data/raw/`:

| Data | Source | Used for |
|---|---|---|
| CNAE 2.3 classes and subclasses | [IBGE CNAE API](https://servicodados.ibge.gov.br/api/docs/cnae) (CONCLA), official | Establishment activities, CNAE rule descriptions |
| Municipalities | [IBGE localities API](https://servicodados.ibge.gov.br/api/docs/localidades), official | Where companies, cardholders and establishments are |
| Population estimates | [IBGE aggregates API](https://servicodados.ibge.gov.br/api/docs/agregados), table 6579, official | Weighting municipalities: more records where more people live |
| Merchant Category Codes | [greggles/mcc-codes](https://github.com/greggles/mcc-codes) (Unlicense), compiled from the card brands' public manuals; the ISO 18245 list itself isn't free | MCC codes and descriptions |

**Synthetic by design:** which brand accepts each MCC (`validation_rules.yaml → mcc_acceptance_rules`), which wallet each CNAE and MCC takes, the CNAE → MCC mapping, and every weight, balance, limit and ticket in `config/simulation_config.yaml`. They follow how the Brazilian benefits market works, not any company's data.

## How it works

```
config/*.yaml ──► reference data ──┐
                                   ├──► PostgreSQL (OLTP) ──► DuckDB (OLAP) ──► Parquet ──► Kaggle
generators (seeded) ──► entities ──┤
                                   │
transactions ──► validators ───────┘   approved / declined with a response code
```

- **Generators** (`src/data_generators/`) create companies (by segment and size), cardholders, cards (the programs the company contracts, with their wallets), establishments (CNAE and the matching MCC) and terminals (POS, TEF, e-commerce gateway, ATM) with real IBGE municipalities, statuses weighted as configured, and dates that follow their parent records; then purchase attempts with the usage patterns in `config/simulation_config.yaml`. One seed reproduces a whole run.
- **Validators** (`src/validators/`) check status, dates, PIN, network rules and wallet routing (CNAE for the proprietary network, MCC for brands), balance and limits (amount and purchases per day), and capture technology. Each returns the ISO 8583 code configured in `config/validation_rules.yaml` and a `decline_reason`.
- **Config** (`config/`) is the source of truth for business rules; the **OLTP schema** is the source of truth for table and column names.

Architecture: [`docs/technical-architecture.md`](docs/technical-architecture.md). Decisions: [`docs/adr/`](docs/adr/).

## Project structure

```
corporate-benefits-transactions/
├── config/                 # Business rules, reference data, simulation parameters
├── database/
│   ├── model/              # DBML models (OLTP and OLAP)
│   ├── oltp_postgres/      # PostgreSQL schema
│   └── olap_duck/          # DuckDB star schema
├── docs/
│   ├── adr/                # Architecture decision records
│   ├── planning/           # Roadmap
│   └── runbooks/           # Local setup, dependency upgrades
├── src/
│   ├── data_generators/
│   │   ├── entities/       # Companies, cardholders, cards, establishments, terminals, transactions
│   │   ├── providers/      # Seeded fake-data sources, CPF/CNPJ
│   │   └── reference_data/ # Loaders for the config's reference tables, MCC and CNAE
│   ├── extractors/         # IBGE (CNAE, municipalities, population), MCC list
│   ├── infrastructure/     # PostgreSQL / DuckDB connections, schema creation
│   ├── pipeline/           # setup: sources, reference tables, entities
│   ├── processors/         # Wallet balance movements
│   ├── main.py             # Command line (python -m src.main setup)
│   ├── utils/              # YAML, CSV and Parquet helpers
│   └── validators/         # Authorization rules
├── tests/
└── docker-compose.yaml     # PostgreSQL 18
```

## Getting started

Prerequisites: [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 if needed) and Docker.

```bash
uv sync                        # dependencies from uv.lock
uv run pytest                  # offline test suite
```

To run against PostgreSQL:

```bash
cp .env.example .env           # then set DB_PASSWORD
docker compose up -d --wait
uv run pytest -m db            # database tests
uv run python -m src.main setup --seed 42 --today 2026-10-30
uv run python -m src.main simulate --seed 42 --today 2026-10-30
uv run python -m src.main etl
uv run python -m src.main export
```

`setup` creates the OLTP schema, loads the reference tables from `config/` and writes the generated companies, cardholders, cards, wallets, establishments and terminals (`--reset` replaces them; the same `--seed` and `--today` give the same data).

Step by step, with troubleshooting: [`docs/runbooks/local-setup.md`](docs/runbooks/local-setup.md).

`simulate` generates the purchase attempts of the 90 days before `--today` (`simulation.days`), lets the issuer answer each one in time order, and writes `transactions`, `balance_history` and the final balances: monthly credits, debits, reversals, and cardholders who stop trying once their balance runs out. Use the same `--today` as `setup`.

`etl` rebuilds `database/olap_duck/olap_corporate_benefits.duckdb` from the OLTP database: 10 dimensions, `fact_transactions` (with the network, acquirer and company of each transaction) and `fact_balance_movements`, plus analytical views (`v_approval_by_program`, `v_declines`, `v_ticket_by_category`, `v_fraud_by_scenario`, `v_daily`, `v_wallet_flows_by_month`).

`export` runs 49 quality checks on the OLAP database (unique ids, every key resolves, the balance ledger holds, approval and fraud rates in range, no personal documents) and, only if all pass, writes `data/final_datasets/`: one Parquet file per table (10 dimensions, 2 facts, 4 reference tables with the acceptance rules), `data_dictionary.md` and `quality_report.md`. The dictionary is also in [`docs/data-dictionary.md`](docs/data-dictionary.md). The public tables carry no CNPJ, CPF, card number or cardholder name.

## Development workflow

- `main` = released code. `develop` = integration; every epic or story is merged into it with a `merge(<scope>): …` commit.
- One branch per epic/story, cut from `develop`: `<type>/ep-XX-<slug>` or `<type>/st-XX.Y-<slug>`, where `<type>` is the conventional-commit type (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`).
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- Before committing: `uv run ruff check`, `uv run ruff format`, `uv run pytest`. CI runs the same three.
- Tests that need the network or the database are behind markers: `uv run pytest -m network`, `uv run pytest -m db`.
- Dependencies: [`docs/runbooks/dependency-upgrades.md`](docs/runbooks/dependency-upgrades.md).

## License

MIT — see [LICENSE](LICENSE).
