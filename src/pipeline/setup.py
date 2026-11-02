"""`setup`: schema, reference data and the generated entities in the OLTP database."""

import logging
import re
from datetime import date

import polars as pl
import psycopg

from src.config import ROOT, load_database, load_pre_populated_data
from src.entities import fake
from src.entities.card_wallets import generate_card_wallets
from src.entities.cardholders import CardholderGenerator
from src.entities.cards import CardGenerator
from src.entities.companies import CompanyGenerator
from src.entities.establishments import generate_establishments
from src.entities.terminals import generate_terminals
from src.pipeline import provenance
from src.postgres import copy_dataframe, count_rows, run_sql_file
from src.reference import REFERENCE_KEYS, build_reference_tables, load_reference_tables
from src.sources import Sources

log = logging.getLogger(__name__)

OLTP_SCHEMA = ROOT / load_database()["oltp_postgres"]["schema"]
# Filled by simulate (counted in the summary)
SIMULATED_TABLES = ["balance_history", "transactions"]


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


class SetupError(Exception):
    pass


def schema_tables() -> list[str]:
    """The tables `oltp_schema.sql` creates."""
    return re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", OLTP_SCHEMA.read_text())


def run_setup(
    conn: psycopg.Connection,
    sources: Sources,
    volumes: dict,
    seed: int,
    today: date,
    reset: bool = False,
) -> dict[str, int]:
    """Create the schema, upsert the reference tables, generate and write the entities.

    The entities are generated from `seed` and `today`, so the same pair gives
    the same database. With entities already there it stops, unless `reset`,
    which drops every table of the schema and creates it again (a changed
    schema needs nothing else). Doesn't commit.
    Returns the row count of every table.
    """
    if reset:
        tables = ", ".join(schema_tables())
        conn.execute(f"DROP TABLE IF EXISTS {tables} CASCADE")
        log.info("Tables dropped")
    run_sql_file(conn, OLTP_SCHEMA)
    log.info("Schema ready")

    load_reference_tables(conn, build_reference_tables(sources.cnae, sources.mcc))
    log.info("Reference tables loaded")

    if count_rows(conn, "companies"):
        raise SetupError("The database already has entities; run with --reset to replace them")

    fake.seed(seed, today=today)
    load_entities(conn, build_entities(volumes, sources.municipios, sources.cnae))
    log.info("Entities generated (seed %s, reference day %s)", seed, today)
    conn.execute("TRUNCATE run_metadata")
    provenance.record(
        conn,
        seed=seed,
        reference_date=today,
        setup_code_version=provenance.code_version(),
        setup_config_hash=provenance.config_hash(),
        config_dir=provenance.config_dir(),
        data_volumes=volumes,
        sources=provenance.source_hashes(),
    )

    tables = [*REFERENCE_KEYS, *ENTITY_TABLES, *SIMULATED_TABLES]
    return {table: count_rows(conn, table) for table in tables}
