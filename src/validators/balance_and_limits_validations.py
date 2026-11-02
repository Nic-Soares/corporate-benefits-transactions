"""Balance and limit validations on the wallet being charged."""

from typing import Any

import polars as pl

from src.validators._common import PASS, RULES, Table, fail, find_one, not_found

BALANCE_RULES = RULES["balance_and_limits_validations"]


def _card_wallet(transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table):
    return find_one(
        card_wallets_df, id=transaction["card_wallet_id"], card_id=transaction["card_id"]
    )


def validate_current_balance(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table
) -> dict[str, Any]:
    card_wallet = _card_wallet(transaction, card_wallets_df)
    if card_wallet is None:
        return not_found("card_wallet")
    if card_wallet["current_balance"] < transaction["amount"]:
        return fail(BALANCE_RULES["current_balance"]["error_code"], "insufficient_balance")
    return PASS


def _within_limit(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table, usage: float, rule_name: str
) -> dict[str, Any]:
    card_wallet = _card_wallet(transaction, card_wallets_df)
    if card_wallet is None:
        return not_found("card_wallet")
    limit = card_wallet[rule_name]
    # A limit of 0 means no limit
    if limit > 0 and usage + transaction["amount"] > limit:
        return fail(BALANCE_RULES[rule_name]["error_code"], f"{rule_name}_exceeded")
    return PASS


def validate_daily_limit(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table, daily_usage: float = 0
) -> dict[str, Any]:
    """`daily_usage`: amount already spent on this wallet today."""
    return _within_limit(transaction, card_wallets_df, daily_usage, "daily_limit")


def validate_monthly_limit(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table, monthly_usage: float = 0
) -> dict[str, Any]:
    """`monthly_usage`: amount already spent on this wallet this month."""
    return _within_limit(transaction, card_wallets_df, monthly_usage, "monthly_limit")


def validate_daily_count(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame | Table, daily_count: int = 0
) -> dict[str, Any]:
    """`daily_count`: purchases already approved on this wallet today."""
    card_wallet = _card_wallet(transaction, card_wallets_df)
    if card_wallet is None:
        return not_found("card_wallet")
    limit = card_wallet["daily_count_limit"]
    # A limit of 0 means no limit
    if limit > 0 and daily_count + 1 > limit:
        return fail(BALANCE_RULES["daily_count_limit"]["error_code"], "daily_count_exceeded")
    return PASS
