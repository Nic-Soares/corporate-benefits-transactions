import requests
import polars as pl


def fetch_municipios() -> pl.DataFrame:
    """
    Busca dados de municípios da API do IBGE.
    
    Returns:
        pl.DataFrame: DataFrame com dados expandidos dos municípios
    """
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url)
    response.raise_for_status()
    
    df = pl.DataFrame(response.json())
    
    df_expanded = df.select([
        pl.col("id").alias("municipio_id"),
        pl.col("nome").alias("municipio_nome"),
        pl.col("microrregiao").struct.field("id").alias("microrregiao_id"),
        pl.col("microrregiao").struct.field("nome").alias("microrregiao_nome"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("id").alias("mesorregiao_id"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("nome").alias("mesorregiao_nome"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("id").alias("uf_id"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("sigla").alias("uf_sigla"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("nome").alias("uf_nome"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("regiao").struct.field("id").alias("regiao_id"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("regiao").struct.field("sigla").alias("regiao_sigla"),
        pl.col("microrregiao").struct.field("mesorregiao").struct.field("UF").struct.field("regiao").struct.field("nome").alias("regiao_nome"),
    ]).with_columns([
        pl.col("municipio_id").cast(pl.String),
        pl.col("municipio_nome").cast(pl.Utf8),
        pl.col("microrregiao_id").cast(pl.String),
        pl.col("microrregiao_nome").cast(pl.Utf8),
        pl.col("mesorregiao_id").cast(pl.String),
        pl.col("mesorregiao_nome").cast(pl.Utf8),
        pl.col("uf_id").cast(pl.String),
        pl.col("uf_sigla").cast(pl.Categorical),
        pl.col("uf_nome").cast(pl.Utf8),
        pl.col("regiao_id").cast(pl.String),
        pl.col("regiao_sigla").cast(pl.Categorical),
        pl.col("regiao_nome").cast(pl.Utf8),
    ])
    
    return df_expanded
