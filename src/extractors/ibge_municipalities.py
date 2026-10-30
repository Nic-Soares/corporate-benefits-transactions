import polars as pl
import requests

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"


def fetch_municipios() -> pl.DataFrame:
    """
    Busca dados de municípios da API do IBGE.

    Returns:
        pl.DataFrame: DataFrame com dados expandidos dos municípios
    """
    response = requests.get(URL, timeout=60)
    response.raise_for_status()

    df = pl.DataFrame(response.json())

    microrregiao = pl.col("microrregiao")
    mesorregiao = microrregiao.struct.field("mesorregiao")
    # Municipalities created after the micro/mesoregion division (e.g. Boa Esperança
    # do Norte, MT, 2024) come with a null microrregião; their UF is reached through
    # the região imediata instead.
    uf = pl.coalesce(
        mesorregiao.struct.field("UF"),
        pl.col("regiao-imediata").struct.field("regiao-intermediaria").struct.field("UF"),
    )
    regiao = uf.struct.field("regiao")

    return df.select(
        pl.col("id").cast(pl.String).alias("municipio_id"),
        pl.col("nome").alias("municipio_nome"),
        microrregiao.struct.field("id").cast(pl.String).alias("microrregiao_id"),
        microrregiao.struct.field("nome").alias("microrregiao_nome"),
        mesorregiao.struct.field("id").cast(pl.String).alias("mesorregiao_id"),
        mesorregiao.struct.field("nome").alias("mesorregiao_nome"),
        uf.struct.field("id").cast(pl.String).alias("uf_id"),
        uf.struct.field("sigla").cast(pl.Categorical).alias("uf_sigla"),
        uf.struct.field("nome").alias("uf_nome"),
        regiao.struct.field("id").cast(pl.String).alias("regiao_id"),
        regiao.struct.field("sigla").cast(pl.Categorical).alias("regiao_sigla"),
        regiao.struct.field("nome").alias("regiao_nome"),
    )
