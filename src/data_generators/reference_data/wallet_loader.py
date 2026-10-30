from typing import Any

import polars as pl


def load_wallets(pre_populated_data: dict[str, Any]) -> pl.DataFrame:
    """Wallets from `pre_populated_data.yaml`."""
    wallets = [
        {
            "id": wallet["id"],
            "name": wallet["name"],
            "category": wallet["category"],
            "active": True,
        }
        for wallet in pre_populated_data["wallets"]
    ]

    return pl.DataFrame(wallets).with_columns(pl.col("category").cast(pl.Categorical))
