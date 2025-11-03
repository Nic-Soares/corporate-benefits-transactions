import requests
import polars as pl


def fetch_mcc_codes() -> pl.DataFrame:
    """
    Busca dados de MCC (Merchant Category Codes) de fonte pública no GitHub.
    
    Returns:
        pl.DataFrame: DataFrame com dados dos MCCs
    """
    url = "https://raw.githubusercontent.com/greggles/mcc-codes/main/mcc_codes.json"
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    if isinstance(data, dict) and 'mcc' in data:
        data = data['mcc']
    
    df = pl.DataFrame(data)
    
    return df

