import random

import polars as pl

from src.data_generators.providers import fake

# Category of an establishment, from the first wallet its CNAE accepts.
# Matches the categories of `usage_patterns.peak_hours_by_category`.
CATEGORY_BY_WALLET = {
    "MEAL": "restaurant",
    "FOOD": "supermarket",
    "MOBILITY": "mobility",
    "HEALTH": "health",
    "HOME_OFFICE": "home_office",
    "EDUCATION": "education",
}
DEFAULT_CATEGORY = "retail"


def _accepted_wallets(cnae: str, cnae_wallets_mapping: dict[str, list[str]]) -> list[str]:
    """Wallets of the longest CNAE prefix in the mapping (same rule as the validator)."""
    prefixes = [prefix for prefix in cnae_wallets_mapping if cnae.startswith(prefix)]
    return cnae_wallets_mapping[max(prefixes, key=len)] if prefixes else []


def generate_establishments(
    n_establishments: int,
    df_cnae: pl.DataFrame,
    df_mcc: pl.DataFrame,
    municipios_df: pl.DataFrame,
    cnae_wallets_mapping: dict[str, list[str]],
    cnae_with_wallets_ratio: float = fake.SETTINGS["cnae_with_wallets_ratio"],
) -> pl.DataFrame:
    """Establishments, most of them with a CNAE that accepts some wallet.

    Args:
        df_cnae: CNAE codes (`subclasse_id`)
        df_mcc: MCC codes (`mcc_code`)
        municipios_df: IBGE municipalities (`municipio_nome`, `uf_sigla`)
        cnae_wallets_mapping: CNAE prefix → accepted wallets (`cnae_wallets` in
            `pre_populated_data.yaml`)
        cnae_with_wallets_ratio: share of establishments whose CNAE accepts a wallet
    """
    all_cnaes = df_cnae["subclasse_id"].to_list()
    cnaes_with_wallets = [
        cnae for cnae in all_cnaes if _accepted_wallets(cnae, cnae_wallets_mapping)
    ]
    n_with_wallets = int(n_establishments * cnae_with_wallets_ratio)

    mcc_codes = df_mcc["mcc_code"].to_list()
    municipios = (
        municipios_df.select("municipio_nome", "uf_sigla").unique(maintain_order=True).to_dicts()
    )

    establishments = []
    for i in range(n_establishments):
        if i < n_with_wallets and cnaes_with_wallets:
            main_cnae = random.choice(cnaes_with_wallets)
        else:
            main_cnae = random.choice(all_cnaes)
        wallets = _accepted_wallets(main_cnae, cnae_wallets_mapping)
        municipio = random.choice(municipios)

        establishments.append(
            {
                "id": fake.new_id("est"),
                "cnpj": fake.brazil.cnpj(),
                "name": fake.finance.company(),
                "trade_name": f"{fake.finance.company()} {fake.person.surname()}",
                "main_cnae": main_cnae,
                "mcc_code": random.choice(mcc_codes),
                "category": CATEGORY_BY_WALLET.get(wallets[0], DEFAULT_CATEGORY)
                if wallets
                else DEFAULT_CATEGORY,
                "city": municipio["municipio_nome"],
                "state": municipio["uf_sigla"],
                "status": fake.status("establishment"),
                "accreditation_date": fake.date_in_range("establishment_opening"),
            }
        )

    return pl.DataFrame(establishments)
