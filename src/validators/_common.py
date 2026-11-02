"""Shared pieces of the transaction validators.

Every validator takes the transaction as a dict (columns of the `transactions`
table) plus the Polars DataFrames it needs, with the column names of
`database/oltp/oltp_schema.sql`, and returns
`{"passed", "error_code", "reason"}`: the ISO 8583 response code from
`config/authorization.yaml` and the specific cause (`decline_reason`).
"""

from datetime import date, datetime
from typing import Any

from src.config import load_authorization, load_reference

RULES = load_authorization()

NOT_FOUND: dict[str, str] = RULES["not_found"]
UNKNOWN_STATUS: str = RULES["unknown_status"]

# Proprietary network (3-party, authorized by CNAE) vs. brands (4-party, by MCC)
PROPRIETARY_MODALITIES = {
    modality["id"]
    for modality in load_reference()["transaction_modalities"]
    if modality["type"] == "proprietary_network"
}

PASS: dict[str, Any] = {"passed": True, "error_code": None, "reason": None}


def fail(error_code: str, reason: str) -> dict[str, Any]:
    return {"passed": False, "error_code": error_code, "reason": reason}


def not_found(entity: str) -> dict[str, Any]:
    return fail(NOT_FOUND[entity], f"{entity}_not_found")


def transaction_date(transaction: dict[str, Any]) -> date:
    value = transaction["date"]
    return value.date() if isinstance(value, datetime) else value
