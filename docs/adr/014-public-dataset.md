# ADR-014 — The public dataset: no documents, and a quality gate

## Status
Accepted (2026-11-01; roadmap `EP-10`).

## Context
The dataset goes public. The generators make valid CPF, CNPJ and card
numbers, and full names: a generated CNPJ can be a real company's, a name a
real person's. A dataset that breaks its own rules (a dangling key, a balance
that doesn't add up) misleads everyone who uses it.

## Decision
- **No documents or personal names in the public tables.** The OLAP drops
  CNPJ, CPF and card number (even hashed) and the cardholder's name; ids
  identify. Company and shop names stay: built from surnames and activity,
  they carry no document. The OLTP keeps everything, locally.
- **Rules travel with the data.** The acceptance rules (`ref_cnae_wallets`,
  `ref_mcc_wallets`, `ref_mcc_modalities`) and the ISO codes ship as
  reference tables, marked synthetic where they are.
- **A quality gate.** `export` runs the checks (unique ids, keys, answers,
  ledger, rates, no documents) and writes nothing if one fails.
- **A dictionary under test.** `dictionary.yaml` describes every column; a
  test fails when a column has no line, and the copy in `docs/` must match.

## Consequences
- Dataset users get 16 tables, a dictionary and the report of the checks.
- Adding an OLAP column means a dictionary line, or the tests fail.
