import polars as pl
import requests

# Table 5938: municipal GDP; variable 37, GDP at current prices (thousand BRL);
# N6 = municipalities
URL = "https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/-1/variaveis/37"


def fetch_gdp() -> pl.DataFrame:
    """The latest IBGE GDP of every municipality, in thousand BRL; empty when the
    IBGE marks a value as missing."""
    response = requests.get(URL, params={"localidades": "N6[all]"}, timeout=120)
    response.raise_for_status()
    series = response.json()[0]["resultados"][0]["series"]
    rows = []
    for item in series:
        value = next(iter(item["serie"].values()))
        rows.append(
            {
                "municipio_id": item["localidade"]["id"],
                "gdp": int(value) if value.isdigit() else None,
            }
        )
    return pl.DataFrame(rows, schema={"municipio_id": pl.String, "gdp": pl.Int64})
