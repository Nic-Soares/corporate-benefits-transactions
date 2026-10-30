import random
from datetime import datetime, timedelta

import polars as pl

from src.data_generators.providers import fake
from src.utils.read_yamls import load_pre_populated_data

_REFERENCE = load_pre_populated_data()
CAPTURE_TYPES = [t["code"] for t in _REFERENCE["transaction_technologies"]]
PIN_CAPTURES = {"CHIP", "MAG_STRIPE"}
PROPRIETARY_MODALITIES = {
    m["id"] for m in _REFERENCE["transaction_modalities"] if m["type"] == "proprietary_network"
}


def transaction_amount(max_amount: float = 1000, scale: float = 250) -> float:
    """Exponentially distributed: larger amounts are rarer."""
    return round(min(random.expovariate(1 / scale), max_amount), 2)


def pin_status(capture_type: str) -> str:
    """`ok` or `wrong` when the capture asks for a PIN, `not_required` otherwise."""
    if capture_type not in PIN_CAPTURES:
        return "not_required"
    return "wrong" if random.random() < fake.SETTINGS["wrong_pin_ratio"] else "ok"


def generate_single_transaction(
    cards_df: pl.DataFrame,
    card_wallets_df: pl.DataFrame,
    terminals_df: pl.DataFrame,
    days_back: int = 30,
) -> dict:
    """One purchase attempt, not yet validated (`response_code` is empty).

    Picks a card and a terminal (so the establishment has one). On the
    proprietary network the cardholder picks one of the card's wallets on the
    terminal; on a brand card `wallet_id` stays empty until the issuer routes
    it by MCC. Columns of `transactions`.
    """
    card = cards_df.select("id", "modality_id").sample(1, seed=random.getrandbits(32))
    card = card.row(0, named=True)
    terminal = terminals_df.select("id", "establishment_id").sample(1, seed=random.getrandbits(32))
    terminal = terminal.row(0, named=True)

    wallet_id = None
    if card["modality_id"] in PROPRIETARY_MODALITIES:
        wallets = card_wallets_df.filter(card_id=card["id"])["wallet_id"].to_list()
        wallet_id = random.choice(wallets)

    end = datetime.combine(fake.reference_date, datetime.min.time())
    moment = end - timedelta(seconds=random.randint(0, days_back * 24 * 3600))
    capture_type = random.choice(CAPTURE_TYPES)

    return {
        "id": fake.new_id("tx"),
        "card_id": card["id"],
        "wallet_id": wallet_id,
        "establishment_id": terminal["establishment_id"],
        "terminal_id": terminal["id"],
        "amount": transaction_amount(max_amount=500, scale=100),
        "date": moment,
        "capture_type": capture_type,
        "pin_status": pin_status(capture_type),
        "response_code": None,
        "response_message": None,
        "decline_reason": None,
    }
