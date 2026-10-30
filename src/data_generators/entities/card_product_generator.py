import random

import polars as pl

from src.data_generators.providers import fake


def generate_card_products(
    cards_df: pl.DataFrame, products_df: pl.DataFrame, min_products: int = 1, max_products: int = 3
) -> pl.DataFrame:
    """Each card gets between `min_products` and `max_products` distinct products.

    `cards_df` needs `id` and `issue_date` (activation comes after it);
    `products_df` needs `id`.
    """
    product_ids = products_df["id"].to_list()

    card_products = []
    for card in cards_df.select("id", "issue_date").iter_rows(named=True):
        n_products = min(random.randint(min_products, max_products), len(product_ids))
        for product_id in random.sample(product_ids, n_products):
            card_products.append(
                {
                    "id": fake.new_id("card_product"),
                    "card_id": card["id"],
                    "product_id": product_id,
                    "current_balance": round(random.uniform(0, 5000), 2),
                    "daily_limit": round(random.uniform(100, 2000), 2),
                    "monthly_limit": round(random.uniform(1000, 10000), 2),
                    "activation_date": fake.date_between(card["issue_date"], fake.reference_date),
                    "status": fake.status("card_product"),
                }
            )

    return pl.DataFrame(card_products)
