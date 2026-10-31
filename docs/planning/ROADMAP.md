# Development Roadmap — Corporate Benefits Transactions

**Repository:** `corporate-benefits-transactions` (Python 3.14 + uv + polars + mimesis, PostgreSQL in Docker as OLTP, DuckDB as OLAP, Parquet → Kaggle)
**Last updated:** 2026-10-30

---

## 0. Status board

| Epic | Status | Where the work lives |
|---|---|---|
| `EP-01` Baseline and toolchain | ✅ Done — merged into `develop` 2026-10-30 | code (`pyproject.toml`, `docker-compose.yaml`) |
| `EP-02` Safety net (tests + CI) | ✅ Done — merged into `develop` 2026-10-30; CI runs after the first push | code (`tests/`, `.github/`) |
| `EP-03` Clean up existing code | ✅ Done — merged into `develop` 2026-10-30 | code (`src/`) |
| `EP-04` Config and model consistency | ✅ Done — merged into `develop` 2026-10-30 | `config/`, `database/` |
| `EP-05` Documentation | ✅ Done — merged into `develop` 2026-10-30 | `README.md`, `docs/` |
| `EP-06` Transaction core review | ✅ Done — merged into `develop` 2026-10-31 (ADR-007, 008, 009) | `docs/`, then `config/`, `database/`, `src/` |
| `EP-07` Setup pipeline (reference data + entities) | Not started — after `EP-06`, which changes the model | code (`src/main.py`, `src/processors/`) |
| `EP-08` Transaction simulator | Not started | code (`src/processors/transaction_simulator.py`) |
| `EP-09` OLAP: Postgres → DuckDB | Not started | code + `database/olap_duck/` |
| `EP-10` Dataset export and quality | Not started | code + `data/final_datasets/` |
| `EP-11` Kaggle release | Not started | Kaggle |

### Git workflow

