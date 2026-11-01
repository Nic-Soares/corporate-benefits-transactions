# ADR-010 — The simulation runs over time, in one ordered stream of events

## Status
Accepted (2026-11-01; roadmap `EP-08`).

## Context
Balances, daily limits and the purchase count per day only mean something in
order: an attempt at 12:05 must see the debit of the one at 12:01, and the
monthly credit must land before the purchases of the 1st. Reversals happen
after their purchase. The generator draws attempts independently, without
knowing balances.

## Decision
- **One stream.** `TransactionSimulator.run` puts the credits (each
  `benefit_credit_day` at 06:00), the attempts and the reversals it schedules
  in a heap ordered by time, and handles one event at a time.
- **The validators are the issuer.** Each attempt runs through
  `validation_order`; the routing sets the card wallet; the first failure
  answers. An approval debits the wallet and counts toward its daily amount,
  daily count and monthly amount, which the limit validators read.
- **Cardholders react.** After a decline for lack of balance, most of that
  card's attempts don't happen until the next credit
  (`give_up_after_insufficient_balance`). Without it, empty cards kept trying
  all month and the approval rate fell to about 72%; with it, about 80%, and
  `51` stays the main decline.
- **Reversals are rows.** A reversal is an approved `transactions` row of type
  `reversal` pointing to its purchase (`related_transaction_id`), with a
  `reversal` movement in `balance_history`.
- **Once per setup.** `simulate` moves balances, so it refuses a database that
  already has transactions; `setup --reset` starts over. It uses the same
  `--today` as `setup` and refuses one before the generated data.

## Consequences
- The ledger checks hold by construction and are tested: each movement starts
  where the previous one ended, nothing goes negative, the final balance is the
  last movement, the daily count limit holds.
- In memory and single-threaded: about 1–2 ms per attempt (7,000 attempts in
  ~10 s). Fine for the dataset sizes planned; a much larger one would need the
  validators to work on dict lookups instead of DataFrame filters.
