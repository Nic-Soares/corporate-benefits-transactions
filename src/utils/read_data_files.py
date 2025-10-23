import geopandas as gpd

def read_shapefile(shapefile_path):
    gdf = gpd.read_file(shapefile_path)
    return gdf

def read_parquet():
  pass
