"""Balance movements: the monthly credit, the debit of an approved attempt, a reversal."""

from datetime import datetime
from typing import Any

import polars as pl

from src.data_generators.providers import fake

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
    card_wallets_df: pl.DataFrame,
    card_wallet_id: str,
    amount: float,
    operation_type: str,
    moment: datetime,
    transaction_id: str | None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Add `amount` (negative to debit) to one card wallet; returns the wallets and the
    `balance_history` row."""
    is_wallet = pl.col("id") == card_wallet_id
    previous = card_wallets_df.filter(is_wallet)["current_balance"].item()
    posterior = round(previous + amount, 2)
    history = {
        "id": fake.new_id("balance"),
        "card_wallet_id": card_wallet_id,
        "transaction_id": transaction_id,
        "operation_type": operation_type,
        "operation_amount": abs(amount),
        "previous_balance": previous,
        "posterior_balance": posterior,
        "operation_date": moment,
    }
    updated = card_wallets_df.with_columns(
        current_balance=pl.when(is_wallet)
        .then(pl.lit(posterior))
        .otherwise(pl.col("current_balance"))
    )
    return updated, history


def debit(
    card_wallets_df: pl.DataFrame, transaction: dict[str, Any]
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Debit an approved purchase or withdrawal from the card wallet it was routed to."""
    return _move(
        card_wallets_df,
        transaction["card_wallet_id"],
        -transaction["amount"],
        transaction["transaction_type"],
        transaction.get("date") or datetime.now(),
        transaction["id"],
    )


def reverse(
    card_wallets_df: pl.DataFrame, reversal: dict[str, Any]
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Give back a reversed purchase to its card wallet."""
    return _move(
        card_wallets_df,
        reversal["card_wallet_id"],
        reversal["amount"],
        "reversal",
        reversal["date"],
        reversal["id"],
    )


def credit(
    card_wallets_df: pl.DataFrame, card_wallet_id: str, moment: datetime
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Credit one wallet's `monthly_credit` (the benefit landing on the credit day)."""
    amount = card_wallets_df.filter(id=card_wallet_id)["monthly_credit"].item()
    return _move(card_wallets_df, card_wallet_id, amount, "credit", moment, None)


def credit_many(
    card_wallets_df: pl.DataFrame, card_wallet_ids: list[str], moment: datetime
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """`credit` for many wallets at once; returns the wallets and the `balance_history` rows."""
    credited = card_wallets_df.filter(pl.col("id").is_in(card_wallet_ids)).select(
        "id", "current_balance", "monthly_credit"
    )
    history = pl.DataFrame(
        {
            "id": [fake.new_id("balance") for _ in range(credited.height)],
            "card_wallet_id": credited["id"],
            "transaction_id": [None] * credited.height,
            "operation_type": ["credit"] * credited.height,
            "operation_amount": credited["monthly_credit"],
            "previous_balance": credited["current_balance"],
            "posterior_balance": (credited["current_balance"] + credited["monthly_credit"]).round(
                2
            ),
            "operation_date": [moment] * credited.height,
        },
        schema=HISTORY_SCHEMA,
    )
    updated = card_wallets_df.update(
        history.select(pl.col("card_wallet_id").alias("id"), current_balance="posterior_balance"),
        on="id",
    )
    return updated, history
