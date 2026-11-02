# Development Roadmap — Corporate Benefits Transactions

**Repository:** `corporate-benefits-transactions` (Python 3.14 + uv + polars + mimesis, PostgreSQL in Docker as OLTP, DuckDB as OLAP, Parquet → Kaggle)
**Last updated:** 2026-11-03

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
| `EP-07` Setup pipeline (reference data + entities) | ✅ Done — merged into `develop` 2026-10-31; ST-07.5 2026-11-01 (ADR-018) | code (`src/main.py`, `src/processors/`) |
| `EP-08` Transaction simulator | ✅ Done — merged into `develop` 2026-11-01 (ADR-010, 011, 013, 015, 016, 017); ST-08.9–08.12 2026-11-03 | code (`src/processors/transaction_simulator.py`) |
| `EP-09` OLAP: Postgres → DuckDB | ✅ Done — merged into `develop` 2026-11-01 (ADR-012) | code + `database/olap_duck/` |
| `EP-10` Dataset export and quality | ✅ Done — merged into `develop` 2026-11-01 (ADR-014) | code + `data/final_datasets/` |
| `EP-11` Kaggle release | Not started — after `EP-13` | Kaggle |
| `EP-12` Architecture review: a coherent dataset at volume | ✅ Done — merged into `develop` 2026-11-03 |
| `EP-13` Layout and developer infrastructure | ✅ Done — merged into `develop` 2026-11-03 (ADR-019) | code, `config/`, `database/`, `.github/` |

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
| Reference data | `src/data_generators/reference_data/*_loader.py`, `src/extractors/` (IBGE, MCC) |
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

- [x] Load every reference table from `config/` into Postgres: wallets, programs and their wallets, modalities, acquirers, response codes, `cnae_wallets` (descriptions from the CNAE dataset), `mcc_wallets`, and `mcc_modalities` from `validation_rules.yaml → mcc_acceptance_rules` (descriptions from the public MCC list) — `src/pipeline/reference.py`
- [x] Idempotent: upsert on the primary key; the schema's indexes became `IF NOT EXISTS`
- [x] Public sources cached in `data/raw/` (`src/pipeline/sources.py`)

### ST-07.2 — Entities

- [x] Generate companies → cardholders → cards → card wallets → establishments → terminals, at `simulation_config.yaml → data_volumes` — `src/pipeline/entities.py`
- [x] Written with COPY, parents first, holdings before branches
- [x] The same seed and reference day give the same database (checked by hash); a second run stops unless `--reset`

### ST-07.3 — Entrypoint

- [x] `src/main.py setup [--seed] [--today] [--reset]`, one transaction; `simulate` and `export` arrive with `EP-08` and `EP-10`
- [x] Progress logging and row counts per table
- [x] `postgres_manager` rewritten for psycopg 3 (the COPY helpers used the psycopg 2 API); the unused Parquet export of the reference data removed
- [x] Tests: the schema test loads the reference tables as the setup builds them; `pytest -m db` runs the whole setup in a scratch schema (counts, refusal, reset, same seed → same data)
- [x] Runbook: from an empty Docker to a filled database (`docs/runbooks/local-setup.md`)

### ST-07.4 — Data sources (2026-10-31)

