# ADR-017 — Calibration: shops that take the wallet, demand above the credit

## Status
Accepted (2026-11-01; roadmap `ST-08.7`). Refines [ADR-013](013-spending-follows-credit.md).

## Context
At the bigger volume ([ADR-016](016-indexed-lookups-and-volume.md)) three
things looked off:
- The cardholder picked a shop by kind of place only, not by whether it takes
  the wallet: the PREMIUM program was approved about half the time, since only
  some supermarket and health CNAEs accept it.
- Near home meant the shop pool of the cardholder's city even when every shop
  there was closed: in small towns the only supermarket could be inactive, so
  "establishment inactive" was a sixth of the declines.
- Once those were fixed, approval went above 90% with lack of balance a
  third of the declines. In the benefits market the lack of balance is by far
  the main decline, and the proprietary network approves less than the brands
  (no open wallet to fall back on).

## Decision
- **Known acceptance.** Most attempts (`known_acceptance_ratio`, 0.9) go to a
  shop that takes the wallet the cardholder means to use: by the CNAE's
  longest prefix on the proprietary network, by MCC (plus GIFT) on a brand.
  The rest try any shop of the kind, as before.
- **Working shops near home.** The city (then state) pool is used only if it
  has a working terminal (active, in an active shop); otherwise the search
  widens.
- **Demand above the credit.** Spenders try to spend 100–150% of the credit
  (`spend_profile.spender`), so the balance runs out before the next credit;
  after a balance decline 30% give up until then (`give_up_after_insufficient_balance`),
  the others try again.

## Consequences
- Seeds 42, 7 and 2026: approval 85.7–86.7%; lack of balance 53–59% of the
  declines; the proprietary network a little below the brands; PREMIUM
  approved about 80% of the time.
- Food and Meal wallets spend about 80% and 90% of the credit over the whole
  dataset (savers and idle cards included).
- The volume grows with the demand: about 530 thousand attempts with seed 42.
