"""Balance and limit validations on the wallet being charged."""

from typing import Any

import polars as pl

from src.validators._common import PASS, RULES, fail, find_one, not_found

BALANCE_RULES = RULES["balance_and_limits_validations"]


def _card_wallet(transaction: dict[str, Any], card_wallets_df: pl.DataFrame):
    return find_one(
        card_wallets_df, card_id=transaction["card_id"], wallet_id=transaction["wallet_id"]
    )


def validate_current_balance(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame
) -> dict[str, Any]:
    card_wallet = _card_wallet(transaction, card_wallets_df)
    if card_wallet is None:
        return not_found("card_wallet")
    if card_wallet["current_balance"] < transaction["amount"]:
        return fail(BALANCE_RULES["current_balance"]["error_code"], "insufficient_balance")
    return PASS


def _within_limit(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame, usage: float, rule_name: str
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
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame, daily_usage: float = 0
) -> dict[str, Any]:
    """`daily_usage`: amount already spent on this wallet today."""
    return _within_limit(transaction, card_wallets_df, daily_usage, "daily_limit")


def validate_monthly_limit(
    transaction: dict[str, Any], card_wallets_df: pl.DataFrame, monthly_usage: float = 0
) -> dict[str, Any]:
    """`monthly_usage`: amount already spent on this wallet this month."""
    return _within_limit(transaction, card_wallets_df, monthly_usage, "monthly_limit")