- [x] CNAE from the official IBGE API instead of a Kaggle copy; `kagglehub` and the downloader removed
- [x] Municipalities weighted by the IBGE population estimate (table 6579); 80% of cardholders live in their company's city
- [x] Sources and what is synthetic listed in the README (`mcc_acceptance_rules` marked synthetic: the brands don't publish their tables)

---

### ST-07.5 — Company geography (2026-11-01, ADR-018)

- [x] Companies drawn by IBGE municipal GDP (`src/extractors/ibge_gdp.py`); establishments stay by population
- [x] Share of cardholders in the company's city per segment (`company_segments.*.same_city`): SME 90% to Corporate 35%
- [x] Result (seeds 42 and 7): São Paulo 21–24% of the transactions, then Rio de Janeiro and Minas Gerais

### ST-07.6 — Card and terminal dates (2026-11-02)

- [x] A card is issued 0–30 days after the admission and renewed on expiry under the same id (`card_issue_days_after_admission`); `card_issuance` range removed; admissions up to 10 years back, companies up to 20
- [x] A terminal is installed 0–30 days after the accreditation (`terminal_install_days_after_accreditation`)
- [x] Why: dates drawn between the parent's date and today piled up near today, so a one-year simulation saw the cards and terminals multiply and the volume grow 4.7×
- [x] Result (seed 42, 2025-09-01 to 2026-08-31): 2.47 million transactions, 177–250 thousand a month, approval 87%, 53 checks, 281 MB of Parquet

---

## EP-08 — Transaction simulator

**Dependencies:** `EP-07`. **Size:** L (~1–2 weeks, with the items from `EP-06`).

### ST-08.1 — Authorization flow

- [x] `src/processors/transaction_simulator.py`: credits, attempts and reversals in time order; each attempt through `validation_order`; approval → `authorization_code`, debit, `balance_history`
- [x] Brand network checks the MCC, proprietary network the CNAE (inside `route_wallet`)
- [x] `python -m src.main simulate [--seed] [--today] [--days]` (`src/pipeline/simulate.py`): reads the database, writes `transactions`, `balance_history` and the final balances in one transaction; refuses a second run and a `--today` before the data
- [x] `docker-compose.yaml` healthcheck (over TCP), so `docker compose up --wait` waits for Postgres

### ST-08.2 — Realism

- [x] Approval near `approval_rates.overall` (80% with seed 42), declines mostly `51`
- [x] Credit on `benefit_credit_day`; daily amount, daily count and monthly amount tracked per wallet over time
- [x] Cardholders mostly stop trying after a decline for balance, until the next credit (`give_up_after_insufficient_balance`)
- [x] Reversals (from `EP-06`, #9): `transactions.related_transaction_id`, type `reversal`, `balance_history` `reversal`
- [x] Cardholders buy near where they live (from `EP-06`, #10): `local_purchase_ratio`, city then state
- [x] Volume per card and month (`transactions_per_card_month`) over `simulation.days`
- [x] Tests: answers, ledger chain, limits, reversals, giving up, same seed → same simulation; `pytest -m db` runs setup + simulate
- [x] Moved to `ST-06.5`: daily count (#6), withdrawal and channels (#9), usage patterns (#10), segments and size (#11)

### ST-08.3 — Fraud scenarios

- [x] Scenarios from the market's typologies (`docs/fraud-scenarios.md`): account takeover into a mobile wallet, card not present on the open wallet, card intercepted before delivery, point of compromise (skimming)
- [x] `transactions.is_fraud`, `fraud_scenario`, `disputed` (and in the fact table); disputes include legit purchases contested by mistake
- [x] Fraudsters don't give up after a balance decline, pick shops the card works at, and are never reversed
- [x] Brazilian company and shop names from surnames, activity and legal type (mimesis pt-BR returned real companies' names); the shop's trade name says its business
- [x] Done earlier: MCC drawn from the CNAE (`ST-06.5`)
- Dropped ideas: acquirer × network acceptance; blocking the card after a dispute (the dataset is not an anti-fraud system)

### ST-08.4 — Spending follows the credit (2026-11-01, ADR-013)

- [x] Attempts per active wallet: monthly credit × spending ratio ÷ average ticket where it is used; the volume is their sum (`transactions_per_card_month` removed)
- [x] Spending profile: most cardholders spend 80–100%, a tenth are savers (`spend_profile`); `card_activity_sigma` removed
- [x] Giving up after a balance decline per option or kind of place, not per card
- [x] Credit only to active cardholders; fewer inactive and blocked cards; virtual cards look for a usable terminal beyond their city
- [x] Result (three seeds): active cards spend 74–90% of Food and Meal; approval 81–82%

### ST-08.5 — Program wallets per company (2026-11-01, ADR-015)

- [x] Each company picks, per program, which of the program's wallets its cards hold (`program_wallet_shares`)
- [x] `ref_program_wallets` in the OLAP and the export; check: cards hold only wallets their program allows
- [x] Wallets activated 0–15 days after the card's issue (`wallet_activation_days`), so the credited cards follow the issues
- [x] Declines for balance keep the wallet that fell short; check: none without it
- [x] Result (seed 42): 2–6 wallets per multi-benefit company; approval 87.5%; 53 checks, 17 tables

### ST-08.6 — Speed and volume (2026-11-01, ADR-016)

- [x] Validators look rows up through an indexed `Table`; balances move in place: `simulate` about 30× faster, same data
- [x] `data_volumes`: 200 companies, 2,000 establishments, 3,000 terminals
- [x] Result (seed 42): all four segments, 9.4k cardholders, 376k attempts in about 35 s, approval 86.9%, 44 MB of Parquet

### ST-08.7 — Calibration (2026-11-01, ADR-017)

- [x] Attempts mostly go to shops that take the wallet (`known_acceptance_ratio`); near home only where a terminal works
- [x] Spenders try 100–150% of the credit; 30% give up after a balance decline
- [x] Result (three seeds): approval 86–87%, lack of balance over half the declines, PREMIUM about 80% approved

### ST-08.8 — Audit fixes (2026-11-01)

- [x] The routing skips wallets not activated yet; attempts start at the wallet's activation (11 thousand approvals came before it)
- [x] Off-pattern attempts of proprietary-network cards never go to a cash machine (they can't withdraw)
- [x] `balance_history.sequence_number` / `fact_balance_movements.sequence_number`: the order of the movements, so two at the same second chain correctly; the ledger checks use it

### ST-08.9 — Day first, then the terminal (2026-11-02)

- [x] An attempt draws its day first, then a terminal installed by that day (`TransactionGenerator._terminal`). Before, the terminal came first and pushed the day past its installation: terminals installed in the window piled extra attempts on the last months, and on a year the approval fell from 89% to 84%. Now it holds at 86–87% every month
- [x] A branch is registered after its holding (83 were before)
- [x] Faster on a year (2.5 million attempts): the day is drawn by bisection over cumulative weights, pools keep cumulative weights, the validators get `Table`s, the CNAE acceptance is memoized, attempts are answered in place. Generation and answers take about 1.5 minutes instead of 5

### ST-08.10 — Status over time, the week per category, the first credit (2026-11-02)

- [x] `status_since` on cardholders, cards, card wallets, establishments and terminals: the day the current status began; before it the record was active (`fake.status_since`; a day since the record's start, leaning to early in its life since ST-08.12). A card never unlocked is inactive since its issue. Validators, credits and the attempt rates follow the status of the day; new quality check "approved attempts only on records active that day". Before, a card blocked today was blocked the whole year
- [x] `weekday_weights_by_category`: meals on workdays, groceries on Saturday, fuel before the weekend; the default week no longer peaks on Monday
- [x] A wallet activated in the window starts empty and gets its first credit, pro rata to the days left in the month, on the activation day. New cards approved 65% of their first month; now about 83%
- [x] Dictionary: the segment is the employer's size; the dataset holds a sample of its cardholders
- [x] `copy_dataframe` sends Polars CSV to `COPY`. The write still takes about 2 minutes on a year: the foreign-key checks of 4.7 million rows
- [x] Fixed in ST-08.12: the first month approves more (90%, the starting balance plus the credit); afterwards the approval eases from 87% to 85% over the year, as records that stopped being active pile up toward the end (no record comes back to active)

### ST-08.11 — Seasonality (2026-11-03)

- [x] `src/data_generators/providers/seasons.py`: national holidays (fixed, and Carnival, Good Friday and Corpus Christi from Easter), their eves, Christmas Eve, New Year's Eve, Black Friday; `usage_patterns.seasonality` weighs each per category, plus a weight per month. A holiday takes the category's Saturday times its weight
- [x] `simulation.year_end_credit`: a third of the employers (`company_share`) add a one-off credit to the FOOD wallet on 10 December, spent over the next 30 days; the generator adds the attempts it pays for
- [x] Result (seed 42, a year): December about 12% more attempts and 8% more approved BRL than November, January the quietest; on a holiday 1.0–1.6× the attempts of the same weekday, BRL up to 2×; Christmas Day spends less (Christmas Eve takes it: supermarkets +50%); Black Friday doubles retail


### ST-08.12 — Monthly approval varies, no drift (2026-11-03)

- [x] Each month of the window draws an intensity (`seasonality.month_noise_sigma`): some months spend more and approve less
- [x] Opening balance in line with the cardholder's spending (`TransactionGenerator.opening_balances`, `usage_patterns.opening_balance`): a spender keeps 10–40% of a credit from past months, a saver what built up over up to 12 months. Before, every wallet started with 0–100% of a credit, so the first month approved about 90% and the cushion drained over the year
- [x] `status_since` leans to early in a record's life (`status_since_skew`; the 30- and 180-day caps are gone): records out of use no longer pile up toward the end of the window
- [x] Spenders spend 1.00–1.35× their credit (was 1.50)
- [x] Result (a year, seeds 42, 7, 3): months between 85% and 90% approved, up and down with no trend; December below the average (more attempts)
---

## EP-09 — OLAP: Postgres → DuckDB

**Dependencies:** `EP-08`. **Size:** M (~2–3 days).

- [x] Plain SQL on DuckDB, no dbt (ADR-012); full refresh into a new file
- [x] ETL from OLTP into `dim_*`, `fact_transactions` and `fact_balance_movements` (`src/pipeline/etl.py`, `03_load.sql`); `python -m src.main etl`
- [x] Model: `dim_card_wallets` (credit, limits, final balance); `fact_balance_movements`; the fact gains `company_id`, `modality_id`, `acquirer_id`, `card_wallet_id`; no CPF or card number hashes
- [x] Views (`04_views.sql`): approval by program and network, declines by code and reason, ticket by category, fraud by scenario, daily volume, wallet flows by month
- [x] Tests: loads, keys resolve, denormalized keys agree, sums match, views; `pytest -m db` runs setup → simulate → etl
- [x] Found on the way and fixed in `ST-08.4`: wallets spent only 20–45% of their monthly credit

---

## EP-10 — Dataset export and quality

**Dependencies:** `EP-09`. **Size:** S (~1 day).

- [x] `python -m src.main export` (`src/pipeline/export.py`): one Parquet file per table in `data/final_datasets/` (zstd)
- [x] Quality checks, 49 with seed 42: unique ids, every key resolves, answers consistent (authorization, reasons, disputes, fraud labels, reversals), the balance ledger holds, approval and fraud rates in range, no personal documents; a failure writes nothing
- [x] Data dictionary (`database/olap_duck/dictionary.yaml`, one line per column) rendered to `data_dictionary.md` and `docs/data-dictionary.md`; tests keep both complete and current
- [x] Public tables without CNPJ, CPF, card number or cardholder name (ADR-014); acceptance rules and ISO codes exported as `ref_*` tables
- [x] Tests: dictionary coverage, checks on simulated data, export writes every table, a broken dataset is refused, rates are checked

---

## EP-11 — Kaggle release

**Dependencies:** `EP-10`, `EP-12`, `EP-13`. **Size:** S (~1 day).

- [ ] Dataset page (description, benefits-market context, license)
- [ ] Example notebook
- [ ] Publish and link from the README

---

## EP-12 — Architecture review: a coherent dataset at volume

**Dependencies:** `EP-10`. **Size:** M (~2 days). Review of 2026-11-03.

**Goal:** not random rows but a statistically coherent dataset: relationships that hold, distributions that look like the market, business rules followed everywhere, reproducible, at a volume that tests dashboards, metrics and data pipelines.

### ST-12.1 — Dead code
- [x] Removed `infrastructure/schema/schema_creator.py`, `infrastructure/database/duckdb_manager.py`, `utils/csv_utils.py`, `utils/parquet_utils.py`, the loaders used only by tests (`capture_technologies`, `segment`), the unused `segments` list and the unused keys of `config/database.yaml`

### ST-12.2 — Reproducible dataset
- [x] The export writes `dataset_metadata.json`: seed, reference day, window, code commit (`-dirty` with local changes), config hash, source hashes, row counts (`src/pipeline/provenance.py`, OLTP table `run_metadata`, carried by the ETL)
- [x] Public sources pinned: the `data/raw/*.parquet` files are versioned in git (about 200 KB, public data); delete one to download a newer version

### ST-12.3 — One acceptance rule
- [x] `src/domain/acceptance.py` answers "which wallets does this establishment take on this network", for the generator (from the config) and the issuer (from the reference tables); inactive rules count in both; `OPEN_WALLET` defined once; a test checks both read the same rule for every CNAE and MCC

### ST-12.4 — One schema contract
- [x] Tests keep the DBML files in line with the SQL schemas (`tests/test_dbml.py`: same tables, same columns in the same order)
- [x] `setup --reset` drops and recreates the tables, so a schema change needs no `docker compose down -v`

### ST-12.5 — CI runs the pipeline
- [x] CI starts Postgres 18 as a service, runs the `db` tests, then setup → simulate (30 days) → etl → export with the quality checks (about 25 s locally); first run on GitHub after the first push

### ST-12.6 — Structure
- [x] `src/simulation/`: `generator.py` (attempts) composes `seasons.Calendar` (days), `pools.TerminalPools` (where) and `demand.Demand` (who, how often, opening balances); fraud, simulator, balance and disputes move there from `data_generators/entities` and `processors/`
- [x] `src/domain/` holds the rules both sides share: `acceptance.py`, `status.py`; `Table` moves to `src/utils/table.py`; validator modules all `*_validators.py`
- [x] Config read once per file, from `config/` or the folder `python -m src.main --config DIR` names (a variant of the rules); `run_metadata.config_dir` records it. Modules still read it when imported, so one process runs one config: enough for runs, and a test of another config runs in a subprocess

### ST-12.7 — Volume
- [x] Simulate month by month: the generator plans every attempt as three small indexes (slot, kind of place, day; `TransactionGenerator.plan`), then each month is built, answered (`TransactionSimulator.start` / `advance`, balances and pending reversals carried over) and written. A year at scale 1: peak memory 6 GB → 1.6 GB
- [x] `setup --scale N` multiplies companies (so cardholders), establishments and terminals; `run_metadata.data_volumes` records them
- [x] `bulk_load`: foreign keys and secondary indexes of `transactions` and `balance_history` dropped during the load and built back at the end, in the same transaction. A year at scale 1: `simulate` 5.5 min → 2.4 min
- [x] `etl` copies `transactions` and `balance_history` to DuckDB in chunks (`read_chunks`, server-side cursor), with column types from the database; a year at scale 4 needed 7 GB before
- [x] Found at scale 4: with more than 100 holdings, Polars guessed `parent_id` from the first rows (all empty) and failed; fixed, with a test
- [x] Result: a year at scale 4, 5.7 million transactions, `simulate` 7 min and 2.9 GB, every check passed

### ST-12.8 — Statistical profile
- [x] `src/pipeline/profile.py`: monthly approval (each month), median ticket per kind of place, restaurant peak hour and weekend dip, the share of declines for balance, reversals, purchases in the cardholder's state, the busiest fifth of the shops, the Christmas Eve lift; each against `quality_profile` in the config. The export fails when one is off and writes the profile into `quality_report.md` (70 checks on a full dataset)

---

## EP-13 — Layout and developer infrastructure

**Dependencies:** `EP-12`. **Size:** S (~half a day). Review of 2026-11-03: folders three and four levels deep holding one or two files, the reference tables built in two places, generated files next to the SQL, personal editor settings in git, long commands to remember.

Found on the way: `src/adapters/`, an empty folder left by an old commit.

### ST-13.1 — A flat source layout
- [x] Packages only where there are several modules: `entities/` (generators, `fake`, `brazil`), `sources/` (IBGE and MCC downloads), `simulation/`, `validators/`, `domain/`, `pipeline/` (the commands); single modules at the top: `config.py`, `postgres.py`, `reference.py`, `table.py`, `main.py`
- [x] The reference tables built in one module (`reference.py`), not five loaders plus a builder
- [x] Every package with an `__init__.py`

### ST-13.2 — Config files by purpose
- [x] `reference.yaml` (wallets, programs, networks, acquirers, acceptance rules, response codes, capture technologies), `authorization.yaml` (the issuer's checks and their order), `simulation.yaml` (volumes, behaviour, calendar, fraud, profile), `database.yaml`

### ST-13.3 — Data folders
- [x] `database/` keeps only schemas and SQL; `data/raw/` (inputs), `data/olap/` (the DuckDB file), `data/dataset/` (the export)

### ST-13.4 — Developer infrastructure
- [x] `make` targets: `db`, `test`, `dataset` (with `SCALE`, `DAYS`, `SEED`, `TODAY`), `clean`; a `benefits` console command
- [x] Docker: defaults for the credentials (no `.env` needed to start), restart only when asked (not at every boot)
- [x] Personal editor settings out of git

### ST-13.5 — Architecture docs
- [x] `docs/technical-architecture.md` describes the layout and the data flow as they are; ADR-019 records the layout

### ST-13.7 — Branches and releases (2026-11-03)
- [x] Releases by hand, one per published dataset version: `CHANGELOG.md`, the version in `pyproject.toml`, a signed tag and a GitHub Release (`docs/runbooks/releases.md`); `v1.0.0` is the first
- [x] CI also on pull requests and by hand, with a timeout
- [x] Left out on purpose, for a data project with one author and no deploy: Dependabot (removed), automated releases, required pull requests; GitHub's own secret scanning replaces a gitleaks job
- [ ] GitHub settings applied by hand: a `main` ruleset (no deletion, no force push), secret scanning with push protection, topics

### ST-13.6 — README and portfolio page (2026-11-03)
- [x] README in the Best-README-Template layout: badges, table of contents, usage, architecture, data sources, roadmap, contributing, contact
- [x] `.portfolio/` for the portfolio site: `project.json`, content in English, Portuguese and Spanish, charts drawn from the official dataset and diagrams from Mermaid (`*.mmd` next to each `.svg`); checked with the portfolio's own ingestion. The repository needs the `portfolio` topic on GitHub

