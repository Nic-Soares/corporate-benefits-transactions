import random
from datetime import datetime, timedelta

import polars as pl

from src.data_generators.providers import fake

CAPTURE_TYPES = ["chip", "magnetic_stripe", "contactless", "nfc"]


def transaction_amount(max_amount: float = 1000, scale: float = 250) -> float:
    """Exponentially distributed: larger amounts are rarer."""
    return round(min(random.expovariate(1 / scale), max_amount), 2)


def generate_single_transaction(
    card_products_df: pl.DataFrame, terminals_df: pl.DataFrame, days_back: int = 30
) -> dict:
    """One purchase attempt, not yet validated (`response_code` is empty).

    Picks a card product (so the card has the product it pays with) and a
    terminal (so the establishment has a terminal). Columns of `transactions`.
    """
    card_product = (
        card_products_df.select("card_id", "product_id")
        .sample(1, seed=random.getrandbits(32))
        .row(0, named=True)
    )
    terminal = (
        terminals_df.select("id", "establishment_id")
        .sample(1, seed=random.getrandbits(32))
        .row(0, named=True)
    )

    end = datetime.combine(fake.reference_date, datetime.min.time())
    moment = end - timedelta(seconds=random.randint(0, days_back * 24 * 3600))

    return {
        "id": fake.new_id("tx"),
        "card_id": card_product["card_id"],
        "product_id": card_product["product_id"],
        "establishment_id": terminal["establishment_id"],
        "terminal_id": terminal["id"],
        "amount": transaction_amount(max_amount=500, scale=100),
        "date": moment,
        "capture_type": random.choice(CAPTURE_TYPES),
        "response_code": None,
        "response_message": None,
    }
