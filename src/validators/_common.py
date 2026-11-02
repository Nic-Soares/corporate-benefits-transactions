"""Shared pieces of the transaction validators.

Every validator takes the transaction as a dict (columns of the `transactions`
table) plus the Polars DataFrames it needs, with the column names of
`database/oltp_postgres/oltp_schema.sql`, and returns
`{"passed", "error_code", "reason"}`: the ISO 8583 response code from
`config/validation_rules.yaml` and the specific cause (`decline_reason`).
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

PASS: dict[str, Any] = {"passed": True, "error_code": None, "reason": None}


def fail(error_code: str, reason: str) -> dict[str, Any]:
    return {"passed": False, "error_code": error_code, "reason": reason}


def not_found(entity: str) -> dict[str, Any]:
    return fail(NOT_FOUND[entity], f"{entity}_not_found")


class Table:
    """The rows of a DataFrame as dicts, indexed by the columns they are looked up
    by (each index built on first use). Lookups are constant time, where a
    DataFrame filter scans the whole table. Rows are shared by every index, so a
    value changed in place (a balance) shows in all of them."""

    def __init__(self, df: pl.DataFrame) -> None:
        self.schema = df.schema
        self.rows: list[dict[str, Any]] = df.to_dicts()
        self._indexes: dict[tuple[str, ...], dict[tuple, list[dict[str, Any]]]] = {}
        # Answers derived from the rows, kept by whoever computes them
        self.memo: dict[Any, Any] = {}

    def find_all(self, **match: Any) -> list[dict[str, Any]]:
        """Rows whose columns equal `match`."""
        if len(match) == 1:  # most lookups: by id
            [(column, value)] = match.items()
            columns, key = (column,), (value,)
        else:
            columns = tuple(sorted(match))
            key = tuple(match[c] for c in columns)
        index = self._indexes.get(columns)
        if index is None:
            index = self._indexes[columns] = {}
            for row in self.rows:
                index.setdefault(tuple(row[c] for c in columns), []).append(row)
        return index.get(key, [])

    def to_frame(self) -> pl.DataFrame:
        return pl.DataFrame(self.rows, schema=self.schema)


# A Table per DataFrame passed to a validator, kept with the DataFrame so that a
# reused id() can't point to another one
_TABLES: dict[int, tuple[pl.DataFrame, Table]] = {}


def as_table(data: pl.DataFrame | Table) -> Table:
    """`data` itself if a Table; otherwise the Table of that DataFrame, built once."""
    if isinstance(data, Table):
        return data
    cached = _TABLES.get(id(data))
    if cached is None or cached[0] is not data:
        if len(_TABLES) > 64:
            _TABLES.clear()
        cached = _TABLES[id(data)] = (data, Table(data))
    return cached[1]


def find_all(data: pl.DataFrame | Table, **match: Any) -> list[dict[str, Any]]:
    """Rows whose columns equal `match`."""
    return as_table(data).find_all(**match)


def find_one(data: pl.DataFrame | Table, **match: Any) -> dict[str, Any] | None:
    """First row whose columns equal `match`, or None."""
    rows = as_table(data).find_all(**match)
    return rows[0] if rows else None


def transaction_date(transaction: dict[str, Any]) -> date:
    value = transaction["date"]
    return value.date() if isinstance(value, datetime) else value
