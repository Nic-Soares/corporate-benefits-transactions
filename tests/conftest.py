import polars as pl
import pytest


@pytest.fixture
def municipios_df() -> pl.DataFrame:
    """Offline stand-in for `fetch_municipios()` with the columns the generators read."""
    return pl.DataFrame(
        {
            "municipio_nome": ["São Paulo", "Recife", "Porto Alegre"],
            "uf_sigla": ["SP", "PE", "RS"],
        }
    )
