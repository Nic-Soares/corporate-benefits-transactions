# Development Roadmap — Corporate Benefits Transactions

**Repository:** `corporate-benefits-transactions` (Python 3.14 + uv + polars + mimesis, PostgreSQL in Docker as OLTP, DuckDB as OLAP, Parquet → Kaggle)
**Last updated:** 2026-10-30

---

## 0. Status board

| Epic | Status | Where the work lives |
|---|---|---|
| `EP-01` Baseline and toolchain | ✅ Done — merged into `develop` 2026-10-30 | code (`pyproject.toml`, `docker-compose.yaml`) |
| `EP-02` Safety net (tests + CI) | ✅ Done — merged into `develop` 2026-10-30; CI runs after the first push | code (`tests/`, `.github/`) |
| `EP-03` Clean up existing code | Not started | code (`src/`) |
| `EP-04` Config and model consistency | Not started | `config/`, `database/` |
| `EP-05` Documentation | Not started | `README.md`, `docs/` |
| `EP-06` Setup pipeline (reference data + entities) | Not started | code (`src/main.py`, `src/processors/`) |
| `EP-07` Transaction simulator | Not started | code (`src/processors/transaction_simulator.py`) |
| `EP-08` OLAP: Postgres → DuckDB | Not started | code + `database/olap_duck/` |
| `EP-09` Dataset export and quality | Not started | code + `data/final_datasets/` |
| `EP-10` Kaggle release | Not started | Kaggle |

### Git workflow

- `main` = released code. `develop` = integration; every epic or story is merged into it with a `merge(<scope>): …` commit.
- One branch per epic/story, cut from `develop`: `<type>/ep-XX-<slug>` or `<type>/st-XX.Y-<slug>`, where `<type>` is the conventional-commit type (`feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`).
- Commits follow Conventional Commits (`chore(deps): …`, `docs(roadmap): …`).

---

## 1. Assumptions

1. **Nothing new until the roadmap is settled.** `EP-01` to `EP-05` only refine what already exists (upgrade, clean up, align, document). New code starts in `EP-06`.
2. **Epic order is execution order.** `EP-01` and `EP-02` are prerequisites for everything else: without a pinned toolchain and running tests, the `EP-03` cleanup has no safety net.
3. **Polars is the DataFrame library.** Code still written with pandas syntax (`.empty`, `.iloc`) is migrated, not the other way around (`EP-03`).
4. **`config/*.yaml` is the source of truth for business rules.** Where `docs/` disagrees with the YAML, the docs change (`EP-04`).
5. **The final dataset is synthetic.** No real customer, card, or merchant data enters the repository.

### Decisions (settled 2026-10-30)

- **Language:** everything in English — code, comments, docs, README. Applied in `ST-03.3` (code) and `EP-05` (docs).
- **Package manager:** `uv` + `pyproject.toml` + `uv.lock`. `requirements.txt` goes away (`ST-01.2`).
- **Python:** `>=3.14`.
- **dbt:** removed from the dependencies in `ST-01.2`; whether to adopt it is decided again in `EP-08`.
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
              EP-06 Setup ──► EP-07 Simulator ──► EP-08 OLAP ──► EP-09 Export ──► EP-10 Kaggle
