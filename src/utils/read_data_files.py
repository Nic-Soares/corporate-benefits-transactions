from pathlib import Path

import geopandas as gpd
import polars as pl


def read_shapefile(shapefile_path):
    gdf = gpd.read_file(shapefile_path)
    return gdf


def read_parquet(parquet_path):
    """Lê um arquivo Parquet e retorna um DataFrame Polars"""
    path = Path(parquet_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado em: {parquet_path}")

    return pl.read_parquet(parquet_path)
