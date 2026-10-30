# ADR-005 — Python 3.14, uv, ruff and pytest

## Status
Accepted (2026-10-30; roadmap `EP-01`, `EP-02`)

## Context
The project had an unpinned `requirements.txt` missing half of what the code
imported, no lint, no CI and print-scripts for tests.

## Decision
- **Python 3.14** (`.python-version`, `requires-python = ">=3.14"`).
- **uv** with `pyproject.toml` and a committed `uv.lock`; the project is
  installed as a package (no `sys.path` hacks).
- **ruff** for lint (`E`, `F`, `I`, `UP`, `B`, line length 100) and format.
- **pytest**, with `network` and `db` markers left out of the default run.
- **GitHub Actions** runs `ruff check`, `ruff format --check` and `pytest`;
  **Dependabot** watches uv, Actions and the Postgres image.

## Consequences
- `uv sync` reproduces the environment exactly.
- Upgrades follow `docs/runbooks/dependency-upgrades.md`, which logs breaking
  changes (e.g. mimesis 19 removed `mimesis.builtins`).
