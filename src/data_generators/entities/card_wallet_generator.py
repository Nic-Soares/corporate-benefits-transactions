import polars as pl

from src.data_generators.providers import fake
from src.utils.read_yamls import load_pre_populated_data

WALLETS_BY_PROGRAM = {
    program["id"]: program["wallets"] for program in load_pre_populated_data()["card_programs"]
}


def generate_card_wallets(cards_df: pl.DataFrame) -> pl.DataFrame:
    """Every wallet of each card's program, with a starting balance and limits.

    `cards_df` needs `id`, `program_id` and `issue_date` (activation comes after it).
    Ranges: `generation_settings.wallet_starting_balance`, `wallet_daily_limit`,
    `wallet_monthly_limit`.
    """
    card_wallets = [
        {
            "id": fake.new_id("card_wallet"),
            "card_id": card["id"],
            "wallet_id": wallet_id,
            "current_balance": fake.amount_between("wallet_starting_balance"),
            "daily_limit": fake.amount_between("wallet_daily_limit"),
            "monthly_limit": fake.amount_between("wallet_monthly_limit"),
            "activation_date": fake.date_between(card["issue_date"], fake.reference_date),
            "status": fake.status("card_wallet"),
        }
        for card in cards_df.select("id", "program_id", "issue_date").iter_rows(named=True)
        for wallet_id in WALLETS_BY_PROGRAM[card["program_id"]]
    ]
    return pl.DataFrame(card_wallets)
