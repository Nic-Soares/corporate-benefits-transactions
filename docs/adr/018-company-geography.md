# ADR-018 — Companies where the economy is; staff spread by segment

## Status
Accepted (2026-11-01; roadmap `ST-07.5`). Refines the population weighting of
roadmap `ST-07.4`.

## Context
Companies, cardholders and establishments were all drawn by population, and
80% of every company's cardholders lived in its city. A few Corporate clients
hold most of the cardholders, so the state mix of the transactions followed
wherever those few landed: with seed 42 Bahia had more transactions than São
Paulo, and a Corporate client with hundreds of cardholders could sit in a town
of a few thousand people.

## Decision
- **Companies by municipal GDP** (IBGE aggregates API, table 5938, variable
  37, latest year; `src/extractors/ibge_gdp.py`, cached in `data/raw/`).
  `fake.Municipalities` takes the weight column (`population` by default).
- **Staff spread by segment.** The share of a company's cardholders who live
  in its city is per segment (`company_segments.*.same_city`): SME 90%,
  Middle 70%, Public 60%, Corporate 35%. The others live anywhere, by
  population: a big employer has branches across the country.
- Establishments stay weighted by population: shops follow people.

## Consequences
- Seeds 42 and 7: São Paulo holds 21–24% of the transactions and about
  30% of the companies, then Rio de Janeiro and Minas Gerais.
- The setup downloads one more public source (municipal GDP, about 5,570 rows).
- The test world grew (cardholder scale 0.02 → 0.05): at the smaller size a
  change in the random stream left too few cards for the simulator tests.
