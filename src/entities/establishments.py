import random

import polars as pl

from src.config import load_pre_populated_data, load_simulation_config
from src.entities import fake

# Category → {weight, cnae prefixes, online, atm, amount} (simulation_config.yaml)
CATEGORIES: dict[str, dict] = load_simulation_config()["establishment_categories"]
CNAE_MCC: dict[str, str] = load_pre_populated_data()["cnae_mcc"]


def longest_prefix(code: str, mapping: dict[str, object]) -> str | None:
    """The longest key of `mapping` that `code` starts with."""
    prefixes = [prefix for prefix in mapping if code.startswith(prefix)]
    return max(prefixes, key=len) if prefixes else None


def mcc_for(cnae: str) -> str:
    """The MCC an acquirer gives this activity (`cnae_mcc`, longest prefix)."""
    return CNAE_MCC[longest_prefix(cnae, CNAE_MCC)]


def generate_establishments(
    n_establishments: int,
    df_cnae: pl.DataFrame,
    municipios_df: pl.DataFrame,
) -> pl.DataFrame:
    """Establishments of the categories in `establishment_categories`, by weight.

    Each takes a CNAE subclass of its category and the MCC of that CNAE, so the
    CNAE rule (proprietary network) and the MCC rule (brands) describe the same
    business.

    Args:
        df_cnae: CNAE subclasses (`subclasse_id`); categories without any are skipped
        municipios_df: IBGE municipalities (`municipio_nome`, `uf_sigla`; with
            `population`, establishments follow where people live)
    """
    all_cnaes = df_cnae["subclasse_id"].to_list()
    cnaes_by_category = {
        name: [c for c in all_cnaes if any(c.startswith(p) for p in category["cnae"])]
        for name, category in CATEGORIES.items()
    }
    weights = {
        name: category["weight"] for name, category in CATEGORIES.items() if cnaes_by_category[name]
    }
    municipios = fake.Municipalities(municipios_df)

    establishments = []
    for _ in range(n_establishments):
        category = fake.weighted_key(weights)
        main_cnae = random.choice(cnaes_by_category[category])
        municipio = municipios.draw()
        legal_name, trade_name = fake.company_names(random.choice(CATEGORIES[category]["names"]))
        status = fake.status("establishment")
        accredited = fake.date_in_range("establishment_opening")
        establishments.append(
            {
                "id": fake.new_id("est"),
                "cnpj": fake.brazil.cnpj(),
                "name": legal_name,
                "trade_name": trade_name,
                "main_cnae": main_cnae,
                "mcc_code": mcc_for(main_cnae),
                "category": category,
                "city": municipio["municipio_nome"],
                "state": municipio["uf_sigla"],
                "status": status,
                "status_since": fake.status_since(status, accredited),
                "accreditation_date": accredited,
            }
        )

    return pl.DataFrame(establishments)
