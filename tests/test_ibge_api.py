import polars as pl
import pytest

from src.extractors.ibge_cnae import fetch_cnae
from src.extractors.ibge_municipalities import fetch_municipios
from src.extractors.ibge_population import fetch_population


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
def test_every_municipio_has_a_uf(municipios):
    # Boa Esperança do Norte (MT) has no microrregião; its UF comes from the região imediata
    assert municipios["uf_sigla"].null_count() == 0
    assert municipios["uf_sigla"].n_unique() == 27


@pytest.mark.network
def test_fetch_cnae():
    cnae = fetch_cnae()
    # CNAE 2.3: 1,332 subclasses, 7 digits; classes with their check digit
    assert len(cnae) >= 1300
    assert cnae["subclasse_id"].str.len_chars().eq(7).all()
    assert cnae["classe_id"].str.len_chars().eq(5).all()
    assert (cnae["subclasse_id"].str.slice(0, 4) == cnae["classe_id"].str.slice(0, 4)).all()


@pytest.mark.network
def test_fetch_population(municipios):
    population = fetch_population()
    assert set(population["municipio_id"]) == set(municipios["municipio_id"])
    sao_paulo = population.filter(municipio_id="3550308")["population"].item()
    assert sao_paulo > 10_000_000
