"""Status validations: every record the transaction touches must be active."""

from typing import Any

import polars as pl

from src.validators._common import NOT_FOUND, PASS, RULES, UNKNOWN_STATUS, fail, find_one

STATUS_RULES = RULES["status_validations"]


def _check_status(value: str, rule_name: str, default: str = UNKNOWN_STATUS) -> dict[str, Any]:
    rule = STATUS_RULES[rule_name]
    if value == rule["required_value"]:
        return PASS
    return fail(rule["error_codes"].get(value, default))


def _check_active(record: dict[str, Any], rule_name: str) -> dict[str, Any]:
    return PASS if record["active"] else fail(STATUS_RULES[rule_name]["error_codes"][False])


def validate_card_status(transaction: dict[str, Any], cards_df: pl.DataFrame) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return fail(NOT_FOUND["card"])
    return _check_status(card["status"], "card_status")


def validate_cardholder_status(
    transaction: dict[str, Any], cards_df: pl.DataFrame, cardholders_df: pl.DataFrame
) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return fail(NOT_FOUND["card"])
    cardholder = find_one(cardholders_df, id=card["cardholder_id"])
    if cardholder is None:
        return fail(NOT_FOUND["cardholder"])
    return _check_status(cardholder["status"], "cardholder_status")


def validate_establishment_status(
    transaction: dict[str, Any], establishments_df: pl.DataFrame
) -> dict[str, Any]:
    establishment = find_one(establishments_df, id=transaction["establishment_id"])
    if establishment is None:
        return fail(NOT_FOUND["establishment"])
    return _check_status(establishment["status"], "establishment_status")


def validate_terminal_status(
    transaction: dict[str, Any], terminals_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return fail(NOT_FOUND["terminal"])
    return _check_status(terminal["status"], "terminal_status")


def validate_card_product_status(
    transaction: dict[str, Any], card_products_df: pl.DataFrame
) -> dict[str, Any]:
    card_product = find_one(
        card_products_df, card_id=transaction["card_id"], product_id=transaction["product_id"]
    )
    if card_product is None:
        return fail(NOT_FOUND["card_product"])
    # Any status other than active (suspended, cancelled…) declines as inactive
    inactive = STATUS_RULES["card_product_status"]["error_codes"]["inactive"]
    return _check_status(card_product["status"], "card_product_status", default=inactive)


def validate_product_active(
    transaction: dict[str, Any], products_df: pl.DataFrame
) -> dict[str, Any]:
    product = find_one(products_df, id=transaction["product_id"])
    if product is None:
        return fail(STATUS_RULES["product_active"]["error_codes"][False])
    return _check_active(product, "product_active")


def validate_modality_active(
    transaction: dict[str, Any], cards_df: pl.DataFrame, modalities_df: pl.DataFrame
) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return fail(NOT_FOUND["card"])
    if card["modality_id"] is None:
        return PASS  # proprietary-network card: no modality to check
    modality = find_one(modalities_df, id=card["modality_id"])
    if modality is None:
        return fail(NOT_FOUND["modality"])
    return _check_active(modality, "modality_active")


def validate_acquirer_active(
    transaction: dict[str, Any], terminals_df: pl.DataFrame, acquirers_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return fail(NOT_FOUND["terminal"])
    acquirer = find_one(acquirers_df, id=terminal["acquirer_id"])
    if acquirer is None:
        return fail(NOT_FOUND["acquirer"])
    return _check_active(acquirer, "acquirer_active")
