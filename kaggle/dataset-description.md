## Context

In Brazil, employers give employees benefit cards — meal (*refeição*), food (*alimentação*), mobility, multi-benefit, incentive — whose balances can only be spent on certain things. A card belongs to a **program** that fixes its **wallets** (one balance each) and its network: the issuer's **proprietary network**, where the shop's CNAE (economic activity code) decides which wallet it accepts, or a **brand** (Visa, Mastercard, Elo), where the MCC decides. Each wallet is credited every month and spent until it runs out.

Real transaction data from this market isn't public. This dataset is **synthetic**: no row is real. But every row went through what a real one goes through — a simulated issuer checks the card, the cardholder, the shop, the terminal, the PIN, which wallet the shop accepts and whether there is balance, then approves or declines with an ISO 8583 response code and a specific reason. The result behaves like the market: relationships that hold, distributions that look right, business rules followed everywhere.

## Content

One simulated year, **September 2025 to August 2026**, as a star schema in Parquet:

| File | Rows | What it holds |
|---|---:|---|
| `fact_transactions.parquet` | 5,689,874 | Every purchase, withdrawal or reversal attempt and the issuer's answer |
| `fact_balance_movements.parquet` | 5,608,434 | The ledger: monthly credits, debits and reversals, chained per wallet |
| `dim_card_wallets.parquet` | 79,517 | Each wallet of each card: monthly credit, limits, final balance |
| `dim_cards.parquet` | 45,847 | Cards: program, network, physical or virtual |
| `dim_cardholders.parquet` | 34,432 | Employees: employer, municipality, admission |
| `dim_companies.parquet` | 800 | Employers by segment (SME, Middle, Corporate, Public) and their branches |
| `dim_establishments.parquet` | 8,000 | Shops, online businesses and cash machines: category, CNAE, MCC, municipality |
| `dim_terminals.parquet` | 12,000 | POS, TEF, e-commerce gateways and ATMs, with their acquirer |
| `dim_wallets`, `dim_card_programs`, `dim_transaction_modalities`, `dim_acquirers` | small | The catalogues |
| `ref_response_codes`, `ref_program_wallets`, `ref_cnae_wallets`, `ref_mcc_wallets`, `ref_mcc_modalities` | small | The rules behind each answer: codes, which wallets a program holds, which wallet a CNAE or MCC accepts, which brand accepts an MCC |

Also included: `data_dictionary.md` (every column described), `quality_report.md` (the checks the data passed) and `dataset_metadata.json` (seed, window, code version, row counts).

Key columns of `fact_transactions`: `amount` (BRL), `date`, `response_code` (`00` = approved), `decline_reason` (e.g. `insufficient_balance`, `wallet_not_accepted_at_cnae`, `wrong_pin`), `wallet_id` (the wallet the issuer charged), `capture_type`, `is_fraud`, `fraud_scenario` and `disputed`. The ids join every table; there is no CPF, CNPJ, card number or person name.

## What the data looks like

- **85–90% approved each month**, varying with no trend; about half the declines are for lack of balance.
- **Spending follows the credit:** most cardholders spend their whole monthly benefit, a few let it build up; the credit lands on the 1st and spending jumps that day.
- **Time:** restaurants peak at lunch and dip on weekends, supermarkets peak on Saturday, fuel before and after work; national holidays, Christmas Eve and Black Friday move the volume; one company in three gives a year-end credit in December.
- **Place:** real IBGE municipalities; companies where the economy is, shops where people live; most in-person purchases in the cardholder's state.
- **Fraud (~0.5%)** labelled by scenario — mobile wallet after an account takeover, card not present, card intercepted before delivery, skimming at a point of compromise — and **disputes**, including legit purchases contested by mistake: `is_fraud` is the truth, `disputed` is what an issuer would see.

## How it was made

An open-source pipeline (Python, Polars, PostgreSQL, DuckDB) generates the world, simulates the attempts month by month in time order — balances move, daily limits count, reversals come later — and exports only if 83 quality checks and a statistical profile pass. The same seed reproduces the same dataset: [github.com/Nic-Soares/corporate-benefits-transactions](https://github.com/Nic-Soares/corporate-benefits-transactions).

The reference data is public — IBGE (CNAE, municipalities, population, municipal GDP) and the public MCC list. Every weight, balance, limit, ticket and acceptance rule is synthetic, shaped after how the Brazilian benefits market works, not taken from any company's data.

## Limitations

- **Synthetic rates.** Approval, decline mix, tickets and fraud share have a realistic shape but are not statistics of the real market; don't draw conclusions about it from them.
- **Snapshot dimensions.** Each record carries its current status and the day it began (`status_since`; active before that day), not a full history of changes.
- **One fact for attempts and reversals.** Reversals are rows of `fact_transactions` with `transaction_type = 'reversal'`, pointing to the purchase they undo; filter them out for attempt-level rates.
- **Simplified world.** Acceptance rules, fraud scenarios and the calendar follow how the market works in broad strokes; acquirer integrations, chargebacks, fees and settlement are out of scope.

## Ideas

- Predict declines (and which reason) from the attempt alone
- Fraud detection with label noise: train on `disputed`, evaluate on `is_fraud`
- Spending and seasonality by category, segment or state
- Data engineering: incremental loads, slowly changing dimensions (`status_since`), ledger reconciliation, dashboards

## License and citation

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use it for anything, including commercially, crediting:

> Nicolas Santos, *Brazilian Benefit-Card Transactions (synthetic)*, v1.0.0, 2026. https://github.com/Nic-Soares/corporate-benefits-transactions
