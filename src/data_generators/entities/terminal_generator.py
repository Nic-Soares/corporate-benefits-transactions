import random

import polars as pl

from src.data_generators.providers import fake

GENERIC_MODEL = "POS Genérico"
TYPE_BY_MODEL = {
    "POS Cielo LIO": "POS",
    "TEF Rede": "TEF",
    "Stone Ton": "POS",
    "GetNet POS": "POS",
    "Moderninha Pro": "POS",
    "SafraPay POS": "POS",
    GENERIC_MODEL: "POS",
}


def generate_terminals(
    n_terminals: int,
    establishments_df: pl.DataFrame,
    acquirers_df: pl.DataFrame,
    business_data: dict,
) -> pl.DataFrame:
    """Terminals whose model belongs to their acquirer.

    Args:
        establishments_df: needs `id` and `accreditation_date` (installation comes after it)
        acquirers_df: needs `id` and `name`
        business_data: `pre_populated_data.yaml` (reads `terminal_models_by_acquirer`)
    """
    models_by_acquirer = business_data["terminal_models_by_acquirer"]
    acquirers = acquirers_df.select("id", "name").to_dicts()
    establishments = establishments_df.select("id", "accreditation_date").to_dicts()

    terminals = []
    for _ in range(n_terminals):
        acquirer = random.choice(acquirers)
        establishment = random.choice(establishments)
        model = random.choice(models_by_acquirer.get(acquirer["name"], [GENERIC_MODEL]))

        terminals.append(
            {
                "id": fake.new_id("term"),
                "establishment_id": establishment["id"],
                "acquirer_id": acquirer["id"],
                "model": model,
                "type": TYPE_BY_MODEL.get(model, "POS"),
                "status": fake.status("terminal"),
                "installation_date": fake.date_between(
                    establishment["accreditation_date"], fake.reference_date
                ),
            }
        )

    return pl.DataFrame(terminals)