- `main` = released code. `develop` = integration; every epic or story is merged into it with a `merge(<scope>): …` commit.
- One branch per epic/story, cut from `develop`: `<type>/ep-XX-<slug>` or `<type>/st-XX.Y-<slug>`, where `<type>` is the conventional-commit type (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`).
- Commits follow Conventional Commits (`chore(deps): …`, `docs(roadmap): …`).

---

## 1. Assumptions

1. **Nothing new until the roadmap is settled.** `EP-01` to `EP-05` only refine what already exists (upgrade, clean up, align, document). New code starts in `EP-07`.
2. **Epic order is execution order.** `EP-01` and `EP-02` are prerequisites for everything else: without a pinned toolchain and running tests, the `EP-03` cleanup has no safety net.
3. **Polars is the DataFrame library.** Code still written with pandas syntax (`.empty`, `.iloc`) is migrated, not the other way around (`EP-03`).
4. **`config/*.yaml` is the source of truth for business rules.** Where `docs/` disagrees with the YAML, the docs change (`EP-04`).
5. **The final dataset is synthetic.** No real customer, card, or merchant data enters the repository.
6. **The OLTP schema (`database/oltp_postgres/oltp_schema.sql`) is the column contract.** Generators, validators and the OLAP model use its table and column names (`id`, not `card_id`, inside `cards`). Settled 2026-10-30 in `ST-03.1`, when three different naming sets turned up.

### Decisions (settled 2026-10-30)

- **Language:** everything in English — code, comments, docs, README. Applied in `ST-03.3` (code) and `EP-05` (docs).
- **Package manager:** `uv` + `pyproject.toml` + `uv.lock`. `requirements.txt` goes away (`ST-01.2`).
- **Python:** `>=3.14`.
- **dbt:** removed from the dependencies in `ST-01.2`; whether to adopt it is decided again in `EP-09`.
- **Products:** `VA, VR, VC, VF, VM, PR` (the `simulation_config.yaml` list). `GF` leaves `pre_populated_data.yaml` and the docs in `ST-04.1`.

---

## 2. Assessment (2026-10-30)

### 2.1 What exists (to be confirmed by tests in `EP-02`)

| Area | Files |
|---|---|
| Data model | `database/model/*.dbml`, `database/oltp_postgres/oltp_schema.sql` (14 tables), `database/olap_duck/01_dimensions.sql` + `02_facts.sql` |
| Reference data | `src/data_generators/reference_data/*_loader.py`, `src/extractors/` (IBGE, MCC, Kaggle) |
| Entity generators | `company_generator`, `cardholder_generator`, `card_generator`, `card_product_generator`, `establishment_generator`, `terminal_generator` |
| Validators | `src/validators/` — status, temporal, balance/limits, infrastructure, MCC × modality, CNAE × product |
| Infra | `docker-compose.yaml` (Postgres), `src/infrastructure/database/*_manager.py` |

### 2.2 What is empty

- `src/main.py` — 0 lines
- `src/processors/transaction_simulator.py` — 0 lines
- `tests/test_cardholder_generator.py` — 0 lines

### 2.3 What is broken or inconsistent

| Problem | Where | Epic |
|---|---|---|
| Imported but undeclared dependencies: `psycopg`, `faker`, `geopandas`, `requests`, `numpy`, `python-dotenv` | `requirements.txt` | `EP-01` |
| Imports of modules that don't exist: `src.extractors.mastercard_mcc_api`, `src.common.*` | `mcc_and_cnae_loader.py`, `schema_creator.py` (and `load_and_save_reference_data.py` through it) | `EP-03` |
| No pinned versions; `postgres:latest` | `requirements.txt`, `docker-compose.yaml` | `EP-01` |
| `.env.example` referenced by the README doesn't exist | repo root | `EP-01` |
| `sys.path.insert` hacks to resolve imports | `tests/`, `src/notebooks/` | `EP-01` |
| Loose example code at module level that raises `NameError` on import; functions defined 2–3 times in the same file | `src/validators/business_rules_validators.py`, `balance_and_limits_validations.py`, `infrastructure_validations.py` | `EP-03` |
| Validators use pandas syntax in a polars project | `src/validators/*.py` | `EP-03` |
| Duplicate generators: `simple_company_generator` × `company_generator`, `simple_card_generator` × `card_generator` | `src/data_generators/entities/` | `EP-03` |
| Two fake-data libraries: `mimesis` (entities) and `faker` (transactions) | `transaction_generator.py` | `EP-03` |
| Mixed Portuguese/English names (`gerar_varias_empresas` × `generate_cardholder`) | `src/` | `EP-03` |
| `src/notebooks/` holds scratch `.py` files, not notebooks | `src/notebooks/` | `EP-03` |
| `database.yaml` points to `02_entities.sql` and `03_facts.sql`, which don't exist | `config/database.yaml` | `EP-04` |
| Product list differs between configs and `docs/` | `config/`, `docs/business-rule.md`, `docs/data-strategy.md` | `EP-04` |
| README folder structure and run instructions don't match the repo; README is in Portuguese | `README.md` | `EP-05` |

---

## 3. Execution order

```
EP-01 Baseline ──► EP-02 Tests/CI ──► EP-03 Cleanup ──► EP-04 Consistency ──► EP-05 Docs
                                                                                  │
                    ┌─────────────────────────────────────────────────────────────┘
                    ▼
              EP-06 Core review ──► EP-07 Setup ──► EP-08 Simulator ──► EP-09 OLAP ──► EP-10 Export ──► EP-11 Kaggle
```

`EP-06` goes before the setup pipeline because what it changes — products, networks, balances — shapes the tables `EP-07` loads.

`EP-05` can run alongside `EP-03`/`EP-04`, but closes only after them (the README describes the final state).

---

## EP-01 — Baseline and toolchain

**Dependencies:** none. **Size:** S (~1 day).

### ST-01.1 — Branch and workflow

- [x] Create `develop` from `main`
- [x] Document the workflow (§0) in the README — with it, "How to run" now uses `uv` (the `pip install -r requirements.txt` steps broke in `ST-01.2`) and the README roadmap points to this file. These two sections are already in English; the rest of the README is translated in `ST-05.1`

### ST-01.2 — Dependency management

- [x] `pyproject.toml` with every dependency the code actually imports, with version ranges; `requires-python = ">=3.14"` — all install on 3.14 (`geopandas` and `psycopg` included)
- [x] `.python-version` pinned to 3.14
- [x] `uv.lock` committed
- [x] Remove `requirements.txt`, `dbt-core`, and `dbt-duckdb`
- [x] Install the project as a package (hatchling, package `src`) — `sys.path.insert` removed from `load_and_save_reference_data.py` and `tests/test_company_generator.py`; the copies in `src/notebooks/` go with that folder in `ST-03.3`
- [x] Import check of every module in `src/` (outside `notebooks/`) from outside the repo: 35 import; the 6 that fail are code bugs, not missing packages (`ST-03.1`, `ST-03.4`)

### ST-01.3 — Package upgrades

- [x] Write `docs/runbooks/dependency-upgrades.md` and run it
- [x] Move everything to the latest stable release — `uv tree --outdated` is empty; the only breaking change that reached the code was `mimesis`
- [x] `mimesis` 18 → 22: `BrazilSpecProvider` ported to `src/data_generators/providers/brazil_provider.py`, same CPF/CNPJ as mimesis 18 for the same seed (checked over 20,000 values); `tests/test_company_generator.py` passes
- [x] Confirm every dependency has a Python 3.14 wheel — done in `ST-01.2`

### ST-01.4 — Environment

- [x] `docker-compose.yaml`: Postgres pinned to `postgres:18`; the volume mounts `/var/lib/postgresql` (18 moved its data dir into a versioned subfolder). Checked: 18.6 starts, `oltp_schema.sql` creates all 14 tables, `connect_pg_db()` connects
- [x] Create `.env.example` with `DB_USER` and `DB_PASSWORD`
- [x] `.gitignore` covers `.env` and `*.duckdb` (already) and now `data/raw/**` and `data/final_datasets/*`, keeping the `.gitkeep` skeleton

### ST-01.5 — Lint and format

- [x] Adopt `ruff` (lint + format), configured in `pyproject.toml` — dev dependency; rules `E`, `F`, `I`, `UP`, `B`; line length 100
- [x] First pass with automatic (safe) fixes + `ruff format` across the repo: 227 → 115 findings. Imports and `test_company_generator.py` behave as before
- Left for `EP-03` (115): 76 `F821` undefined names (pandas `pd` never imported, loose module-level code), 17 `E402`, 10 `F841`, 5 `E501`, 3 `E712`, 1 `B007`, and 3 syntax errors in `tests/test_cardholder_generator.py` (the file holds only `..`). Over half sit in `src/validators/` and `src/notebooks/`

---

## EP-02 — Safety net: tests and CI

**Dependencies:** `EP-01`. **Size:** S (~1 day).

### ST-02.1 — Existing tests running

- [x] Configure `pytest` in `pyproject.toml` (dev dependency)
- [x] Mark tests that need the network (`test_ibge_api.py`) or Docker (`test_pg_connection.py`) with markers (`network`, `db`); the default run leaves them out. Run them with `uv run pytest -m network` / `-m db`
- [x] `test_company_generator.py`, `test_ibge_api.py`, `test_pg_connection.py` rewritten from print-scripts into assertions (the IBGE one used to `pip install pyarrow` on import; the Postgres one imported `src.common`)
- [x] `test_cardholder_generator.py` filled in
- [x] `tests/conftest.py`: an offline `municipios_df` fixture, so the generator tests don't call the IBGE API

### ST-02.2 — Minimum coverage before the cleanup

- [x] One smoke test per entity generator (company, cardholder, card, card product, establishment, terminal)
- [x] `tests/test_brazil_provider.py`: CPF/CNPJ check digits over 1,000 values each
- [x] `tests/test_imports.py`: every module in `src/` (outside `notebooks/`) imports; the known-broken ones are strict `xfail`, so fixing one in `EP-03` fails the run until its entry is removed
- Moved to `EP-03`: tests for `src/validators/`. They can't lock today's behavior because none of it runs — `status_validators.py` reads an undefined `validation_rules`, the others use pandas syntax or fail on import. Each validator gets its tests when it is fixed (`ST-03.1`)
- Result: 46 passed, 7 xfailed (known bugs, each pointing to its `EP-03` story); `-m network` 1 passed + 1 xfailed; `-m db` 1 passed against Postgres 18

### ST-02.3 — CI

- [x] `.github/workflows/ci.yml`: `uv sync --locked`, `ruff format --check`, `pytest` (without `network`/`db`), on push to `main`/`develop` and on pull requests. Runs on GitHub after the first push
- [x] `ruff check` joined CI in `ST-03.3`, once the findings reached zero
- [x] Dependabot (`.github/dependabot.yml`): `uv`, GitHub Actions, and the Postgres image in `docker-compose.yaml`, weekly, minor/patch grouped

---

## EP-03 — Clean up existing code

**Dependencies:** `EP-02`. **Size:** M (~2–3 days).

### ST-03.1 — Validators

- [x] One definition per function, no module-level code; `business_rules_validators.py` went from 3 copies of each function to 2 functions
- [x] Polars instead of pandas syntax; shared helpers in `src/validators/_common.py`
- [x] Error codes read from `config/validation_rules.yaml` (`status_validations` used an undefined `validation_rules` — every call raised `NameError`)
- [x] Column names from the OLTP schema (assumption 6): `id`, `status`, `main_cnae`, `accreditation_date`, `type` — the validators read `card_id`, `registration_status`, `main_cnae_id`, `opening_date`, `terminal_type`
- [x] Consistent names: `validate_<what>` (was a mix of `validate_*` and `*_validation`); `validate_product_active` took no arguments and read undefined globals
- [x] Network routing inside the business rules: the MCC rule passes proprietary-network cards and the CNAE rule passes branded cards, so a caller can run both
- [x] CNAE rule matches by the longest prefix (`cnae_products` lists `5611` and `5611201`); it compared the 7-digit CNAE to the prefix with `==`, so it never matched
- [x] `modality_active` and `acquirer_active` check the `active` column, as the config describes (they always passed)
- [x] `config/` loaded relative to the repo, not the working directory (`src/utils/read_yamls.py`)
- [x] Tests: `tests/test_validators.py`, approved + declined case for each of the 18 validators
- [x] Standardized return value `{"passed", "error_code"}`; aligning the codes themselves with `response_codes` is a set of decisions → `ST-04.2`

### ST-03.2 — Generators

- [x] `card_generator.py`: `Card` called `_generate_card_hash`, which didn't exist — no card could be generated. The number is now hashed into `card_number_hash`
- [x] `cardholder_generator.py`: the CPF was generated and dropped; it's exported hashed, as the schema's `cpf_hash`
- [x] Column names and order of the OLTP tables (assumption 6), checked by a test per table; audit columns are left to the database
- [x] Statuses from `status_options`, drawn with the weights in `simulation_config.yaml → generation_settings.*_status_distribution` (they were uniform, and in Portuguese for establishments); distributions added for companies, card products and terminals
- [x] Dates follow their parents: admission ≥ company registration, card issue ≥ admission, product activation ≥ card issue, terminal installation ≥ establishment accreditation. Ranges from `generation_settings.date_ranges`; card validity 3–5 years (`card_validity_years`)
- [x] Cards get a modality — `OWN` or a brand — instead of `None`
- [x] A card no longer gets the same product twice
- [x] Establishments: `category` (required by the schema) from the CNAE's accepted products — `restaurant`, `supermarket`, `gas_station`, `pharmacy` (the categories of `usage_patterns`) or `other`; city/state names instead of IBGE ids
- [x] `simple_company_generator.py` and `simple_card_generator.py` deleted (no callers)
- [x] One source of randomness: `src/data_generators/providers/fake.py` (`random` + shared mimesis providers). `fake.seed(n, today=…)` reproduces a whole run, transactions included, across processes. `faker`, `numpy` and `python-ulid` removed from the dependencies
- [x] Polars `unique()` and `sample()` made deterministic (row order and seed) — a seeded run differed without it
- [x] Tests: `tests/test_entity_generators.py` chains the generators as the setup will (schema columns, statuses, unique ids, date order, reproducibility)
- Not done here, noted for realism (`EP-08`): the MCC is drawn independently of the CNAE, and mimesis' pt-BR `Finance.company()` returns US company names

### ST-03.3 — Structure

- [x] `src/notebooks/` deleted: scratch scripts with hard-coded Linux paths. `test_reference_data.py` became `tests/test_reference_loaders.py`; the pipeline sketch in `postgres_manipulation.py` is already in `docs/data-strategy.md` (and is `EP-07`)
- [x] Dead code deleted: `src/utils/data_queries.py` (queried tables that don't exist, e.g. `dim_municipios`), `municipality_data_importer.py` + `read_data_files.py` (a second, unused municipality source from a shapefile — the project uses the IBGE API). `geopandas` and its native stack (`pandas`, `numpy`, `shapely`, `pyproj`, `pyogrio`) left the dependencies
- [x] Portuguese functions, variables, comments, docstrings and messages in `src/` translated to English (the functions were renamed in `ST-03.1`/`ST-03.2`). Business data values (product names, response descriptions) stay in Portuguese — they're Brazilian-market terms
- [x] `typing_extensions` → `typing` (`TypedDict`); `typing-extensions` left the dependencies
- [x] `ruff check` finds nothing in the repo → it joined CI

### ST-03.4 — Broken imports

- [x] `mcc_and_cnae_loader.py` imported `src.extractors.mastercard_mcc_api` → `src.extractors.mcc_extractor`. Checked against the public source: 286 MCCs, all with brands. Output column renamed `mcc` → `mcc_code` (the schema's and the generator's name); dedup made deterministic; CNAE CSV path no longer depends on the working directory
- [x] `schema_creator.py` imported `src.common.*` and a missing `src.utils.load_db_config` → `src.infrastructure.database.*` and `read_yamls.load_database`. Checked: creates the 14 OLTP tables in Postgres 18 and the 9 OLAP tables in DuckDB
- [x] `tests/test_pg_connection.py` → fixed in `EP-02`
- [x] `load_and_save_reference_data.py` ran (network calls included) on import → `main()`
- [x] `config/database.yaml` pointed DuckDB to `02_entities.sql` and `03_facts.sql`, which don't exist → `01_dimensions.sql` + `02_facts.sql` (was `ST-04.1`); `postgres_manager.py` read the config relative to the working directory
- [x] `src/adapters/` deleted: `mcc_modality_adapter.py` used pandas without importing it, `cnae_product_adapter.py` was empty, and nothing called them. Loading `mcc_modalities` from `mcc_acceptance_rules` is `EP-07`
- [x] `ibge_municipalities.py`: the UF falls back to the região imediata when the microrregião is null — all 5,571 municipalities now have one of the 27 UFs
- [x] `tests/test_imports.py` has no `KNOWN_BROKEN` entries left: every module in `src/` imports

---

## EP-04 — Config and model consistency

**Dependencies:** `EP-03`. **Size:** S (~1 day).

### ST-04.1 — Configs

- [x] `config/database.yaml`: fix the DuckDB SQL paths — done in `ST-03.4`
- [x] Products `VA, VR, VC, VF, VM, PR` in every YAML; `GF` removed. `VF` Vale Farmácia (pharmacy CNAEs `4771…`), `VM` Multibenefícios (wherever VA, VR or VF is accepted), `PR` Premiação (incentive: supermarkets, restaurants, general retail — where `GF` was)
- [x] `cnae_products` fixed on the way: `4781` (clothing) and `4784` (bottled gas) were mapped to VA; added `4724` (fruit and vegetables) and `4782` (footwear); every entry commented with its activity
- [x] `terminal_models_by_acquirer` is keyed by acquirer id with `{model, type}`, but the generator read it by acquirer name with a hard-coded model → type map: with the real config every terminal came out as "POS Genérico". The generator now reads the config's shape, and the generator tests run against the real config
- [x] One list of capture technologies: `transaction_technologies` (`CHIP`, `MAG_STRIPE`, `CONTACTLESS`, `MOBILE_NFC`, `APPLE_PAY`, `GOOGLE_PAY`) is what `transactions.capture_type` holds; the unused `capture_technologies` list is gone, and the terminal-type support moved from the validator into `validation_rules.yaml → capture_type_support`
- [x] `validation_order` matches `src/validators/` (checked by `test_codes_are_documented`)
- [x] YAML comments and descriptions in English. Business data values — product and segment names, response descriptions — stay in Portuguese
- [x] Sections the code doesn't read yet are marked as such: `product_acceptance_rules`, `commission_rules`, `transaction_technology_rules`, `data_volumes`, `approval_rates`, `usage_patterns`, `validation_config`, `product_specific_rules`
- Two segment lists stay on purpose: `pre_populated_data.yaml → segments` (industry) and the company size segments in `company_generator.py` (`Public`, `Corporate`, `SME`…), which is what `companies.segment` holds

### ST-04.2 — Response codes and statuses

Found while fixing the validators (`ST-03.1`); settled 2026-10-30 (Nicolas confirmed the CNAE rule and left the rest to the roadmap). Done ahead of `ST-03.2`, which needs the statuses.

- [x] Establishment codes follow `response_codes` (the catalog with descriptions): `inactive 19 / suspended 20 / terminated 21`; `18` stays "Empresa inativa" for the employer
- [x] Duplicate meanings removed from `response_codes`: `59` and `60` dropped, `27`/`28` kept
- [x] "Record not found" codes in `validation_rules.yaml → not_found`, one per entity and described in `response_codes`: `92` card, `93` card product, `94` cardholder, `95` modality, `97` establishment, `98` terminal, `99` acquirer. A status outside the rule's list → `unknown_status: 96` ("Erro no sistema")
- [x] Statuses in English everywhere, listed in `business_rules.yaml → status_options` (now also `card_product` and `terminal`); `canceled` → `cancelled`; terminal `maintenance` declines as `22`; card product `suspended`/`cancelled` → `23`
- [x] Proprietary network = modality `OWN` (type `proprietary_network` in `pre_populated_data.yaml`), not a null `modality_id`. Matches the business: the 3-party model (issuer's own network, authorized by the establishment's CNAE) vs. the 4-party model (acquirer → brand, authorized by MCC)
- [x] CNAE rule: the longest prefix wins — confirmed
- [x] `terminal_acquirer_match` (code `31`) removed: it checked nothing. The real rule (an acquirer only takes the proprietary network once integrated with it) needs acquirer × network data → idea for `EP-08`
- [x] `tests/test_validators.py::test_codes_are_documented`: every code a validator can return has a description
- Generators still emit the old statuses (`ATIVA`…, cardholder `suspended`) → `ST-03.2`

### ST-04.3 — Data model

- [x] DBML × SQL: same tables, columns and types, OLTP and OLAP (the OLTP DBML lacked `cardholders.position` and `department`)
- [x] `transaction_modalities.code` (and `dim_transaction_modalities.code`) dropped: required and unique, but nothing fills it — the config has none and `id` already holds `VISA`, `OWN`… Inserting the modalities would have failed
- [x] `cnae_products.cnae_description` optional: the 4-digit prefixes (`4711`) aren't codes in the CNAE dataset, so they have no description to load
- [x] `tests/test_schema.py`: the OLTP schema on in-memory DuckDB takes the config's reference data and every generated table, with the foreign keys enforced (and a dangling reference is rejected); the OLAP schema takes the reference dimensions; a `db` test applies the OLTP schema to Postgres 18
- [x] `pyarrow` added: DuckDB needs it to read Polars DataFrames (`duckdb_manager.insert_dataframe` too)
- For `EP-07`: `companies.parent_id` references `companies`, so holdings load before their branches

---

## EP-05 — Documentation

**Dependencies:** closes after `EP-04`. **Size:** S (~1 day).

### ST-05.1 — README

- [x] Rewritten in English: business context (products, the two networks), how it works, project structure as it is, getting started, workflow
- [x] "Getting started" from the real repo (`uv sync`, `uv run pytest`, `docker compose up -d`, `pytest -m db`, the schema creator) — each command checked
- [x] Links to this roadmap, the ADRs and the runbooks

### ST-05.2 — Retroactive ADRs (`docs/adr/`)

- [x] `001` — Postgres (OLTP) + DuckDB (OLAP) + Parquet
- [x] `002` — Polars instead of pandas
- [x] `003` — Network routing: MCC for brands, CNAE (longest prefix) for the proprietary network `OWN`
- [x] `004` — Business rules and reference data in YAML
- [x] `005` — Python toolchain: 3.14 + uv + ruff + pytest + CI
- [x] `006` — The OLTP schema is the column contract (assumption 6)

### ST-05.3 — Runbooks (`docs/runbooks/`)

- [x] `dependency-upgrades.md` (written in `ST-01.3`; `geopandas` notes removed)
- [x] `local-setup.md` — from clone to a database with the schema, reset, troubleshooting

### ST-05.4 — Business docs

- [x] `docs/business-rule.md`: products, networks, CNAE/MCC rules, validation order and codes, statuses — from the YAML
- [x] `docs/data-strategy.md`: source of each table; entities generated in batches, parents first (it described an on-demand `get_or_create` flow the code doesn't follow)
- [x] `docs/technical-architecture.md`: stack with its ADRs, data flow, what exists vs. planned, testing
- [x] `docs/transactions_flow_diagram.mmd`: in English and checked against the code — it named Prefect (not used), 15 tables (14), `GF`, a terminal/acquirer check (removed in `ST-04.2`), and `dim_time` / `fact_authorizations` (not in the OLAP model). Planned steps are dashed
- [x] Every relative link in `README.md` and `docs/` resolves

---

## EP-06 — Transaction core review

**Scope:** findings #1–#5 — done. **Goal:** the transaction core — who issues, what the card holds, where it's accepted, how the balance moves, why a purchase is declined — behaves like a real Brazilian benefits issuer, not only a consistent one. **Dependencies:** `EP-05`. **Size:** M (~1 week).

**Method:** compare the model with the business reference of an issuer (an internal knowledge base, **kept out of this repository**). Only market-wide concepts and public rules enter the repo — the 3-party / 4-party models, wallets, the PAT law. No issuer names, internal systems, parameters or limits: every number in `config/` stays synthetic.

### ST-06.1 — Assessment (2026-10-30)

What the project models today against how the market works. Priority: **must** (the dataset would be wrong without it), **should** (clearly more realistic), **could** (nice to have).

| # | Topic | Today | In the market | Priority |
|---|---|---|---|---|
| 1 | **Products vs. wallets** | Six "products" (`VA, VR, VC, VF, VM, PR`) on a card; `VM` Multibenefícios is one of them | A card belongs to a **program** and holds one or more **wallets** (*carteiras*). Mono-product programs (Food, Meal) have one wallet; the multi-benefit program has several (Food, Meal, Mobility, Health & wellness, Home office, Education, Gift). Multi-benefit is a card, not a wallet | must |
| 2 | **Network per program** | Each card draws `OWN`, Visa, Mastercard or Elo at random | The network is a property of the program: most programs run on the issuer's own network (3-party); a multi-benefit program may run on a market brand — Visa, Mastercard or Elo (4-party). A card never "picks" a brand | must |
| 3 | **Wallet chosen at purchase** | The transaction samples a random card product | 3-party: the cardholder chooses the wallet on the terminal (food / meal / other). 4-party: the issuer picks it from the MCC, in a priority order (meal → food → other closed wallets → gift), skipping paused or empty wallets | must |
| 4 | **Balance follows the transactions** | `current_balance` drawn at random and never changes | Each wallet starts the simulation with a balance; every approved purchase lowers it and a reversal gives it back, so later purchases can be declined for insufficient funds. `balance_history` holds those movements. Where the balance comes from (employer credit orders) is out of scope | must |
| 5 | **Response codes** | Own numbering; `55`–`58` reused for temporal checks | ISO 8583 codes are the market's language: `51` insufficient funds, `55` wrong PIN, `54` expired card, `57` not permitted to cardholder, `58` not permitted to terminal, `61` amount limit, `65` frequency limit, `14` invalid card, `05` do not honor. Wrong PIN and "establishment registered under another category" are among the most common declines and aren't modeled | must |
| 6 | **Limits** | Daily and monthly amount per card product | A wallet has a daily amount limit **and a daily transaction count**; monthly credit caps per wallet | should |
| 9 | **Transaction types** | Purchase only | Purchase, reversal / cancellation; in 4-party, cash withdrawal on the gift wallet with a fee and limits. Channels: card present (chip, contactless, wallets), e-commerce, virtual card | should |
| 10 | **Usage patterns** | Uniform: any card, any terminal, any time in 30 days | Meal on weekdays around lunch, near work; food in larger tickets after the credit day; fuel spread through the week. `usage_patterns` in the config already describes this and nothing reads it | should |
| 11 | **Company segments and size** | `Public`, `Corporate`, `Middle`, `SME`, `High SME`; cardholders per company fixed | SME, Middle, Corporate and Public; the segment follows the number of employees, which sets how many cardholders a company has | should |
| 12 | **Establishment acceptance** | CNAE prefix × product, checked at each purchase | On the proprietary network the issuer **accredits** the establishment for specific wallets (from its CNAE) and curates the network; market acquirers' terminals only capture | could |
| 13 | **Card formats** | Every card nominal | Non-nominal reusable cards tied to a company credit pool (first day, temporary staff); virtual cards | could |
| 14 | **Negative balance** | Impossible | Offline or forced transactions can leave a wallet negative; it's written off after a long period without credits | could |

**Out of scope** (Nicolas, 2026-10-30) — the project is about the transaction:
- fees and establishment payments: the PAT/Auxílio rules on fees, reimbursement and transfers (#7) and establishment settlement (#8);
- the employer side: credit orders, credit schedules and expiry (cut from #4).

### ST-06.2 — Decisions (Nicolas)

- [x] Product model (#1): **programs + wallets** — agreed. Programs: Food, Meal, Multi-benefit 3-party, Multi-benefit 4-party, Gift, Premium, Fuel
- [x] Market brands for 4-party (#2): **keep Visa, Mastercard and Elo**
- [x] Response codes (#5): **ISO 8583**, the card industry standard; a missing record declines with the ISO code for that party (`14`, `15`, `57`, `03`, `58`, `92`)
- [x] Balance (#4): no employer credit orders — a starting balance that the transactions move
- [x] Scope: the five "must" items (#1–#5) here; the "should" items (#6, #9, #10, #11) go to the simulator (`ST-08.2`), where they show; the "could" items (#12–#14) stay ideas

### ST-06.3 — Model changes

- [x] `products` → `wallets` (8); new `card_programs` (7: Food, Meal, Multi-benefit 3-party and 4-party, Gift, Premium, Fuel) and `card_program_wallets`; `cards.program_id`; `card_products` → `card_wallets` (every wallet of the program); `cnae_products` → `cnae_wallets`; new `mcc_wallets`
- [x] Network from the program: `OWN` for 3-party programs, Visa / Mastercard / Elo for the 4-party one; `cards.modality_id` never null
- [x] Wallet choice: the cardholder's pick, checked by `validate_cnae_wallet` (3-party); `validate_mcc_brand` + `route_wallet` by MCC priority (4-party), declining `57` when no wallet takes the MCC and `51` when none has the balance
- [x] Balance follows the transactions: synthetic starting balance and limits per wallet (config); `src/processors/balance.py → debit` moves it and writes `balance_history`
- [x] ISO 8583 response codes; every validator also returns a `decline_reason`, stored in `transactions`; PIN check (`55`) with `transactions.pin_status`
- [x] Schema, DBML (match checked), config, generators, validators, loaders and tests changed together (ADR-006): 100 tests; the OLTP schema on DuckDB takes every reference and generated table under foreign keys; `pytest -m db` applies the 17 tables to Postgres 18
- [x] ADR-007 — the transaction core model; ADR-003 refined
- [x] Docs and diagrams: `README.md`, `docs/business-rule.md` (program, network and authorization diagrams, code table), `docs/data-strategy.md` (ER diagram), `docs/technical-architecture.md`, `docs/transactions_flow_diagram.mmd`
- [x] Config sections no code read and that described the old products or fees removed (`product_acceptance_rules`, `commission_rules`, `product_specific_rules`, `validation_config`)

### ST-06.4 — Transaction record (2026-10-31, ADR-008)

- [x] `transactions.card_wallet_id` → `card_wallets` (was `wallet_id` → `wallets`): the balance charged, not the wallet type; validators, `route_wallet` and `debit` work on it
- [x] `response_codes` table (16 ISO codes) referenced by `transactions.response_code`; `response_message` leaves the OLTP (the fact keeps it, denormalized)
- [x] `authorizations` merged into `transactions` (`nsu`, `authorization_code`); the fact drops `authorization_datetime` and `authorization_status`, which repeated `date` and `response_code`
- [x] Still 17 OLTP and 10 OLAP tables; DBML matches SQL; the schema test inserts transactions under the new foreign keys

### ST-06.5 — Market review (2026-10-31, ADR-009)

Second pass against how benefits cards are used in the market. The model held; the gaps were in how the data behaves. Every number in the config stays synthetic.

- [x] Proprietary network: the terminal offers *Food*, *Meal* or *Others* and the issuer routes inside the option (`wallet_routing.proprietary_options`, `transactions.wallet_option`); `route_wallet` serves both networks and folds the card-wallet status, wallet and CNAE checks
- [x] Monthly credit: `card_wallets.monthly_credit`, `benefit_credit_day`, `balance.credit` (`balance_history` `credit`); the starting balance is a share of the credit
- [x] Cash withdrawal (from `ST-08.2`, #9): `transactions.transaction_type`, brand cards from GIFT only, at cash machines (MCC `6011`, ATM network and terminals)
- [x] Limits per wallet from the config, Meal lowest; purchases per day on Food and Meal (from `ST-08.2`, #6): `card_wallets.daily_count_limit`, `validate_daily_count` → `65`
- [x] Companies by segment, cardholders by the segment's size (SME 1–250, Middle 251–1,999, Corporate 2,000+, Public any), cards by the company's program bundle (from `ST-08.2`, #11)
- [x] Establishments by category → CNAE → the MCC of that CNAE (`cnae_mcc`), so the CNAE and MCC rules describe the same business; e-commerce gateways for online businesses
- [x] `TransactionGenerator` (from `ST-08.2`, #10): log-normal card activity and shop popularity, inactive records rarely used, hour curves (lunch and evening; restaurant and fuel their own), weekday and day-of-month weights, log-normal tickets per category, captures per terminal type (virtual cards never physical), wrong option and off-pattern attempts, no attempt before the card or terminal exists
- [x] Calibration runs (scratch script, four seeds): 75–82% approved, most declines `51`; volume per card (`transactions_per_card_month`) and no attempt on a terminal before it's installed; the simulator (`EP-08`) checks it for real

---

## EP-07 — Setup pipeline

**Dependencies:** `EP-06`. **Size:** M (~2–3 days).

### ST-07.1 — Reference data

- [ ] Load every reference table from `config/` into Postgres: wallets, programs and their wallets, modalities, acquirers, response codes, `cnae_wallets`, `mcc_wallets`, and `mcc_modalities` from `validation_rules.yaml → mcc_acceptance_rules` (descriptions from the public MCC list and the CNAE dataset)
- [ ] Idempotent: running it twice doesn't duplicate rows

### ST-07.2 — Entities

- [ ] Generate companies → cardholders → cards → card wallets → establishments → terminals, at `simulation_config.yaml → data_volumes` (companies, `cardholder_scale`, establishments, terminals)
- [ ] Write to Postgres respecting the foreign keys — parents first, and holdings before branches (`companies.parent_id`)
- [ ] The same seed gives the same database

### ST-07.3 — Entrypoint

- [ ] `src/main.py` with subcommands: `setup` (schema, reference data, entities), `simulate`, `export` (the last two arrive with `EP-08` and `EP-10`)
- [ ] Progress logging and row counts per table
- [ ] Runbook: from an empty Docker to a filled database

---

## EP-08 — Transaction simulator

**Dependencies:** `EP-07`. **Size:** L (~1–2 weeks, with the items from `EP-06`).

### ST-08.1 — Authorization flow

- [ ] `transaction_simulator.py`: transaction → validations in `validation_order` → authorization → `balance_history` when approved
- [ ] Branded network checks MCC; proprietary network checks CNAE

### ST-08.2 — Realism

- [ ] Approval rate near `approval_rates.overall`, declines mostly `51`
- [ ] Credit on `benefit_credit_day`; daily usage, daily count and monthly usage tracked per wallet over time
- [ ] Reversals and cancellations (from `EP-06`, #9)
- [ ] Cardholders buy near where they live and work (from `EP-06`, #10)
- [x] Moved to `ST-06.5`: daily count (#6), withdrawal and channels (#9), usage patterns (#10), segments and size (#11)

### ST-08.3 — Fraud scenarios

- [ ] Define the scenarios (e.g. rapid repeated attempts, use outside the usual region)
- [ ] From `ST-03.2`: draw the MCC from the CNAE (a restaurant CNAE can get a gas-station MCC today); Brazilian company names (mimesis pt-BR returns US ones)
- [ ] Idea from `ST-04.2`: acquirer × network acceptance — an acquirer only takes the proprietary network once integrated with it (open arrangement under the 2025 PAT decree); would bring back a terminal/acquirer decline code
- [ ] Label transactions generated by these scenarios (a column dataset users can train on)

---

## EP-09 — OLAP: Postgres → DuckDB

**Dependencies:** `EP-08`. **Size:** M (~2–3 days).

- [ ] Decide dbt × plain SQL (ADR)
- [ ] ETL from OLTP into `dim_*` and `fact_transactions`
- [ ] Basic analytical views (approval by product, average ticket, declines by response code)

---

## EP-10 — Dataset export and quality

**Dependencies:** `EP-09`. **Size:** S (~1 day).

- [ ] Export dimensions and facts to `data/final_datasets/*.parquet`
- [ ] Quality checks: foreign keys, nulls, approval rates vs. config
- [ ] Data dictionary (one line per column)

---

## EP-11 — Kaggle release

**Dependencies:** `EP-10`. **Size:** S (~1 day).

- [ ] Dataset page (description, benefits-market context, license)
- [ ] Example notebook
- [ ] Publish and link from the README
