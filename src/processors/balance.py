"""Balance movements: an approved purchase debits the wallet it was charged to."""

from datetime import datetime
from typing import Any

import polars as pl

from src.data_generators.providers import fake


def debit(
    card_wallets_df: pl.DataFrame, transaction: dict[str, Any]
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Debit an approved purchase from its wallet.

    Returns the card wallets with the new balance and the `balance_history` row.
    The transaction must already carry the charged `card_wallet_id`.
    """
    is_wallet = pl.col("id") == transaction["card_wallet_id"]
    card_wallet = card_wallets_df.filter(is_wallet).row(0, named=True)
    previous = card_wallet["current_balance"]
    posterior = round(previous - transaction["amount"], 2)

    history = {
        "id": fake.new_id("balance"),
        "card_wallet_id": card_wallet["id"],
        "transaction_id": transaction["id"],
        "operation_type": "purchase",
        "operation_amount": transaction["amount"],
        "previous_balance": previous,
        "posterior_balance": posterior,
        "operation_date": transaction.get("date") or datetime.now(),
    }
    updated = card_wallets_df.with_columns(
        current_balance=pl.when(is_wallet)
        .then(pl.lit(posterior))
        .otherwise(pl.col("current_balance"))
    )
    return updated, history
