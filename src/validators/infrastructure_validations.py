"""Infrastructure validations: the terminal can take this transaction."""

from typing import Any

import polars as pl

from src.validators._common import NOT_FOUND, PASS, RULES, fail, find_one

INFRASTRUCTURE_RULES = RULES["infrastructure_validations"]

SUPPORTED_CAPTURES = {
    "POS": {"chip", "magnetic_stripe", "contactless", "nfc"},
    "TEF": {"chip", "magnetic_stripe"},
}
DEFAULT_CAPTURES = {"chip", "magnetic_stripe"}


def validate_capture_type_support(
    transaction: dict[str, Any], terminals_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return fail(NOT_FOUND["terminal"])
    if transaction["capture_type"] not in SUPPORTED_CAPTURES.get(
        terminal["type"], DEFAULT_CAPTURES
    ):
        return fail(INFRASTRUCTURE_RULES["capture_type_support"]["error_code"])
    return PASS
