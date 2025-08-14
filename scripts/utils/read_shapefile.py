import geopandas as gpd
import pandas as pd
import shapely.geometry

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



if __name__ == "__main__":
    shapefile_path = './data/BR_Municipios_2024/BR_Municipios_2024.shp'
    try:
        municipios_df = carregar_municipios_shapefile(shapefile_path)
        print(municipios_df.head())
        print(municipios_df.columns)
        print(f"Total de municípios: {len(municipios_df)}")
    except Exception as e:
        print(f"Erro ao carregar shapefile: {e}")
