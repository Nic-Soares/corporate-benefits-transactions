"""The public data the setup needs, cached in `data/raw` after the first download."""

import logging
from dataclasses import dataclass

import polars as pl

from src.data_generators.reference_data.mcc_and_cnae_loader import RAW_DIR, extract_cnae_data
from src.extractors.ibge_municipalities import fetch_municipios
from src.extractors.mcc_extractor import fetch_mcc_codes

log = logging.getLogger(__name__)


@dataclass
class Sources:
    cnae: pl.DataFrame  # CNAE 2024 (Kaggle): classe_id, classe, subclasse_id, subclasse
    mcc: pl.DataFrame  # public MCC list: mcc_code, description
    municipios: pl.DataFrame  # IBGE: municipio_nome, uf_sigla


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
    """CNAE (Kaggle), MCC list (GitHub) and municipalities (IBGE API)."""
    mcc = _cached(
        "mcc_codes",
        lambda: fetch_mcc_codes().select(
            pl.col("mcc").alias("mcc_code"), pl.col("edited_description").alias("description")
        ),
    )
    municipios = _cached("ibge_municipios", fetch_municipios)
    cnae = extract_cnae_data().with_columns(pl.col(pl.Categorical).cast(pl.String))
    return Sources(cnae=cnae, mcc=mcc, municipios=municipios)
