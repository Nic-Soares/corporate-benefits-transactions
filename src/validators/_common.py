"""Shared pieces of the transaction validators.

Every validator takes the transaction as a dict (columns of the `transactions`
table) plus the Polars DataFrames it needs, with the column names of
`database/oltp_postgres/oltp_schema.sql`, and returns `{"passed", "error_code"}`.
Error codes come from `config/validation_rules.yaml`.
"""

from datetime import date, datetime
from typing import Any

import polars as pl

from src.utils.read_yamls import load_validation_rules

RULES = load_validation_rules()

# Referenced record missing. Not in validation_rules.yaml yet (EP-04).
NOT_FOUND = {
    "card": "99",
    "card_product": "99",
    "cardholder": "98",
    "modality": "98",
    "establishment": "97",
    "terminal": "96",
    "acquirer": "96",
}
UNKNOWN_STATUS = "99"

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
