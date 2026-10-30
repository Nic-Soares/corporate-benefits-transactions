from typing import Any

import polars as pl


def load_capture_technologies(pre_populate_reference: dict[str, Any]) -> pl.DataFrame:
    """Load capture technologies from business_data['transaction_technologies']"""
    capture_tech_list = [
        {"id": tech["code"], "name": tech["name"], "category": tech["category"]}
        for tech in pre_populate_reference["transaction_technologies"]
    ]

    return pl.DataFrame(capture_tech_list).with_columns(
        [
            pl.col("id").cast(pl.Utf8),
            pl.col("name").cast(pl.Utf8),
            pl.col("category").cast(pl.Categorical),
        ]
    )
