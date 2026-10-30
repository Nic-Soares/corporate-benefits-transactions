from typing import Any

import polars as pl


def load_acquirers(pre_populate_reference: dict[str, Any]) -> pl.DataFrame:
    """Loads DataFrame for Acquirers based on business rules"""
    acquires = [
        {
            "id": acquire["id"],
            "name": acquire["name"],
            "active": True,
        }
        for acquire in pre_populate_reference["acquirers"]
    ]

    return pl.DataFrame(acquires).with_columns(
        [
            pl.col("id").cast(pl.Utf8),
            pl.col("name").cast(pl.Utf8),
            pl.col("active").cast(pl.Boolean),
        ]
    )
