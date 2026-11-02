# Changelog

## 1.0.0 (2026-11-03)

First public release.

### Features

* A synthetic dataset of Brazilian benefit-card transactions: programs, wallets, the issuer's proprietary network (CNAE) and the brands (MCC), answered by a simulated issuer with ISO 8583 codes and decline reasons
* `setup → simulate → etl → export` (`make dataset`): PostgreSQL as the OLTP model, a DuckDB star schema, Parquet with a data dictionary, a quality report and `dataset_metadata.json`
* Spending that follows each wallet's monthly credit; a calendar of weekdays, national holidays, Christmas Eve and Black Friday; monthly approval that varies between about 85% and 90%; a year-end credit
* Fraud labelled by scenario, and disputes including friendly fraud
* Statuses over time (`status_since`): records were active until their status began
* Reproducible runs: versioned public sources (IBGE, MCC), the seed, the window, the code commit and the config hashes in the metadata
* Volume: month-by-month simulation, `setup --scale N`; a year at scale 4 is 5.7 million transactions
* 83 quality checks and a statistical profile that stop the export when the data breaks its shape
