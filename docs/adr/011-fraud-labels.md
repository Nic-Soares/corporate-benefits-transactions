# ADR-011 — Fraud as labeled scenarios, with disputes as a separate signal

## Status
Accepted (2026-11-01; roadmap `ST-08.3`).

## Context
A fraud dataset needs ground truth, and fraud in benefits cards has typical
shapes: account takeover into a mobile wallet, online use of brand cards,
cards intercepted before delivery, skimming at a point of compromise. Most
fraud reaches the issuer as a cardholder contesting a transaction, and not
every contested transaction is fraud.

## Decision
- **Scenarios generate incidents**, not isolated rows: bursts on one card, or
  several cards sharing a skimmed terminal. They go through the same
  validators as legit attempts; fraudsters don't give up after a balance
  decline and pick shops the card works at.
- **Three columns** on `transactions` (and the fact table): `is_fraud`
  (truth), `fraud_scenario` (which typology, NULL when legit), `disputed`
  (what the issuer would see).
- **Disputes are noisy on purpose**: most approved fraud is disputed, card by
  card; a few legit card-and-PIN purchases are disputed too.
- **Volume**: about 0.5% of attempts, above the market's rate, so the
  positives are enough to study. All numbers synthetic.

## Consequences
- Users can train on `is_fraud`, or on `disputed` and meet the label noise.
- Not modeled: blocking the card after a dispute, refunds to the cardholder,
  fraud on the employer or merchant side (out of scope).
