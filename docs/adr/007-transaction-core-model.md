# ADR-007 — The transaction core: programs, wallets, networks and ISO codes

## Status
Accepted (2026-10-30; roadmap `EP-06`). Refines [ADR-003](003-network-routing-mcc-cnae.md). The transaction record is refined by [ADR-008](008-transaction-record.md).

## Context
The first model had six "products" (`VA, VR, VC, VF, VM, PR`) on a card, each
card drew its network at random, a transaction sampled a random product, the
balance never changed, and the response codes were the project's own.
Reviewed against how a Brazilian benefits issuer works, four things were off:

- A card isn't a bag of products. It belongs to a **program** that fixes its
  **wallets** (*carteiras*) and its network. "Multi-benefit" is a program with
  several wallets, not a wallet.
- On the issuer's own network (3-party) the cardholder picks the wallet on the
  terminal; on a brand network (4-party) the issuer picks it from the MCC.
- A purchase spends the balance, so later purchases can fail for lack of it.
- Terminals and acquirers speak ISO 8583; one code covers several causes.

## Decision
- **Programs and wallets.** `wallets` (8) replace `products`; `card_programs`
  (7) and `card_program_wallets` say which wallets each program holds;
  `cards.program_id` is required and `card_wallets` (one per wallet of the
  program) replaces `card_products`.
- **Network from the program.** 3-party programs run on `OWN`; the 4-party
  multi-benefit program runs on Visa, Mastercard or Elo. `cards.modality_id`
  is never null.
- **Wallet choice.** 3-party: the transaction carries the cardholder's choice
  and `cnae_wallets` (longest prefix) checks it. 4-party: the brand must accept
  the MCC (`mcc_modalities`), then `route_wallet` takes the first wallet in
  `wallet_priority` that the card holds, is active, accepts the MCC
  (`mcc_wallets`; GIFT takes any) and has the balance.
- **Balance follows the transactions.** Wallets start with a synthetic balance;
  an approved purchase debits it and writes `balance_history`. Where balances
  come from (employer credit orders) is out of scope.
- **ISO 8583 codes plus a reason.** Validators return the ISO response code and
  a `decline_reason` (`card_blocked`, `wallet_not_accepted_at_cnae`,
  `wrong_pin`…), stored in `transactions`. A PIN check (`55`) joins, fed by
  `transactions.pin_status`.

## Consequences
- 17 OLTP tables (was 14) and 10 OLAP tables (`dim_wallets`,
  `dim_card_programs`); the fact carries `program_id`, `wallet_id`,
  `pin_status`, `decline_reason`.
- Dataset users can study declines by code and by cause, per program and
  network.
- Out of scope, by decision: fees and establishment payments, the employer
  side, wallet-to-wallet transfers. Daily transaction counts, reversals, usage
  patterns and company size move to the simulator (`EP-08`).
