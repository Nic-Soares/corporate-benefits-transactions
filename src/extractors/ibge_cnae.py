import polars as pl
import requests

URL = "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses"


def fetch_cnae() -> pl.DataFrame:
    """Every CNAE 2.3 subclass with its class, from the IBGE API (CONCLA).

    Ids without punctuation: class `47113` (4 digits + check digit), subclass `4711302`.
    """
    response = requests.get(URL, timeout=60)
    response.raise_for_status()
    return pl.DataFrame(
        [
            {
                "classe_id": item["classe"]["id"],
                "classe": item["classe"]["descricao"],
                "subclasse_id": item["id"],
                "subclasse": item["descricao"],
            }
            for item in response.json()
        ]
    ).sort("subclasse_id")
