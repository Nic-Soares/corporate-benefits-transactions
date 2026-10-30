import random

import polars as pl

from src.data_generators.providers import fake


def generate_terminals(
    n_terminals: int,
    establishments_df: pl.DataFrame,
    acquirers_df: pl.DataFrame,
    business_data: dict,
) -> pl.DataFrame:
    """Terminals whose model (and its type) belongs to their acquirer.

    Args:
        establishments_df: needs `id` and `accreditation_date` (installation comes after it)
        acquirers_df: needs `id`
        business_data: `pre_populated_data.yaml` — reads `terminal_models_by_acquirer`,
            acquirer id → list of `{model, type}`
    """
    models_by_acquirer = business_data["terminal_models_by_acquirer"]
    acquirer_ids = [a for a in acquirers_df["id"].to_list() if a in models_by_acquirer]
    establishments = establishments_df.select("id", "accreditation_date").to_dicts()

    terminals = []
    for _ in range(n_terminals):
        acquirer_id = random.choice(acquirer_ids)
        establishment = random.choice(establishments)
        terminal_model = random.choice(models_by_acquirer[acquirer_id])

        terminals.append(
            {
                "id": fake.new_id("term"),
                "establishment_id": establishment["id"],
                "acquirer_id": acquirer_id,
                "model": terminal_model["model"],
                "type": terminal_model["type"],
                "status": fake.status("terminal"),
                "installation_date": fake.date_between(
                    establishment["accreditation_date"], fake.reference_date
                ),
            }
        )

    return pl.DataFrame(terminals)
