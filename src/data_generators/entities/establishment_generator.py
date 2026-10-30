import random

import polars as pl

from src.data_generators.providers import fake

# Category of an establishment, from the first product its CNAE accepts.
# Matches the categories of `usage_patterns.peak_hours_by_category`.
CATEGORY_BY_PRODUCT = {
    "VR": "restaurant",
    "VA": "supermarket",
    "VC": "gas_station",
    "VF": "pharmacy",
}
DEFAULT_CATEGORY = "other"


def _accepted_products(cnae: str, cnae_products_mapping: dict[str, list[str]]) -> list[str]:
    """Products of the longest CNAE prefix in the mapping (same rule as the validator)."""
    prefixes = [prefix for prefix in cnae_products_mapping if cnae.startswith(prefix)]
    return cnae_products_mapping[max(prefixes, key=len)] if prefixes else []


def generate_establishments(
    n_establishments: int,
    df_cnae: pl.DataFrame,
    df_mcc: pl.DataFrame,
    municipios_df: pl.DataFrame,
    cnae_products_mapping: dict[str, list[str]],
    cnae_with_products_ratio: float = fake.SETTINGS["cnae_with_products_ratio"],
) -> pl.DataFrame:
    """Establishments, most of them with a CNAE that accepts some product.

    Args:
        df_cnae: CNAE codes (`subclasse_id`)
        df_mcc: MCC codes (`mcc_code`)
        municipios_df: IBGE municipalities (`municipio_nome`, `uf_sigla`)
        cnae_products_mapping: CNAE prefix → accepted products (`cnae_products` in
            `pre_populated_data.yaml`)
        cnae_with_products_ratio: share of establishments whose CNAE accepts a product
    """
    all_cnaes = df_cnae["subclasse_id"].to_list()
    cnaes_with_products = [
        cnae for cnae in all_cnaes if _accepted_products(cnae, cnae_products_mapping)
    ]
    n_with_products = int(n_establishments * cnae_with_products_ratio)

    mcc_codes = df_mcc["mcc_code"].to_list()
    municipios = (
        municipios_df.select("municipio_nome", "uf_sigla").unique(maintain_order=True).to_dicts()
    )

    establishments = []
    for i in range(n_establishments):
        if i < n_with_products and cnaes_with_products:
            main_cnae = random.choice(cnaes_with_products)
        else:
            main_cnae = random.choice(all_cnaes)
        products = _accepted_products(main_cnae, cnae_products_mapping)
        municipio = random.choice(municipios)

        establishments.append(
            {
                "id": fake.new_id("est"),
                "cnpj": fake.brazil.cnpj(),
                "name": fake.finance.company(),
                "trade_name": f"{fake.finance.company()} {fake.person.surname()}",
                "main_cnae": main_cnae,
                "mcc_code": random.choice(mcc_codes),
                "category": CATEGORY_BY_PRODUCT.get(products[0], DEFAULT_CATEGORY)
                if products
                else DEFAULT_CATEGORY,
                "city": municipio["municipio_nome"],
                "state": municipio["uf_sigla"],
                "status": fake.status("establishment"),
                "accreditation_date": fake.date_in_range("establishment_opening"),
            }
        )

    return pl.DataFrame(establishments)
