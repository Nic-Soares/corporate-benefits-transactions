# ADR-016 — Indexed lookups in the simulator; a bigger dataset

## Status
Accepted (2026-11-01; roadmap `ST-08.6`). Refines [ADR-010](010-simulation-over-time.md).

## Context
The first dataset had 30 companies (no Corporate or Public client by
chance), about a thousand cardholders and 44 thousand attempts. A profile of
`simulate` showed 86 of its 103 seconds in Polars filters: every validator
looked its row up by filtering a whole table, about 1.2 million times, and
every balance movement rebuilt the card wallets. The cost grows with
attempts × table size, so five times the volume would take over half an hour.

## Decision
- **`Table`** (`src/validators/_common.py`): the rows of a DataFrame as
  dicts, with a hash index per set of lookup columns, built on first use.
  `find_one` and `find_all` take a DataFrame (its Table is built once and
  cached) or a Table, so the validators and their tests keep their signatures.
- **Balances in place.** The simulator holds the card wallets as a Table and
  `src/processors/balance.py` changes `current_balance` on the row; the
  final DataFrame is built once at the end.
- **Volume** (`data_volumes`): 200 companies, 2,000 establishments, 3,000
  terminals; `cardholder_scale` stays at 0.1.

## Consequences
- Same seed, same data: the 44-thousand run gives identical results, in 3
  seconds instead of about 100. The offline tests run in 2 seconds instead of 8.
- With seed 42 the setup makes all four segments (11 Corporate, 16 Public),
  9.4 thousand cardholders and 12.5 thousand cards; `simulate` answers 376
  thousand attempts in about 35 seconds; the export (53 checks) writes 44 MB.
- Rows of a Table are shared: code that changes one changes what every
  lookup returns, which is the point for balances and a trap anywhere else.
