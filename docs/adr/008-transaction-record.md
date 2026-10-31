# ADR-008 — The transaction record: card wallet, response codes, one table

## Status
Accepted (2026-10-31; roadmap `ST-06.4`). Refines [ADR-007](007-transaction-core-model.md).

## Context
After ADR-007, three parts of the transaction record were loose:

- `transactions.wallet_id` pointed at the wallet type (`MEAL`), not at the
  card's balance that was charged; the card wallet had to be found again from
  `card_id` + `wallet_id`.
- The ISO response codes lived only in the config, and every transaction
  repeated the code's message.
- `authorizations` was one row per transaction, repeating its date and result.

## Decision
- `transactions.card_wallet_id` references `card_wallets`. The validators,
  `route_wallet` and `balance.debit` work on it; the wallet type is one join away.
- A `response_codes` table holds the ISO 8583 codes;
  `transactions.response_code` references it and `response_message` goes.
- `authorizations` is merged into `transactions`: `nsu` (the terminal's
  sequence number, every attempt) and `authorization_code` (approvals only).

## Consequences
- Still 17 OLTP tables: `response_codes` in, `authorizations` out.
- The fact table is unchanged for users except two dropped columns
  (`authorization_datetime`, `authorization_status`) that repeated `date` and
  `response_code`; the ETL fills `wallet_id` from the card wallet and
  `response_message` from `response_codes`.
