# ADR-002 — Polars instead of pandas

## Status
Accepted (retroactive, recorded 2026-10-30)

## Context
The generators and loaders were written with Polars, but the validators were
written with pandas syntax (`.empty`, `.iloc`) on Polars frames and never ran.
pandas was also pulled in indirectly through `geopandas`.

## Decision
Polars is the only DataFrame library. Code is migrated to Polars, not the
other way around (`ST-03.1`). Row lookups use `df.filter(**match)` and
`row(0, named=True)` (`src/validators/_common.py → find_one`).

## Consequences
- pandas and `geopandas` left the dependencies (`ST-03.3`).
- Polars operations that don't keep row order or use their own randomness
  must be pinned for reproducibility: `unique(maintain_order=True)` and
  `sample(seed=…)` drawn from the shared seed.
