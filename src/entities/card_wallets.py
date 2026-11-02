import random
from datetime import date, timedelta

import polars as pl

from src.config import load_reference
from src.entities import fake

WALLETS_BY_PROGRAM = {
    program["id"]: program["wallets"] for program in load_reference()["card_programs"]
}
WALLET_SETTINGS: dict[str, dict] = fake.SETTINGS["wallets"]


def draw_program_wallets(program_id: str) -> list[str]:
    """The wallets a company gives on a program: each allowed wallet with its share
    (`program_wallet_shares`; a wallet not listed always). Never empty."""
    allowed = WALLETS_BY_PROGRAM[program_id]
    shares = fake.SETTINGS["program_wallet_shares"]
    chosen = [w for w in allowed if random.random() < shares.get(w, 1.0)]
    return chosen or [max(allowed, key=lambda w: shares.get(w, 1.0))]


def activation_date(issue_date: date) -> date:
    """A few days after the issue (`wallet_activation_days`), no later than today."""
    days = fake.SETTINGS["wallet_activation_days"]
    delay = timedelta(days=random.randint(days["min"], days["max"]))
    return min(issue_date + delay, fake.reference_date)


def generate_card_wallets(cards_df: pl.DataFrame, cardholders_df: pl.DataFrame) -> pl.DataFrame:
    """The wallets of each card, with its monthly credit, balance and limits.

    `cards_df` needs `id`, `cardholder_id`, `program_id` and `issue_date`;
    `cardholders_df` needs `id` and `company_id`. Each company draws, per program,
    the wallets it gives (`draw_program_wallets`) and all its cards get them.
    Per wallet: `generation_settings.wallets` (credit range and limits); the
    starting balance is a share of the credit (`starting_balance_ratio`).
    """
    ratio = fake.SETTINGS["starting_balance_ratio"]
    company_of = dict(cardholders_df.select("id", "company_id").iter_rows())
    given: dict[tuple[str, str], list[str]] = {}
    card_wallets = []
    for card in cards_df.select("id", "cardholder_id", "program_id", "issue_date").iter_rows(
        named=True
    ):
        key = (company_of[card["cardholder_id"]], card["program_id"])
        if key not in given:
            given[key] = draw_program_wallets(card["program_id"])
        activated = activation_date(card["issue_date"])
        for wallet_id in given[key]:
            status = fake.status("card_wallet")
            settings = WALLET_SETTINGS[wallet_id]
            credit = settings["monthly_credit"]
            monthly_credit = round(random.uniform(credit["min"], credit["max"]) / 10) * 10.0
            card_wallets.append(
                {
                    "id": fake.new_id("card_wallet"),
                    "card_id": card["id"],
                    "wallet_id": wallet_id,
                    "current_balance": round(
                        monthly_credit * random.uniform(ratio["min"], ratio["max"]), 2
                    ),
                    "monthly_credit": monthly_credit,
                    "daily_limit": float(settings["daily_limit"]),
                    "monthly_limit": float(settings["monthly_limit"]),
                    "daily_count_limit": settings["daily_count_limit"],
                    "activation_date": activated,
                    "status": status,
                    "status_since": fake.status_since(status, activated),
                }
            )
    return pl.DataFrame(card_wallets)
