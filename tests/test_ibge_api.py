import polars as pl
import pytest

from src.extractors.ibge_municipalities import fetch_municipios


@pytest.fixture(scope="module")
def municipios() -> pl.DataFrame:
    return fetch_municipios()


@pytest.mark.network
def test_fetch_municipios(municipios):
    # Brazil has 5,571 municipalities since Boa Esperança do Norte (MT) in 2024
    assert len(municipios) >= 5571
    assert municipios["municipio_id"].n_unique() == len(municipios)
    assert {"municipio_nome", "uf_sigla"} <= set(municipios.columns)


@pytest.mark.network
@pytest.mark.xfail(
    reason="ST-03.4: UF comes from the microrregião, which the API leaves null for "
    "Boa Esperança do Norte (MT)",
    strict=True,
)
def test_every_municipio_has_a_uf(municipios):
    assert municipios["uf_sigla"].null_count() == 0
    assert municipios["uf_sigla"].n_unique() == 27
