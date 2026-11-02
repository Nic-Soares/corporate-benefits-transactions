"""Entity tables: generated, then written parents first."""

import polars as pl
import psycopg

from src.data_generators.entities.card_generator import CardGenerator
from src.data_generators.entities.card_wallet_generator import generate_card_wallets
from src.data_generators.entities.cardholder_generator import CardholderGenerator
from src.data_generators.entities.company_generator import CompanyGenerator
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.terminal_generator import generate_terminals
from src.infrastructure.database.postgres_manager import copy_dataframe
from src.utils.read_yamls import load_pre_populated_data

# Load order: each table after the ones it references
ENTITY_TABLES = ["companies", "cardholders", "cards", "card_wallets", "establishments", "terminals"]


def build_entities(
    volumes: dict, municipios: pl.DataFrame, cnae: pl.DataFrame
) -> dict[str, pl.DataFrame]:
    """Every entity table at `volumes` (`simulation_config.yaml → data_volumes`)."""
    companies = CompanyGenerator(municipios).generate_companies_as_dataframe(volumes["companies"])
    cardholders = CardholderGenerator(municipios).generate_cardholders_as_dataframe(
        companies, scale=volumes["cardholder_scale"]
    )
    cards = CardGenerator(cardholders).generate_cards_as_dataframe()
    establishments = generate_establishments(volumes["establishments"], cnae, municipios)
    return {
        "companies": companies,
        "cardholders": cardholders,
        "cards": cards,
        "card_wallets": generate_card_wallets(cards, cardholders),
        "establishments": establishments,
        "terminals": generate_terminals(
            volumes["terminals"], establishments, load_pre_populated_data()
        ),
    }


def load_entities(conn: psycopg.Connection, tables: dict[str, pl.DataFrame]) -> None:
    for table in ENTITY_TABLES:
        df = tables[table]
        if table == "companies":
            # Self-reference: holdings before their branches
            copy_dataframe(conn, table, df.filter(pl.col("parent_id").is_null()))
            copy_dataframe(conn, table, df.filter(pl.col("parent_id").is_not_null()))
        else:
            copy_dataframe(conn, table, df)
