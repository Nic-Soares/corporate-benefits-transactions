# ADR-009 — Market-shaped generation: terminal options, monthly credit, usage patterns

## Status
Accepted (2026-10-31; roadmap `ST-06.5`). Refines [ADR-007](007-transaction-core-model.md).

## Context
The model was checked again against how benefits cards are used in the
market. The tables held; the behavior didn't:

- On the proprietary network the terminal doesn't list every wallet: the
  cardholder picks *Food*, *Meal* or *Others*, and the issuer picks the wallet
  inside *Others*.
- Balances are credited every month; spending follows the credit.
- Usage is uneven: lunch and evening peaks, quiet nights, small tickets with a
  long tail, a few heavy cards, companies of every size. Most declines are for
  lack of balance.
- Brand cards withdraw cash from the gift wallet; Food and Meal cap the
  purchases per day.

## Decision
- **Routing on both networks.** `route_wallet` takes the candidates of the
  option picked on the terminal (proprietary network, `wallet_option`), of
  `wallet_priority` (brand) or of `withdrawal_wallets` (cash), and keeps the
  first one held, active, accepted here (CNAE or MCC) and with the balance.
  The card-wallet status, wallet and CNAE checks fold into it.
- **Monthly credit.** `card_wallets.monthly_credit` lands on
  `benefit_credit_day` as a `credit` row in `balance_history`. The employer's
  order and payment stay out of scope.
- **New columns.** `transactions.transaction_type` (`purchase`,
  `withdrawal`), `transactions.wallet_option`, `card_wallets.daily_count_limit`
  (`65` when exceeded).
- **Generation from the config.** Segments size the companies, program
  bundles give the cards, categories give the establishments (CNAE, then the
  MCC of that CNAE), and `usage_patterns` shapes the attempts. Every number is
  synthetic and rounded: the market informs the shape, not the values.

## Consequences
- Still 17 OLTP and 10 OLAP tables; the fact gains `transaction_type` and
  `wallet_option`.
- A calibration run approves about 86%, with `51` the main decline.
- Reversals, cancellations and buying near home stay in `ST-08.2`.
