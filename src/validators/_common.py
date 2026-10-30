"""Shared pieces of the transaction validators.

Every validator takes the transaction as a dict (columns of the `transactions`
table) plus the Polars DataFrames it needs, with the column names of
`database/oltp_postgres/oltp_schema.sql`, and returns `{"passed", "error_code"}`.
Error codes come from `config/validation_rules.yaml`.
"""

from datetime import date, datetime
from typing import Any

import polars as pl

from src.utils.read_yamls import load_pre_populated_data, load_validation_rules

RULES = load_validation_rules()

NOT_FOUND: dict[str, str] = RULES["not_found"]
UNKNOWN_STATUS: str = RULES["unknown_status"]

# Proprietary network (3-party, authorized by CNAE) vs. brands (4-party, by MCC)
PROPRIETARY_MODALITIES = {
    modality["id"]
    for modality in load_pre_populated_data()["transaction_modalities"]
    if modality["type"] == "proprietary_network"
}

PASS: dict[str, Any] = {"passed": True, "error_code": None}


def fail(error_code: str) -> dict[str, Any]:
    return {"passed": False, "error_code": error_code}


def find_one(df: pl.DataFrame, **match: Any) -> dict[str, Any] | None:
    """First row whose columns equal `match`, or None."""
    rows = df.filter(**match)
    return rows.row(0, named=True) if rows.height else None


def transaction_date(transaction: dict[str, Any]) -> date:
    value = transaction["date"]
    return value.date() if isinstance(value, datetime) else value