```

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
- [ ] `ruff check` joins CI when `EP-03` brings the findings to zero (115 left after `ST-01.5`)
- [x] Dependabot (`.github/dependabot.yml`): `uv`, GitHub Actions, and the Postgres image in `docker-compose.yaml`, weekly, minor/patch grouped

---

## EP-03 — Clean up existing code

**Dependencies:** `EP-02`. **Size:** M (~2–3 days).

### ST-03.1 — Validators

- [ ] `status_validators.py` reads `validation_rules`, which is never defined or loaded — every function raises `NameError` when called
- [ ] Tests for each validator as it is fixed (approved + declined case), moved here from `ST-02.2`
- [ ] `business_rules_validators.py`: keep one definition of each function, remove loose module-level code
- [ ] Migrate `src/validators/*.py` from pandas syntax to polars
- [ ] Standardize the return value (`{'passed', 'error_code'}`) and align error codes with `pre_populated_data.yaml → response_codes`

### ST-03.2 — Generators

- [ ] `card_generator.py`: `Card` calls `_generate_card_hash`, which doesn't exist — no card can be generated (`test_cards` is xfail)
- [ ] `cardholder_generator.py`: the CPF is generated but `to_dict()` leaves it out
- [ ] Statuses differ between generators: establishments use `ATIVA/INATIVA/SUSPENSA/BAIXADA`, the rest `active/inactive/…` — align with `business_rules.yaml → status_options`
- [ ] Choose between `simple_*_generator` and `*_generator`; delete the other
- [ ] Use `mimesis` everywhere (drop `faker` from `transaction_generator.py`)
- [ ] Configurable seed for every generator (reproducible dataset)

### ST-03.3 — Structure

- [ ] `src/notebooks/`: move what's useful to `scripts/` or a top-level `notebooks/`, delete the rest
- [ ] Rename Portuguese functions, variables, and comments to English
- [ ] Type hints on public functions; replace `typing_extensions.Dict` with `dict`
- [ ] Manual `ruff` findings left over from `ST-01.5` (115 — breakdown in `ST-01.5`)

### ST-03.4 — Broken imports

- [ ] `mcc_and_cnae_loader.py` imports `src.extractors.mastercard_mcc_api` — point it to `src.extractors.mcc_extractor` or restore the module
- [ ] `schema_creator.py` and `tests/test_pg_connection.py` import `src.common.*` — point them to `src.infrastructure.database.*`
- [ ] `ibge_municipalities.py`: the UF comes from the microrregião, which the API leaves null for Boa Esperança do Norte (MT, 2024) — take it from the região imediata instead (`test_every_municipio_has_a_uf` is xfail)
- [ ] `tests/test_imports.py` has no `KNOWN_BROKEN` entries left

---

## EP-04 — Config and model consistency

**Dependencies:** `EP-03`. **Size:** S (~1 day).

### ST-04.1 — Configs

- [ ] `config/database.yaml`: fix the DuckDB SQL paths
- [ ] Products `VA, VR, VC, VF, VM, PR` in every YAML: add `VF`, `VM`, `PR` to `pre_populated_data.yaml`, remove `GF`, update `cnae_products` and `product_acceptance_rules` to match
- [ ] `validation_rules.yaml → validation_order` matches the functions that exist in `src/validators/`
- [ ] YAML comments and keys in English

### ST-04.2 — Data model

- [ ] DBML × SQL: same tables, columns, and types (OLTP and OLAP)
- [ ] Test that creates the OLTP schema on a clean Postgres and the OLAP schema on an in-memory DuckDB

---

## EP-05 — Documentation

**Dependencies:** closes after `EP-04`. **Size:** S (~1 day).

### ST-05.1 — README

- [ ] Rewrite in English
- [ ] "Project structure" and "How to run" written from the real repo (`uv sync`, `docker compose up -d`, `uv run …`)
- [ ] Replace the README roadmap with a link to this file

### ST-05.2 — Retroactive ADRs (`docs/adr/`)

- [ ] `001` — Postgres (OLTP) + DuckDB (OLAP) + Parquet
- [ ] `002` — polars instead of pandas
- [ ] `003` — Authorization by MCC (branded network) × CNAE (proprietary network)
- [ ] `004` — Reference data in YAML
- [ ] `005` — Python toolchain: 3.14 + uv + ruff

### ST-05.3 — Runbooks (`docs/runbooks/`)

- [ ] `dependency-upgrades.md` (written in `ST-01.3`)
- [ ] `local-setup.md` — from clone to a populated database

### ST-05.4 — Business docs

- [ ] `docs/business-rule.md` and `docs/data-strategy.md` aligned with the YAML (product list from §1)
- [ ] `docs/transactions_flow_diagram.mmd` checked against the real flow

---

## EP-06 — Setup pipeline

**Dependencies:** `EP-05`. **Size:** M (~2–3 days).

### ST-06.1 — Reference data

- [ ] `src/processors/load_and_save_reference_data.py` loads every pre-populated table into Postgres
- [ ] Idempotent: running it twice doesn't duplicate rows

### ST-06.2 — Entities

- [ ] Generate companies → cardholders → cards → card products → establishments → terminals, at the volumes in `simulation_config.yaml → data_volumes`
- [ ] Write to Postgres respecting the foreign keys

### ST-06.3 — Entrypoint

- [ ] `src/main.py` with subcommands: `setup`, `simulate`, `export`
- [ ] Progress logging and row counts per table

---

## EP-07 — Transaction simulator

**Dependencies:** `EP-06`. **Size:** L (~1 week).

### ST-07.1 — Authorization flow

- [ ] `transaction_simulator.py`: transaction → validations in `validation_order` → authorization → `balance_history` when approved
- [ ] Branded network checks MCC; proprietary network checks CNAE

### ST-07.2 — Realism

- [ ] Approval rates calibrated from `approval_rates` (overall, per network, per product)
- [ ] Usage patterns from `usage_patterns` (hour, weekday, average ticket per product)
- [ ] Balance and daily/monthly limits respected over time

### ST-07.3 — Fraud scenarios

- [ ] Define the scenarios (e.g. rapid repeated attempts, use outside the usual region)
- [ ] Label transactions generated by these scenarios (a column dataset users can train on)

---

## EP-08 — OLAP: Postgres → DuckDB

**Dependencies:** `EP-07`. **Size:** M (~2–3 days).

- [ ] Decide dbt × plain SQL (ADR)
- [ ] ETL from OLTP into `dim_*` and `fact_transactions`
- [ ] Basic analytical views (approval by product, average ticket, declines by response code)

---

## EP-09 — Dataset export and quality

**Dependencies:** `EP-08`. **Size:** S (~1 day).

- [ ] Export dimensions and facts to `data/final_datasets/*.parquet`
- [ ] Quality checks: foreign keys, nulls, approval rates vs. config
- [ ] Data dictionary (one line per column)

---

## EP-10 — Kaggle release

**Dependencies:** `EP-09`. **Size:** S (~1 day).

- [ ] Dataset page (description, benefits-market context, license)
- [ ] Example notebook
- [ ] Publish and link from the README
