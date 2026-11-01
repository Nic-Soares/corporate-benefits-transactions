"""Disputes: what cardholders contest after the fact.

Most approved fraud is reported (`fraud.report_ratio`), card by card: the
cardholder contests every fraud on the card. Some legit approved purchases,
made with card and PIN, are contested too, by mistake or bad faith
(`friendly_disputes_per_fraud_dispute`): `disputed` without `is_fraud`, the
label noise a fraud team lives with.
"""

import random

import polars as pl

from src.utils.read_yamls import load_simulation_config

FRAUD = load_simulation_config()["fraud"]


def mark_disputes(transactions: pl.DataFrame) -> pl.DataFrame:
    approved = pl.col("response_code") == "00"
    fraud_cards = (
        transactions.filter(approved, pl.col("is_fraud"))["card_id"].unique().sort().to_list()
    )
    reporting = [card for card in fraud_cards if random.random() < FRAUD["report_ratio"]]
    reported = approved & pl.col("is_fraud") & pl.col("card_id").is_in(reporting)

    n_friendly = round(
        transactions.filter(reported).height * FRAUD["friendly_disputes_per_fraud_dispute"]
    )
    legit_with_pin = transactions.filter(
        approved,
        ~pl.col("is_fraud"),
        pl.col("transaction_type") == "purchase",
        pl.col("pin_status") == "ok",
    )["id"].to_list()
    friendly = random.sample(legit_with_pin, min(n_friendly, len(legit_with_pin)))

    return transactions.with_columns(disputed=reported | pl.col("id").is_in(friendly))
