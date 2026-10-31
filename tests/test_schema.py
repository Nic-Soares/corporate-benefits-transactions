"""The SQL schemas accept the config's reference data and the generators' output.

DuckDB runs the OLTP schema too, so the foreign keys are checked without Docker;
the `db` test applies it to the real Postgres.
"""

from datetime import date
from pathlib import Path

import duckdb
import polars as pl
import pytest

from src.data_generators.providers import fake
from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.card_program_loader import (
    load_card_program_wallets,
    load_card_programs,
    load_cnae_wallets,
    load_mcc_wallets,
)
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.response_codes_loader import load_response_codes
from src.data_generators.reference_data.wallet_loader import load_wallets
from src.utils.read_yamls import load_pre_populated_data

DATABASE = Path(__file__).parent.parent / "database"
OLTP_SCHEMA = DATABASE / "oltp_postgres" / "oltp_schema.sql"
OLAP_SCHEMA = [
    DATABASE / "olap_duck" / "01_dimensions.sql",
    DATABASE / "olap_duck" / "02_facts.sql",
]

# Parents before children, so the foreign keys resolve
GENERATED_TABLES = [
    "companies",
    "cardholders",
    "cards",
    "card_wallets",
    "establishments",
    "terminals",
]


def _insert(conn: duckdb.DuckDBPyConnection, table: str, df: pl.DataFrame) -> None:
    columns = ", ".join(df.columns)
    conn.register("rows", df)
    conn.execute(f"INSERT INTO {table} ({columns}) SELECT {columns} FROM rows").fetchall()
    conn.unregister("rows")


def _reference_tables() -> dict[str, pl.DataFrame]:
    """Reference tables in load order (parents first)."""
    data = load_pre_populated_data()
    return {
        "wallets": load_wallets(data),
        "transaction_modalities": load_transaction_modalities(data),
        "acquirers": load_acquirers(data),
        "response_codes": load_response_codes(data),
        "card_programs": load_card_programs(data),
        "card_program_wallets": load_card_program_wallets(data),
        "cnae_wallets": load_cnae_wallets(data),
        "mcc_wallets": load_mcc_wallets(data),
    }


OLAP_DIMENSIONS = {
    "wallets": "dim_wallets",
    "card_programs": "dim_card_programs",
    "transaction_modalities": "dim_transaction_modalities",
    "acquirers": "dim_acquirers",
}


def test_oltp_takes_reference_and_generated_data(build_tables, transaction_generator):
    conn = duckdb.connect()
    conn.execute(OLTP_SCHEMA.read_text())

    for table, df in _reference_tables().items():
        _insert(conn, table, df)

    fake.seed(1, today=date(2026, 10, 30))
    generated = build_tables()
    for table in GENERATED_TABLES:
        if table == "companies":
            # Self-reference: holdings must exist before their branches
            companies = generated[table]
            _insert(conn, table, companies.filter(pl.col("parent_id").is_null()))
            _insert(conn, table, companies.filter(pl.col("parent_id").is_not_null()))
        else:
            _insert(conn, table, generated[table])
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0]
        assert count == len(generated[table]), table

    # Transactions reference the card wallet charged and an ISO response code
    generator = transaction_generator(generated)
    transactions = pl.DataFrame([generator.generate() | {"response_code": "00"} for _ in range(20)])
    _insert(conn, "transactions", transactions)
    assert conn.execute("SELECT count(*) FROM transactions").fetchall()[0][0] == 20


def test_oltp_rejects_a_dangling_reference(build_tables):
    """The foreign keys are really enforced: a card for an unknown cardholder fails."""
    conn = duckdb.connect()
    conn.execute(OLTP_SCHEMA.read_text())
    for table, df in _reference_tables().items():
        _insert(conn, table, df)

    cards = build_tables()["cards"].head(1)
    with pytest.raises(duckdb.ConstraintException):
        _insert(conn, "cards", cards)


def test_olap_schema_and_reference_dimensions():
    conn = duckdb.connect()
    for path in OLAP_SCHEMA:
        conn.execute(path.read_text())

    reference = _reference_tables()
    for table, dimension in OLAP_DIMENSIONS.items():
        _insert(conn, dimension, reference[table])

    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert "fact_transactions" in tables
    assert len(tables) == 10


@pytest.mark.db
def test_oltp_schema_on_postgres():
    """Needs `docker compose up -d` and a filled-in .env. Rolls back."""
    from src.infrastructure.database.postgres_manager import connect_pg_db

    conn = connect_pg_db()
    assert conn
    try:
        conn.execute("CREATE SCHEMA schema_check")
        conn.execute("SET search_path TO schema_check")
        conn.execute(OLTP_SCHEMA.read_text())
        count = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'schema_check'"
        ).fetchone()[0]
        assert count == 17
    finally:
        conn.rollback()
        conn.close()
