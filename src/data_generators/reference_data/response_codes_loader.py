import polars as pl
from typing import Dict

def load_response_codes(pre_populated_data: Dict) -> pl.DataFrame:
    """Loads DataFrame for Response Codes from pre_populated_data.yaml"""

    # Extract response codes
    response_codes = [
        {
            'id': code,
            'description': description,
        }
        for code, description in pre_populated_data['response_codes'].items()
    ]

    return pl.DataFrame(response_codes).with_columns([
        pl.col('id').cast(pl.Utf8),
        pl.col('description').cast(pl.Utf8),
    ])
