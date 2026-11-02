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
| Metadata | `dataset-metadata.json`: the fields above plus a description of every file and column, from `database/olap/dictionary.yaml`. Kaggle applies the file and column descriptions only with a new version (`datasets metadata --update` ignores them) |
| Dataset | https://www.kaggle.com/datasets/nicolasssoares/brazilian-benefit-card-transactions-synthetic |
| Notebook URL | https://www.kaggle.com/code/nicolasssoares/getting-started-brazilian-benefit-card-transactio |

## A new version

1. Build the data from the release commit: `make dataset SCALE=4`.
2. Put the files of `data/dataset/` (not `.gitkeep`) in a folder with `dataset-metadata.json`, and upload them with the release tag as the note. The Kaggle CLI needs `six` on Python 3.14 and a token in `~/.kaggle/access_token`:

   ```bash
   uvx --with six kaggle datasets version -p <folder> -m "vX.Y.Z"
   ```

   `datasets version` keeps the privacy and the license. Avoid `datasets metadata --update` without `isPrivate`: a missing field makes the dataset public.
3. Re-run the notebook on the new version.
