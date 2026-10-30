import polars as pl
import requests


def fetch_mcc_codes() -> pl.DataFrame:
    """MCCs (Merchant Category Codes) from a public list on GitHub."""
    url = "https://raw.githubusercontent.com/greggles/mcc-codes/main/mcc_codes.json"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict) and "mcc" in data:
        data = data["mcc"]

    df = pl.DataFrame(data)

    return df
