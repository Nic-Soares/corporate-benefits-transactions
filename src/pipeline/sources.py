"""The public data the setup needs, cached in `data/raw` after the first download.

The cached files are versioned, so the same seed gives the same dataset on any
machine; their hashes go into `run_metadata` (`provenance.source_hashes`).
Delete a file to download a newer version."""

import logging
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from src.extractors.ibge_cnae import fetch_cnae
from src.extractors.ibge_gdp import fetch_gdp
from src.extractors.ibge_municipalities import fetch_municipios
from src.extractors.ibge_population import fetch_population
from src.extractors.mcc_extractor import fetch_mcc_codes

log = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"


@dataclass
class Sources:
    cnae: pl.DataFrame  # IBGE CNAE: classe_id, classe, subclasse_id, subclasse
    mcc: pl.DataFrame  # public MCC list: mcc_code, description
    municipios: pl.DataFrame  # IBGE: municipio_nome, uf_sigla, population, gdp


def _cached(name: str, fetch) -> pl.DataFrame:
    path = RAW_DIR / f"{name}.parquet"
    if path.exists():
        return pl.read_parquet(path)
    log.info("Downloading %s", name)
    df = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    return df


def fetch_sources() -> Sources:
    """CNAE, municipalities, population and GDP (IBGE APIs) and the MCC list (GitHub)."""
    cnae = _cached("ibge_cnae", fetch_cnae)
    mcc = _cached(
        "mcc_codes",
        lambda: fetch_mcc_codes().select(
            pl.col("mcc").alias("mcc_code"), pl.col("edited_description").alias("description")
        ),
    )
    population = _cached("ibge_population", fetch_population)
    gdp = _cached("ibge_gdp", fetch_gdp)
    municipios = (
        _cached("ibge_municipios", fetch_municipios)
        .join(population, on="municipio_id", how="left")
        .join(gdp, on="municipio_id", how="left")
    )
    return Sources(cnae=cnae, mcc=mcc, municipios=municipios)
