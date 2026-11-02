import polars as pl
import requests

# Table 6579: estimated resident population; variable 9324; N6 = municipalities
URL = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/-1/variaveis/9324"


def fetch_population() -> pl.DataFrame:
    """The latest IBGE population estimate of every municipality."""
    response = requests.get(URL, params={"localidades": "N6[all]"}, timeout=120)
    response.raise_for_status()
    series = response.json()[0]["resultados"][0]["series"]
    return pl.DataFrame(
        [
            {
                "municipio_id": item["localidade"]["id"],
                "population": int(next(iter(item["serie"].values()))),
            }
            for item in series
        ]
    )
