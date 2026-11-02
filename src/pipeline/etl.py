"""`etl`: the OLTP database into the DuckDB star schema.

The OLTP tables are staged in DuckDB as `stg_<table>` and transformed by
plain SQL (`database/olap_duck/03_load.sql`); `04_views.sql` adds the
analytical views. Full refresh: a new database file each run.
"""

import logging
from pathlib import Path

import duckdb
import polars as pl
import psycopg

from src.infrastructure.database.postgres_manager import read_table
from src.utils.read_yamls import CONFIG_DIR, load_database

log = logging.getLogger(__name__)

ROOT = CONFIG_DIR.parent
OLAP_DIR = ROOT / "database" / "olap_duck"
OLAP_SQL = ["01_dimensions.sql", "02_facts.sql", "03_load.sql", "04_views.sql"]
OLAP_FILE = ROOT / load_database()["olap_duck"]["file_path"]

# OLTP tables the load reads
STAGED = [
    "wallets",
    "card_programs",
    "transaction_modalities",
    "acquirers",
    "response_codes",
    "card_program_wallets",
    "companies",
    "cardholders",
    "cards",
    "card_wallets",
    "establishments",
    "terminals",
    "transactions",
    "balance_history",
    "cnae_wallets",
    "mcc_wallets",
    "mcc_modalities",
]
OLAP_TABLES = [
    "dim_wallets",
    "dim_card_programs",
    "dim_transaction_modalities",
    "dim_acquirers",
    "dim_companies",
    "dim_cardholders",
    "dim_cards",
    "dim_card_wallets",
    "dim_establishments",
    "dim_terminals",
    "fact_transactions",
    "fact_balance_movements",
    "ref_response_codes",
    "ref_program_wallets",
    "ref_cnae_wallets",
    "ref_mcc_wallets",
    "ref_mcc_modalities",
]


def build_olap(duck: duckdb.DuckDBPyConnection, oltp: dict[str, pl.DataFrame]) -> dict[str, int]:
    """Create the star schema in `duck` and load it from the OLTP tables.
    Returns the row count of every OLAP table."""
    for table in STAGED:
        duck.register(f"stg_{table}", oltp[table])
    for name in OLAP_SQL:
        duck.execute((OLAP_DIR / name).read_text())
    for table in STAGED:
        duck.unregister(f"stg_{table}")
    return {
        table: duck.sql(f"SELECT count(*) FROM {table}").fetchall()[0][0] for table in OLAP_TABLES
    }


def run_etl(pg: psycopg.Connection, path: Path = OLAP_FILE) -> dict[str, int]:
    """Read the OLTP database and write a fresh DuckDB file at `path`."""
    oltp = {table: read_table(pg, table) for table in STAGED}
    if not oltp["transactions"].height:
        log.warning("No transactions yet: run simulate first for the facts")
    metadata = read_table(pg, "run_metadata")
    path.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as duck:
        counts = build_olap(duck, oltp)
        # How the data was made, for the export's dataset_metadata.json
        duck.register("stg_run_metadata", metadata)
        duck.execute("CREATE TABLE run_metadata AS SELECT * FROM stg_run_metadata")
    log.info("OLAP written to %s", path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return counts
