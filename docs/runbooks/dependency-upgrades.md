# Runbook — Dependency upgrades

Guide for keeping Python and the dependencies of this repository up to date.
`pyproject.toml` holds the version ranges; `uv.lock` pins the exact versions
of every package, transitive ones included. `.python-version` pins the
interpreter `uv` uses.

---

## 1. See what's outdated

```bash
uv tree --outdated --depth 1
```

Lists the direct dependencies with `(latest: vX)` next to the ones that have
a newer release. Drop `--depth 1` to include transitive packages.

## 2. Upgrade inside the declared ranges

```bash
uv lock --upgrade          # every package
uv lock --upgrade-package polars   # one package
uv sync
```

Only `uv.lock` changes. Use this for minor and patch releases.

## 3. Upgrade past a declared range (major bumps)

```bash
uv add "mimesis>=22.2"
```

Rewrites the range in `pyproject.toml` and the lock in one step. Before
doing it, read the package's changelog for the versions being skipped and
grep the code for every removed or renamed API.

## 4. Verify

1. Every module still imports — run from outside the repo so nothing resolves
   by accident through the working directory:

   ```bash
   cd /tmp && uv run --project <repo> python -c "import src.<module>"
   ```

2. `uv run pytest` (once `EP-02` adds the configuration).
3. Run the generators touched by the upgrade and look at the output.

## 5. Upgrade Python

1. Change `.python-version` and `requires-python` in `pyproject.toml`.
2. `uv sync` — `uv` downloads the interpreter if it isn't installed.
3. If a package has no wheel for the new version, `uv sync` falls back to a
   source build and fails without the native toolchain (`psycopg[binary]`,
   `duckdb`, `polars`). Wait for the wheel or stay on the previous version.

## 6. Commit

`pyproject.toml`, `uv.lock` and, if changed, `.python-version` go in one
`chore(deps): …` commit. Breaking changes and code migrations are described
in the commit body.

---

## Upgrade log

| Date | Change | Notes |
|---|---|---|
| 2026-10-30 | Moved to `uv`; all packages to the latest release | `mimesis` 18 → 22: `mimesis.builtins` was removed in 19, so `BrazilSpecProvider` was ported to `src/entities/brazil_provider.py` (same output for the same seed). 20 rewrote `SchemaBuilder` and 21 removed `Person.political_views/worldview/views_on`, `Datetime.century`, `Payment.paypal`, `Science.measure_unit/metric_prefix`, `Internet.stock_image_url` — none used here |
