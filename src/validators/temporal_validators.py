"""Temporal validations: the transaction can't predate or outlive its records."""

from datetime import date
from typing import Any

import polars as pl

from src.validators._common import NOT_FOUND, PASS, RULES, fail, find_one, transaction_date

TEMPORAL_RULES = RULES["temporal_validations"]


def _on_or_after(transaction: dict[str, Any], start: date, rule_name: str) -> dict[str, Any]:
    if transaction_date(transaction) < start:
        return fail(TEMPORAL_RULES[rule_name]["error_code"])
    return PASS


def validate_card_expiration(transaction: dict[str, Any], cards_df: pl.DataFrame) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return fail(NOT_FOUND["card"])
    if transaction_date(transaction) > card["expiration_date"]:
        return fail(TEMPORAL_RULES["card_expiration"]["error_code"])
    return PASS


def validate_cardholder_admission(
    transaction: dict[str, Any], cards_df: pl.DataFrame, cardholders_df: pl.DataFrame
) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return fail(NOT_FOUND["card"])
    cardholder = find_one(cardholders_df, id=card["cardholder_id"])
    if cardholder is None:
        return fail(NOT_FOUND["cardholder"])
    return _on_or_after(transaction, cardholder["admission_date"], "cardholder_admission")


def validate_establishment_accreditation(
    transaction: dict[str, Any], establishments_df: pl.DataFrame
) -> dict[str, Any]:
    establishment = find_one(establishments_df, id=transaction["establishment_id"])
    if establishment is None:
        return fail(NOT_FOUND["establishment"])
    return _on_or_after(
        transaction, establishment["accreditation_date"], "establishment_accreditation"
    )


def validate_terminal_installation(
    transaction: dict[str, Any], terminals_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return fail(NOT_FOUND["terminal"])
    return _on_or_after(transaction, terminal["installation_date"], "terminal_installation")
