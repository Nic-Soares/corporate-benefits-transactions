import random
from datetime import datetime

import polars as pl
from mimesis import Datetime, Person
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)


def generate_terminals(n_terminals, establishments_df, acquirers_df, business_data):
    """Generate terminals for establishments with correct model/acquirer/type relation"""
    person = Person(Locale.PT_BR)

    models_by_acquirer = business_data["terminal_models_by_acquirer"]
    model_type_map = {
        "POS Cielo LIO": "POS",
        "TEF Rede": "TEF",
        "Stone Ton": "POS",
        "GetNet POS": "POS",
        "Moderninha Pro": "POS",
        "SafraPay POS": "POS",
        "POS Genérico": "POS",
    }

    # Pre-select data
    acquirer_names = acquirers_df["name"].to_list()
    establishment_ids = establishments_df["establishment_id"].to_list()
    statuses = ["active", "inactive", "maintenance"]

    # Create acquirer lookup dict for performance
    acquirer_lookup = {row["name"]: row["acquirer_id"] for row in acquirers_df.to_dicts()}

    terminals = []
    for i in range(n_terminals):
        acquirer_name = random.choice(acquirer_names)
        terminal_model = random.choice(models_by_acquirer.get(acquirer_name, ["POS Genérico"]))
        terminal_type = model_type_map.get(terminal_model, "POS")

        terminals.append(
            {
                "terminal_id": f"TERM_{i}",
                "terminal_code": f"T{random.randint(100000, 999999)}",
                "establishment_id": random.choice(establishment_ids),
                "acquirer_id": acquirer_lookup[acquirer_name],
                "terminal_model": terminal_model,
                "terminal_type": terminal_type,
                "status": random.choice(statuses),
                "installation_date": datetime_provider.date(start=2021, end=2024),
                "created_at": datetime.now(),
            }
        )

    return pl.DataFrame(terminals)
