import random

import polars as pl

from src.entities import fake


def test_municipalities_follow_population():
    municipios = pl.DataFrame(
        {
            "municipio_nome": ["São Paulo", "Borá"],
            "uf_sigla": ["SP", "SP"],
            "population": [11_900_000, 900],
        }
    )
    random.seed(1)
    draws = [fake.Municipalities(municipios).draw()["municipio_nome"] for _ in range(500)]
    assert draws.count("São Paulo") > 490


def test_municipalities_without_population_are_uniform():
    municipios = pl.DataFrame({"municipio_nome": ["A", "B"], "uf_sigla": ["SP", "RJ"]})
    random.seed(1)
    draws = [fake.Municipalities(municipios).draw()["municipio_nome"] for _ in range(500)]
    assert 150 < draws.count("A") < 350


def test_municipalities_by_another_weight():
    municipios = pl.DataFrame(
        {
            "municipio_nome": ["Big town", "Rich town"],
            "uf_sigla": ["SP", "SP"],
            "population": [1_000_000, 10],
            "gdp": [10, 1_000_000],
        }
    )
    random.seed(1)
    draws = [fake.Municipalities(municipios, weight="gdp").draw() for _ in range(200)]
    assert all(d["municipio_nome"] == "Rich town" for d in draws)
