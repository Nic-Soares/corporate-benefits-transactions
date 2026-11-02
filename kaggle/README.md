# Kaggle release

What goes on the Kaggle dataset page, and how to publish a new version.

| Field | Value |
|---|---|
| Title | Brazilian Benefit-Card Transactions (Synthetic) |
| Subtitle | 5.7M benefit-card purchases answered by a simulated issuer, with fraud labels |
| URL slug | `brazilian-benefit-card-transactions` |
| Cover image | `cover.png` (1600 × 800) |
| Description | `dataset-description.md` |
| License | CC BY 4.0 |
| Tags | finance, banking, tabular, time series analysis, fraud detection, brazil |
| Files | everything in `data/dataset/` except `.gitkeep` (17 Parquet, `data_dictionary.md`, `quality_report.md`, `dataset_metadata.json`) |
| Notebook | `getting-started.ipynb`, attached to the dataset |

## A new version

1. Build the data from the release commit: `make dataset SCALE=4`.
2. On the dataset page → **New Version** → upload the files of `data/dataset/`, with the release tag (`vX.Y.Z`) as the version note.
3. Re-run the notebook on the new version.
