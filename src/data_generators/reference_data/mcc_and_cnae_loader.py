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
    Extrai e processa dados de MCC da API.

    Returns:
        pl.DataFrame: DataFrame com colunas mcc_code, description, valid_payment_brands
    """
    from src.utils.read_yamls import load_validation_rules

    # Buscar dados da API
    df = fetch_mcc_codes()

    # Carregar regras de aceitação do YAML
    validation_rules = load_validation_rules()
    mcc_acceptance_rules = validation_rules.get("mcc_acceptance_rules", {})

    # Selecionar apenas as colunas necessárias e renomear
    df_processed = df.select(
        [pl.col("mcc").alias("mcc_code"), pl.col("irs_description").alias("description")]
    )

    # Remover duplicadas, mantendo o menor MCC
    df_processed = (
        df_processed.sort("mcc_code").unique(  # Ordenar por MCC crescente
            subset=["description"], keep="first", maintain_order=True
        )  # Manter primeira ocorrência (menor MCC)
    )

    # Adicionar coluna valid_payment_brands usando o dicionário do YAML
    df_processed = df_processed.with_columns(
        [
            pl.col("mcc_code")
            .map_elements(lambda x: mcc_acceptance_rules.get(x, ""), return_dtype=pl.Utf8)
            .alias("valid_payment_brands")
        ]
    )

    # Aplicar tipagem
    df_processed = df_processed.with_columns(
        [
            pl.col("mcc_code").cast(pl.Utf8),
            pl.col("description").cast(pl.Utf8),
            pl.col("valid_payment_brands").cast(pl.Utf8),
        ]
    )

    return df_processed
