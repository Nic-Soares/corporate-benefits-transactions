import random

import polars as pl

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.providers import fake

PHYSICAL_TYPES = ("POS", "TEF")
ATM_NETWORK = "ATM"  # acquirer id of the cash machines


def _terminal_type(category: str) -> str:
    if CATEGORIES[category].get("atm"):
        return "ATM"
    if CATEGORIES[category].get("online"):
        return "ECOMMERCE"
    return "PHYSICAL"


def generate_terminals(
    n_terminals: int,
    establishments_df: pl.DataFrame,
    business_data: dict,
) -> pl.DataFrame:
    """At least one terminal per establishment, of the kind its category uses.

    Shops get a POS or TEF of an acquirer drawn by `acquirer_distribution`;
    online businesses an acquirer's e-commerce gateway; cash machines the ATM
    network. The model (and its type) belongs to the acquirer.

    Args:
        establishments_df: needs `id`, `category` and `accreditation_date`
            (installation comes after it)
        business_data: `pre_populated_data.yaml` — reads `terminal_models_by_acquirer`,
            acquirer id → list of `{model, type}`
    """
    models_by_acquirer = business_data["terminal_models_by_acquirer"]

    def models(acquirer_id: str, kind: str) -> list[dict]:
        types = PHYSICAL_TYPES if kind == "PHYSICAL" else (kind,)
        return [m for m in models_by_acquirer.get(acquirer_id, []) if m["type"] in types]

    acquirer_weights = fake.SETTINGS["acquirer_distribution"]
    establishments = establishments_df.select("id", "category", "accreditation_date").to_dicts()
    extra = [random.choice(establishments) for _ in range(n_terminals - len(establishments))]

    terminals = []
    for establishment in establishments + extra:
        kind = _terminal_type(establishment["category"])
        if kind == "ATM":
            acquirer_id = ATM_NETWORK
        else:
            weights = {a: w for a, w in acquirer_weights.items() if models(a, kind)}
            acquirer_id = fake.weighted_key(weights)
        terminal_model = random.choice(models(acquirer_id, kind))
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
