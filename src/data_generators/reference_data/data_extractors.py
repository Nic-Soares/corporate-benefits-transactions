import polars as pl


def extract_cnae_data():
    from src.extractors.kaggle_downloader import download_kaggle_dataset
    
    download_kaggle_dataset("diovanimerlo/cnae-brazil-2024")

    cnaes = pl.read_csv(
        './data/raw/cnae_dataset_2024.csv',
        separator=',',
        encoding='utf8',
        schema_overrides={
            "secao_id": pl.Utf8,
            "secao": pl.Categorical,
            "divisao_id": pl.Utf8,
            "divisao": pl.Categorical,
            "grupo_id": pl.Utf8,
            "grupo": pl.Categorical,
            "classe_id": pl.Utf8,
            "classse": pl.Categorical,
            "subclasse_id": pl.Utf8,
            "subclasse": pl.Categorical
        }
    )
    return cnaes


def extract_mcc_data():
    mcc = pl.read_csv(
        './data/raw/mcc.csv',
        separator=',',
        encoding='utf-8',
        dtypes={
            "mcc_id": pl.Utf8,
            "mcc_code": pl.Categorical,
            "mcc_description": pl.Utf8,
            "valid_payment_brands": pl.Utf8,
            "category": pl.Categorical
        }
    )
    return mcc