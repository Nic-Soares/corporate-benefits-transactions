# ADR-013 — Spending follows the credit

## Status
Accepted (2026-11-01; roadmap `ST-08.4`). Refines [ADR-009](009-market-shaped-generation.md)
and [ADR-010](010-simulation-over-time.md).

## Context
The OLAP showed Food and Meal wallets spending 20–45% of their monthly
credit, while these benefits are mostly spent within the month. Attempts were
drawn per card with a log-normal activity that ignored the credit: heavy cards
emptied their wallets and got declined, light ones built up balance. Raising
the volume only raised the declines.

## Decision
- **Attempts per wallet.** Each active wallet of a card makes about
  *monthly credit × spending ratio ÷ average ticket where it is used* attempts
  a month; an attempt picks a wallet by that weight, then a kind of place that
  takes it. The volume of a simulation is the sum
  (`expected_attempts`); the fixed attempts per card is gone.
- **Spending profile.** Most cardholders spend 80–100% of the credit; a tenth
  are savers (10–50%) (`usage_patterns.spend_profile`).
- **Giving up per intent.** After a decline for balance the cardholder stops
  trying that option (proprietary network) or kind of place (brand) until the
  next credit, not the whole card.
- **Credit to active cardholders only**, on cards not cancelled; fewer
  inactive and blocked cards in the status weights.

## Consequences
- Active cards spend 74–90% of Food and Meal credits; the whole dataset
  61–75% (savers, suspended wallets and idle cards included). Approval stays
  around 81%.
- The volume grows with the credits: about 10 attempts per active card per
  month (median), with a long tail.
