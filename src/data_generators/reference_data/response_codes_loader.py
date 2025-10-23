import polars as pl
from typing import Dict

def load_response_codes(validation_rules: ValidationRulesReference) -> pl.DataFrame:
    """Loads DataFrame for Response Codes from validation_rules.yaml"""

    # Extract response codes
    response_codes = [
        {
            'id': code,
            'description': description,
        }
        for code in validation_rules['response_codes'].items()
    ]

    return pl.DataFrame(response_codes).with_columns([
        pl.col('id').cast(pl.Utf8),
        pl.col('description').cast(pl.Utf8),
    ])
