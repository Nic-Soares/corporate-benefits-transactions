"""Balance and limit validations on the card product being charged."""

from typing import Any

import polars as pl

from src.validators._common import NOT_FOUND, PASS, RULES, fail, find_one

BALANCE_RULES = RULES["balance_and_limits_validations"]


def _card_product(transaction: dict[str, Any], card_products_df: pl.DataFrame):
    return find_one(
        card_products_df, card_id=transaction["card_id"], product_id=transaction["product_id"]
    )


def validate_current_balance(
    transaction: dict[str, Any], card_products_df: pl.DataFrame
) -> dict[str, Any]:
    card_product = _card_product(transaction, card_products_df)
    if card_product is None:
        return fail(NOT_FOUND["card_product"])
    if card_product["current_balance"] < transaction["amount"]:
        return fail(BALANCE_RULES["current_balance"]["error_code"])
    return PASS


def _within_limit(
    transaction: dict[str, Any], card_products_df: pl.DataFrame, usage: float, rule_name: str
) -> dict[str, Any]:
    card_product = _card_product(transaction, card_products_df)
    if card_product is None:
        return fail(NOT_FOUND["card_product"])
    limit = card_product[rule_name]
    # A limit of 0 means no limit
    if limit > 0 and usage + transaction["amount"] > limit:
        return fail(BALANCE_RULES[rule_name]["error_code"])
    return PASS


def validate_daily_limit(
    transaction: dict[str, Any], card_products_df: pl.DataFrame, daily_usage: float = 0
) -> dict[str, Any]:
    """`daily_usage`: amount already spent on this card product today."""
    return _within_limit(transaction, card_products_df, daily_usage, "daily_limit")


def validate_monthly_limit(
    transaction: dict[str, Any], card_products_df: pl.DataFrame, monthly_usage: float = 0
) -> dict[str, Any]:
    """`monthly_usage`: amount already spent on this card product this month."""
    return _within_limit(transaction, card_products_df, monthly_usage, "monthly_limit")
