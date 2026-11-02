# ADR-015 — Wallets per company, activation at issue, wallet on balance declines

## Status
Accepted (2026-11-01; roadmap `ST-08.5`). Refines [ADR-009](009-market-shaped-generation.md)
and [ADR-013](013-spending-follows-credit.md).

## Context
A look at the exported data (seed 42) showed four gaps:
- Every multi-benefit card held all seven wallets of its program. In the
  market the employer picks which benefits its employees get.
- Which wallets a program allows lived only in the config; the dataset
  showed it only through the cards.
- A wallet was activated on a day drawn between the card's issue and today,
  so a card issued two years ago could start getting credit last month: the
  credited cards grew a third in three months, and attempts on wallets not yet
  credited were declined for balance.
- Every declined attempt had no wallet, even a decline for balance, where
  the issuer knows which wallet fell short.

## Decision
- **Wallets per company.** For each program, a company draws its set of the
  program's wallets: each with its share (`generation_settings.program_wallet_shares`;
  a wallet not listed always), never empty. Every card of the company on that
  program gets the same set.
- **`ref_program_wallets`** in the OLAP and the export, from
  `card_program_wallets`: the wallets each program allows. A check fails if
  a card holds a wallet its program doesn't allow.
- **Activation at issue.** A card's wallets are activated 0–15 days after its
  issue (`wallet_activation_days`), never after today.
- **Wallet on balance declines.** When no candidate has the balance, the
  routing returns the first candidate as `card_wallet_id`. Declines before
  the routing still have no wallet. A check fails if a balance decline has none.

## Consequences
- With seed 42: multi-benefit companies give 2–6 wallets; the credited cards
  grow about 9% a month, following the issues, instead of 15%.
- Declines for balance drop from 4.1 thousand to 1.0 thousand: most were the
  wallets not yet credited. Approval goes from 82% to 87.5%, inside the export
  range (0.70–0.90). Active cards spend 70% of Food and 74% of Meal.
- Brand cards without GIFT are declined off their wallets' MCCs
  (`no_wallet_for_mcc`), which was rare before.
- Dataset users get 17 tables and 53 checks.
