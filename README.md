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

Every record is synthetic. The generators draw on public reference data, versioned in `data/raw/` so the same seed gives the same dataset (`dataset_metadata.json` records the seed, the code commit and the hashes of the config and the sources):

| Data | Source | Used for |
|---|---|---|
| CNAE 2.3 classes and subclasses | [IBGE CNAE API](https://servicodados.ibge.gov.br/api/docs/cnae) (CONCLA), official | Establishment activities, CNAE rule descriptions |
| Municipalities | [IBGE localities API](https://servicodados.ibge.gov.br/api/docs/localidades), official | Where companies, cardholders and establishments are |
| Population estimates | [IBGE aggregates API](https://servicodados.ibge.gov.br/api/docs/agregados), table 6579, official | Weighting municipalities: cardholders and establishments where people live |
| Municipal GDP | [IBGE aggregates API](https://servicodados.ibge.gov.br/api/docs/agregados), table 5938, official | Weighting municipalities: companies where the economy is |
| Merchant Category Codes | [greggles/mcc-codes](https://github.com/greggles/mcc-codes) (Unlicense), compiled from the card brands' public manuals; the ISO 18245 list itself isn't free | MCC codes and descriptions |

**Synthetic by design:** which brand accepts each MCC (`reference.yaml → mcc_acceptance_rules`), which wallet each CNAE and MCC takes, the CNAE → MCC mapping, and every weight, balance, limit and ticket in `config/simulation.yaml`. They follow how the Brazilian benefits market works, not any company's data.

## How it works

```
config/*.yaml ──► reference data ──┐
                                   ├──► PostgreSQL (OLTP) ──► DuckDB (OLAP) ──► Parquet ──► Kaggle
generators (seeded) ──► entities ──┤
                                   │
transactions ──► validators ───────┘   approved / declined with a response code
```

- **Entities** (`src/entities/`) create companies (by segment and size), cardholders, cards (the programs the company contracts, with their wallets), establishments (CNAE and the matching MCC) and terminals (POS, TEF, e-commerce gateway, ATM) with real IBGE municipalities, statuses weighted as configured, and dates that follow their parent records. **Simulation** (`src/simulation/`) draws the purchase attempts with the demand, calendar and places in `config/simulation.yaml`, and the issuer answers them in time order. One seed reproduces a whole run.
- **Validators** (`src/validators/`) check status, dates, PIN, network rules and wallet routing (CNAE for the proprietary network, MCC for brands), balance and limits (amount and purchases per day), and capture technology. Each returns the ISO 8583 code configured in `config/authorization.yaml` and a `decline_reason`.
- **Config** (`config/`: `reference.yaml`, `authorization.yaml`, `simulation.yaml`, `database.yaml`) is the source of truth for business rules; the **OLTP schema** is the source of truth for table and column names.

Architecture: [`docs/technical-architecture.md`](docs/technical-architecture.md). Decisions: [`docs/adr/`](docs/adr/).

## Project structure

```
corporate-benefits-transactions/
├── config/                 # reference, authorization, simulation, database (YAML)
├── data/
│   ├── raw/                # Public sources (IBGE, MCC), versioned
│   ├── olap/               # The DuckDB file (generated)
│   └── dataset/            # The export (generated)
├── database/
│   ├── model/              # DBML models (OLTP and OLAP)
│   ├── oltp/               # PostgreSQL schema
│   └── olap/               # DuckDB star schema, load SQL, data dictionary
├── docs/
│   ├── adr/                # Architecture decision records
│   ├── planning/           # Roadmap
│   └── runbooks/           # Local setup, dependency upgrades
├── src/
│   ├── main.py             # Command line: setup, simulate, etl, export
│   ├── config.py           # The YAML config, read once
│   ├── postgres.py         # Connection, COPY, bulk loads
│   ├── reference.py        # Reference tables from the config
│   ├── table.py            # Rows indexed by column (constant-time lookups)
│   ├── sources/            # Public data: IBGE (CNAE, municipalities, population, GDP), MCC list
│   ├── entities/           # Companies, cardholders, cards, wallets, establishments, terminals; seeded fake data
│   ├── domain/             # Rules the generator and the issuer share: acceptance, status over time
│   ├── simulation/         # Calendar, demand, terminal pools, attempts, fraud, the issuer over time
│   ├── validators/         # The issuer's authorization checks
│   └── pipeline/           # The commands, provenance, statistical profile
├── tests/
├── Makefile                # make help
└── docker-compose.yaml     # PostgreSQL 18
```

## Getting started

Prerequisites: [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 if needed), Docker and `make`.

```bash
make install                   # dependencies from uv.lock
make check                     # lint, format, offline tests
make dataset                   # Postgres up, then setup → simulate → etl → export (a year)
make dataset SCALE=4           # a world 4× bigger: about 5.7 million transactions
make help                      # every target
```

`make dataset` runs the four commands of `uv run benefits` (the same as `python -m src.main`), with `SEED=42 TODAY=2026-09-01 DAYS=365 SCALE=1` unless given:

- `setup` creates the OLTP schema, loads the reference tables from `config/` and writes the generated companies, cardholders, cards, wallets, establishments and terminals. The same `--seed`, `--today` and `--scale` give the same data.
- `simulate` plans the purchase attempts of the `--days` before `--today`, then month by month lets the issuer answer them in time order and writes `transactions`, `balance_history` and the final balances: monthly credits, debits, reversals, cardholders who stop trying once their balance runs out.
- `etl` rebuilds `data/olap/olap_corporate_benefits.duckdb`: 10 dimensions, `fact_transactions` and `fact_balance_movements`, plus analytical views.
- `export` runs the quality checks (keys, ledger, rates, no personal documents, and the statistical profile: monthly approval, tickets, hours, geography…) and, only if all pass, writes `data/dataset/`: one Parquet file per table, `data_dictionary.md`, `quality_report.md` and `dataset_metadata.json` (seed, window, code commit, config and source hashes).

Postgres needs no `.env`: local defaults work; copy `.env.example` to change them. Step by step, with troubleshooting: [`docs/runbooks/local-setup.md`](docs/runbooks/local-setup.md). How it fits together: [`docs/technical-architecture.md`](docs/technical-architecture.md).

## Development workflow

- `main` = released code. `develop` = integration; every epic or story is merged into it with a `merge(<scope>): …` commit.
- One branch per epic/story, cut from `develop`: `<type>/ep-XX-<slug>` or `<type>/st-XX.Y-<slug>`, where `<type>` is the conventional-commit type (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`).
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- Before committing: `make check` (ruff check, ruff format, pytest). CI runs it, then the database tests and the pipeline on 30 days.
- Tests that need the network or the database are behind markers: `uv run pytest -m network`, `make test-db`.
- Dependencies: [`docs/runbooks/dependency-upgrades.md`](docs/runbooks/dependency-upgrades.md).

## License

MIT — see [LICENSE](LICENSE).
