import polars as pl

from src.extractors.kaggle_downloader import download_kaggle_dataset
from src.extractors.mcc_extractor import fetch_mcc_codes
from src.utils.read_yamls import CONFIG_DIR

RAW_DIR = CONFIG_DIR.parent / "data" / "raw"


def extract_cnae_data() -> pl.DataFrame:
    download_kaggle_dataset("diovanimerlo/cnae-brazil-2024")

    cnaes = pl.read_csv(
        RAW_DIR / "cnae_dataset_2024.csv",
        separator=",",
        encoding="utf8",
        schema_overrides={
            "secao_id": pl.Utf8,
            "secao": pl.Categorical,
            "divisao_id": pl.Utf8,
            "divisao": pl.Categorical,
            "grupo_id": pl.Utf8,
            "grupo": pl.Categorical,
            "classe_id": pl.Utf8,
            "classe": pl.Categorical,
            "subclasse_id": pl.Utf8,
            "subclasse": pl.Categorical,
        },
    )
    return cnaes


def extract_mcc_data() -> pl.DataFrame:
    """
    MCCs from the public list, with the brands that accept each one.

    Returns:
        pl.DataFrame: columns mcc_code, description, valid_payment_brands
            (from `validation_rules.yaml → mcc_acceptance_rules`)
    """
    from src.utils.read_yamls import load_validation_rules

    df = fetch_mcc_codes()

    validation_rules = load_validation_rules()
    mcc_acceptance_rules = validation_rules.get("mcc_acceptance_rules", {})

    df_processed = df.select(
        [pl.col("mcc").alias("mcc_code"), pl.col("irs_description").alias("description")]
    )

    # One MCC per description: the lowest
    df_processed = (
        df_processed.sort("mcc_code").unique(
            subset=["description"], keep="first", maintain_order=True
        )  # keep the lowest MCC per description
    )

    df_processed = df_processed.with_columns(
        [
            pl.col("mcc_code")
            .map_elements(lambda x: mcc_acceptance_rules.get(x, ""), return_dtype=pl.Utf8)
            .alias("valid_payment_brands")
        ]
    )

    df_processed = df_processed.with_columns(
        [
            pl.col("mcc_code").cast(pl.Utf8),
            pl.col("description").cast(pl.Utf8),
            pl.col("valid_payment_brands").cast(pl.Utf8),
        ]
    )

    return df_processed
