import pandas as pd
from shapely.geometry.base import BaseGeometry
from src.common.queries.data_queries import verificar_tabela_possui_dados

import geopandas as gpd

def carregar_municipios_shapefile(shapefile_path):
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.rename(columns={
        'CD_MUN': 'municipio_id',
        'NM_MUN': 'municipio_nome',
        'CD_RGI': 'rgi_id',
        'NM_RGI': 'rgi_nome',
        'CD_RGINT': 'rgint_id',
        'NM_RGINT': 'rgint_nome',
        'CD_UF': 'uf_id',
        'NM_UF': 'uf_nome',
        'SIGLA_UF': 'uf_sigla',
        'CD_REGIA': 'regiao_id',
        'NM_REGIA': 'regiao_nome',
        'SIGLA_RG': 'regiao_sigla',
        'CD_CONCU': 'concu_id',
        'NM_CONCU': 'concu_nome',
        'AREA_KM2': 'area_km2'
    })
    gdf['created_at'] = pd.Timestamp.now()
    return gdf

def importar_municipios(conn):
    """Importa dados de municípios do shapefile para o banco de dados"""
    # Verifica se a tabela já possui dados
    if verificar_tabela_possui_dados(conn, "dim_municipios"):
        print("dim_municipios já possui dados. Nenhuma importação realizada.")
        return
    shapefile_path = './data/BR_Municipios_2024/BR_Municipios_2024.shp'
    gdf = carregar_municipios_shapefile(shapefile_path)  # Deve retornar GeoDataFrame com geometry shapely

    # Instala e carrega extensão espacial (só precisa fazer uma vez por conexão)
    conn.execute("INSTALL spatial;")
    conn.execute("LOAD spatial;")

    # Extrai apenas latitude e longitude do centroide
    # Cria uma cópia como DataFrame regular sem geometry
    df_municipios = pd.DataFrame(gdf.drop(columns=['geometry']))

    # Adiciona latitude e longitude do centroide
    df_municipios['latitude'] = gdf['geometry'].apply(
        lambda geom: geom.centroid.y if isinstance(geom, BaseGeometry) and geom is not None else None
    )
    df_municipios['longitude'] = gdf['geometry'].apply(
        lambda geom: geom.centroid.x if isinstance(geom, BaseGeometry) and geom is not None else None
    )

    # Registra o DataFrame como uma tabela temporária
    conn.register('municipios_df', df_municipios)

    # Reordena colunas para bater com a tabela
    colunas_ordem = ['municipio_id', 'municipio_nome', 'rgi_id', 'rgi_nome', 'rgint_id', 'rgint_nome',
                     'uf_id', 'uf_nome', 'uf_sigla', 'regiao_id', 'regiao_nome', 'regiao_sigla',
                     'concu_id', 'concu_nome', 'area_km2', 'latitude', 'longitude', 'created_at']
    df_municipios = df_municipios[colunas_ordem]

    conn.unregister('municipios_df')
    conn.register('municipios_df', df_municipios)
    conn.execute("INSERT INTO dim_municipios SELECT * FROM municipios_df")

if __name__ == "__main__":
    shapefile_path = './data/BR_Municipios_2024/BR_Municipios_2024.shp'
    try:
        municipios_df = carregar_municipios_shapefile(shapefile_path)
        print(municipios_df.head())
        print(municipios_df.columns)
        print(f"Total de municípios: {len(municipios_df)}")
    except Exception as e:
        print(f"Erro ao carregar shapefile: {e}")
