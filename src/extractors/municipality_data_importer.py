import pandas as pd
from shapely.geometry.base import BaseGeometry
from src.utils.read_data_files import read_shapefile


def generate_municipality_data(shapefile_path='./data/raw/municipios/municipios.shp'):
    """Generates municipality DataFrame from shapefile"""
    gdf = read_shapefile(shapefile_path)
    gdf = gdf.rename(columns={
        'CD_MUN': 'municipality_id',
        'NM_MUN': 'municipality_name',
        'CD_RGI': 'rgi_id',
        'NM_RGI': 'rgi_name',
        'CD_RGINT': 'rgint_id',
        'NM_RGINT': 'rgint_name',
        'CD_UF': 'state_id',
        'NM_UF': 'state_name',
        'SIGLA_UF': 'state_code',
        'CD_REGIA': 'region_id',
        'NM_REGIA': 'region_name',
        'SIGLA_RG': 'region_code',
        'CD_CONCU': 'concu_id',
        'NM_CONCU': 'concu_name',
        'AREA_KM2': 'area_km2'
    })
    gdf['created_at'] = pd.Timestamp.now()
    gdf['updated_at'] = None

    # Extrai apenas latitude e longitude do centroide
    df_municipios = pd.DataFrame(gdf.drop(columns=['geometry']))
    df_municipios['latitude'] = gdf['geometry'].apply(lambda geom: geom.centroid.y if geom is not None else None)
    df_municipios['longitude'] = gdf['geometry'].apply(lambda geom: geom.centroid.x if geom is not None else None)

    # Reordena colunas para bater com a tabela
    colunas_ordem = [
        'municipality_id', 'municipality_name', 'rgi_id', 'rgi_name', 'rgint_id', 'rgint_name',
        'state_id', 'state_name', 'state_code', 'region_id', 'region_name', 'region_code',
        'concu_id', 'concu_name', 'area_km2', 'latitude', 'longitude', 'created_at', 'updated_at'
    ]
    df_municipios = df_municipios[colunas_ordem]

    # Aplicação dos tipos de dados
    string_cols = ['municipality_id', 'municipality_name', 'rgi_id', 'rgint_id', 'state_id', 'region_id', 'concu_id']
    for col in string_cols:
        df_municipios[col] = df_municipios[col].astype('string')

    categorical_cols = ['rgi_name', 'rgint_name', 'state_name', 'state_code', 'region_name', 'region_code', 'concu_name']
    for col in categorical_cols:
        df_municipios[col] = df_municipios[col].astype('category')

    numeric_cols = ['area_km2', 'latitude', 'longitude']
    for col in numeric_cols:
        df_municipios[col] = df_municipios[col].astype('float64')

    return df_municipios


if __name__ == "__main__":
    shapefile_path = './data/raw/municipios/municipios.shp'
    try:
        municipios_df = generate_municipality_data(shapefile_path)
        print(municipios_df.head())
        print(municipios_df.columns)
        print(municipios_df.dtypes)
        print(f"Total de municípios: {len(municipios_df)}")
    except Exception as e:
        print(f"Erro ao carregar shapefile: {e}")
