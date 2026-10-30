from typing import Any

import polars as pl


def load_products(pre_populate_reference: dict[str, Any]) -> pl.DataFrame:
    """Products from `pre_populated_data.yaml`."""
    products = [
        {
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "active": True,
        }
        for product in pre_populate_reference["products"]
    ]

    return pl.DataFrame(products).with_columns(
        [
            pl.col("id").cast(pl.Utf8),
            pl.col("name").cast(pl.Utf8),
            pl.col("category").cast(pl.Categorical),
        ]
    )
