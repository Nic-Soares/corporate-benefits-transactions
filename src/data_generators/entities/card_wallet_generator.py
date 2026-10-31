import random

import polars as pl

from src.data_generators.providers import fake
from src.utils.read_yamls import load_pre_populated_data

WALLETS_BY_PROGRAM = {
    program["id"]: program["wallets"] for program in load_pre_populated_data()["card_programs"]
}
WALLET_SETTINGS: dict[str, dict] = fake.SETTINGS["wallets"]


def generate_card_wallets(cards_df: pl.DataFrame) -> pl.DataFrame:
    """Every wallet of each card's program, with its monthly credit, balance and limits.

    `cards_df` needs `id`, `program_id` and `issue_date` (activation comes after it).
    Per wallet: `generation_settings.wallets` (credit range and limits); the
    starting balance is a share of the credit (`starting_balance_ratio`).
    """
    ratio = fake.SETTINGS["starting_balance_ratio"]
    card_wallets = []
    for card in cards_df.select("id", "program_id", "issue_date").iter_rows(named=True):
        for wallet_id in WALLETS_BY_PROGRAM[card["program_id"]]:
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
                    "activation_date": fake.date_between(card["issue_date"], fake.reference_date),
                    "status": fake.status("card_wallet"),
                }
            )
    return pl.DataFrame(card_wallets)
