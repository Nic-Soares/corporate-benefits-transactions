"""`setup`: schema, reference data and entities in the OLTP database."""

import logging
from datetime import date

import psycopg

from src.data_generators.providers import fake
from src.infrastructure.database.postgres_manager import count_rows, run_sql_file
from src.pipeline import provenance
from src.pipeline.entities import ENTITY_TABLES, build_entities, load_entities
from src.pipeline.reference import REFERENCE_KEYS, build_reference_tables, load_reference_tables
from src.pipeline.sources import Sources
from src.utils.read_yamls import CONFIG_DIR, load_database

log = logging.getLogger(__name__)

OLTP_SCHEMA = CONFIG_DIR.parent / load_database()["oltp_postgres"]["schema"]
# Cleared by --reset, children first
SIMULATED_TABLES = ["balance_history", "transactions"]


class SetupError(Exception):
    pass


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
    the same database. With entities already there it stops, unless `reset`
    clears them (and the simulated tables) first. Doesn't commit.
    Returns the row count of every table.
    """
    run_sql_file(conn, OLTP_SCHEMA)
    log.info("Schema ready")

    load_reference_tables(conn, build_reference_tables(sources.cnae, sources.mcc))
    log.info("Reference tables loaded")

    if count_rows(conn, "companies"):
        if not reset:
            raise SetupError("The database already has entities; run with --reset to replace them")
        tables = ", ".join(SIMULATED_TABLES + ENTITY_TABLES[::-1])
        conn.execute(f"TRUNCATE {tables}")
        log.info("Entities and simulated tables cleared")

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
        sources=provenance.source_hashes(),
    )

    tables = [*REFERENCE_KEYS, *ENTITY_TABLES, *SIMULATED_TABLES]
    return {table: count_rows(conn, table) for table in tables}
