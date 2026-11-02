"""Status validations: every record the transaction touches must be active on its day."""

from typing import Any

import polars as pl

from src.domain.status import status_on
from src.utils.table import find_one
from src.validators._common import PASS, RULES, UNKNOWN_STATUS, fail, not_found, transaction_date

STATUS_RULES = RULES["status_validations"]


def _check_status(value: str, rule_name: str, entity: str) -> dict[str, Any]:
    rule = STATUS_RULES[rule_name]
    if value == rule["required_value"]:
        return PASS
    if value not in rule["error_codes"]:
        return fail(UNKNOWN_STATUS, f"unknown_{entity}_status")
    return fail(rule["error_codes"][value], f"{entity}_{value}")


def _check_active(record: dict[str, Any], rule_name: str, entity: str) -> dict[str, Any]:
    if record["active"]:
        return PASS
    return fail(STATUS_RULES[rule_name]["error_codes"][False], f"{entity}_disabled")


def validate_card_status(transaction: dict[str, Any], cards_df: pl.DataFrame) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return not_found("card")
    return _check_status(status_on(card, transaction_date(transaction)), "card_status", "card")


def validate_cardholder_status(
    transaction: dict[str, Any], cards_df: pl.DataFrame, cardholders_df: pl.DataFrame
) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return not_found("card")
    cardholder = find_one(cardholders_df, id=card["cardholder_id"])
    if cardholder is None:
        return not_found("cardholder")
    return _check_status(
        status_on(cardholder, transaction_date(transaction)), "cardholder_status", "cardholder"
    )


def validate_establishment_status(
    transaction: dict[str, Any], establishments_df: pl.DataFrame
) -> dict[str, Any]:
    establishment = find_one(establishments_df, id=transaction["establishment_id"])
    if establishment is None:
        return not_found("establishment")
    return _check_status(
        status_on(establishment, transaction_date(transaction)),
        "establishment_status",
        "establishment",
    )


def validate_terminal_status(
    transaction: dict[str, Any], terminals_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return not_found("terminal")
    return _check_status(
        status_on(terminal, transaction_date(transaction)), "terminal_status", "terminal"
    )


def validate_modality_active(
    transaction: dict[str, Any], cards_df: pl.DataFrame, modalities_df: pl.DataFrame
) -> dict[str, Any]:
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return not_found("card")
    modality = find_one(modalities_df, id=card["modality_id"])
    if modality is None:
        return not_found("modality")
    return _check_active(modality, "modality_active", "modality")


def validate_acquirer_active(
    transaction: dict[str, Any], terminals_df: pl.DataFrame, acquirers_df: pl.DataFrame
) -> dict[str, Any]:
    terminal = find_one(terminals_df, id=transaction["terminal_id"])
    if terminal is None:
        return not_found("terminal")
    acquirer = find_one(acquirers_df, id=terminal["acquirer_id"])
    if acquirer is None:
        return not_found("acquirer")
    return _check_active(acquirer, "acquirer_active", "acquirer")
