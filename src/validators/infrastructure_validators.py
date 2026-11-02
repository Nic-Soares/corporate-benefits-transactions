"""Infrastructure validations: the terminal can take this transaction."""

from typing import Any

import polars as pl

from src.table import find_one
from src.validators._common import PASS, RULES, fail, not_found

INFRASTRUCTURE_RULES = RULES["infrastructure_validations"]

CAPTURE_RULE = INFRASTRUCTURE_RULES["capture_type_support"]


def validate_capture_type_support(
    transaction: dict[str, Any], terminals_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return not_found("terminal")
    supported = CAPTURE_RULE["supported_by_terminal_type"].get(terminal["type"], [])
    if transaction["capture_type"] not in supported:
        return fail(CAPTURE_RULE["error_code"], "capture_not_supported")
    return PASS
