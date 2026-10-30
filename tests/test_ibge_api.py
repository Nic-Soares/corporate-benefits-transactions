# %% Cell 1 - Verificação do ambiente
import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Verificar se pyarrow está disponível
try:
    import pyarrow as pa

    print(f"PyArrow version: {pa.__version__}")
except ImportError as e:
    print(f"PyArrow não encontrado: {e}")
    print("\nInstalando pyarrow...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow"])
    import pyarrow as pa

    print(f"PyArrow instalado: {pa.__version__}")

# %% Cell 2 - Teste da API
import polars as pl
import requests


def test_ibge_municipios():
    """Teste simples para consumir a API do IBGE de municípios"""

    print("=== Testando API IBGE - Municípios ===\n")

    # Fazer requisição
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Total de municípios: {len(response.json())}\n")

    # Converter para DataFrame Polars
    df_municipios = pl.DataFrame(response.json())

    print(f"Colunas originais: {df_municipios.columns}")
    print(f"Shape: {df_municipios.shape}")
    print(f"Data Types:\n{df_municipios.dtypes}\n")

    # Expandir estruturas aninhadas
    df_expanded = df_municipios.select(
        [
            pl.col("id").alias("municipio_id"),
            pl.col("nome").alias("municipio_nome"),
            pl.col("microrregiao").struct.field("id").alias("microrregiao_id"),
            pl.col("microrregiao").struct.field("nome").alias("microrregiao_nome"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("id")
            .alias("mesorregiao_id"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("nome")
            .alias("mesorregiao_nome"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("id")
            .alias("uf_id"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("sigla")
            .alias("uf_sigla"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("nome")
            .alias("uf_nome"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("regiao")
            .struct.field("id")
            .alias("regiao_id"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("regiao")
            .struct.field("sigla")
            .alias("regiao_sigla"),
            pl.col("microrregiao")
            .struct.field("mesorregiao")
            .struct.field("UF")
            .struct.field("regiao")
            .struct.field("nome")
            .alias("regiao_nome"),
        ]
    ).with_columns(
        [
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
            pl.col("regiao_nome").cast(pl.Categorical),
        ]
    )

    print("\n=== DataFrame Expandido ===")
    print(f"Colunas: {df_expanded.columns}")
    print(f"Shape: {df_expanded.shape}")
    print(f"Data Types:\n{df_expanded.dtypes}\n")

    # Mostrar amostra
    print("Primeiros 10 registros:")
    print(df_expanded.head(10))

    # Mostrar estrutura aninhada original
    print("\n=== Estrutura de um registro original ===")
    print(response.json()[0])

    return df_expanded


if __name__ == "__main__":
    df = test_ibge_municipios()

# %% Cell 3 - Executar teste
df = test_ibge_municipios()

# %%
