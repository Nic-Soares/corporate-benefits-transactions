import polars as pl
from typing import Dict, Any

def load_transaction_modalities(pre_populated_data: Dict[str, Any]) -> pl.DataFrame:
    """Loads DataFrame for Transaction Modalities based on business rules"""

    transaction_modalities = [
      {
        "id": modalitites['id'],
        "name": modalitites['name'],
        "type": modalitites['type'],
        "active": True
      }
      for modalitites in pre_populated_data["transaction_modalities"].items()
    ]

    return pl.DataFrame(transaction_modalities).with_columns([
      pl.col('id').cast(pl.Utf8),
      pl.col('name').cast(pl.Utf8),
      pl.col('type').cast(pl.Categorical)
    ])
