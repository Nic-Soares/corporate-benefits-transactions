"""Balance movements: the monthly credit, the debit of an approved attempt, a reversal.

The card wallets are a `Table`: each movement changes the wallet's
`current_balance` in place and returns its `balance_history` row.
"""

from datetime import datetime
from typing import Any

import polars as pl

from src.data_generators.providers import fake
from src.validators._common import Table, find_one

# Columns of `balance_history`
HISTORY_SCHEMA = {
    "id": pl.String,
    "card_wallet_id": pl.String,
    "transaction_id": pl.String,
    "operation_type": pl.String,
    "operation_amount": pl.Float64,
    "previous_balance": pl.Float64,
    "posterior_balance": pl.Float64,
    "operation_date": pl.Datetime("us"),
}


def _move(
    card_wallets: Table,
    card_wallet_id: str,
    amount: float,
    operation_type: str,
    moment: datetime,
    transaction_id: str | None,
) -> dict[str, Any]:
    """Add `amount` (negative to debit) to one card wallet; returns the
    `balance_history` row."""
    card_wallet = find_one(card_wallets, id=card_wallet_id)
    previous = card_wallet["current_balance"]
    posterior = round(previous + amount, 2)
    card_wallet["current_balance"] = posterior
    return {
        "id": fake.new_id("balance"),
        "card_wallet_id": card_wallet_id,
        "transaction_id": transaction_id,
        "operation_type": operation_type,
        "operation_amount": abs(amount),
        "previous_balance": previous,
        "posterior_balance": posterior,
        "operation_date": moment,
    }


def debit(card_wallets: Table, transaction: dict[str, Any]) -> dict[str, Any]:
    """Debit an approved purchase or withdrawal from the card wallet it was routed to."""
    return _move(
        card_wallets,
        transaction["card_wallet_id"],
        -transaction["amount"],
        transaction["transaction_type"],
        transaction.get("date") or datetime.now(),
        transaction["id"],
    )


def reverse(card_wallets: Table, reversal: dict[str, Any]) -> dict[str, Any]:
    """Give back a reversed purchase to its card wallet."""
    return _move(
        card_wallets,
        reversal["card_wallet_id"],
        reversal["amount"],
        "reversal",
        reversal["date"],
        reversal["id"],
    )


def credit(
    card_wallets: Table, card_wallet_id: str, moment: datetime, amount: float | None = None
) -> dict[str, Any]:
    """Credit one wallet: `amount`, by default its `monthly_credit` (the benefit
    landing on the credit day)."""
    if amount is None:
        amount = find_one(card_wallets, id=card_wallet_id)["monthly_credit"]
    return _move(card_wallets, card_wallet_id, amount, "credit", moment, None)
