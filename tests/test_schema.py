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
from src.pipeline.reference import build_reference_tables

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


@pytest.fixture
def reference_tables(sources) -> dict[str, pl.DataFrame]:
    """Reference tables in load order (parents first), as the setup builds them."""
    return build_reference_tables(sources.cnae, sources.mcc)


OLAP_DIMENSIONS = {
    "wallets": "dim_wallets",
    "card_programs": "dim_card_programs",
    "transaction_modalities": "dim_transaction_modalities",
    "acquirers": "dim_acquirers",
}


def test_oltp_takes_reference_and_generated_data(
    reference_tables, build_tables, transaction_generator
):
    conn = duckdb.connect()
    conn.execute(OLTP_SCHEMA.read_text())

    for table, df in reference_tables.items():
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


def test_oltp_rejects_a_dangling_reference(reference_tables, build_tables):
    """The foreign keys are really enforced: a card for an unknown cardholder fails."""
    conn = duckdb.connect()
    conn.execute(OLTP_SCHEMA.read_text())
    for table, df in reference_tables.items():
        _insert(conn, table, df)

    cards = build_tables()["cards"].head(1)
    with pytest.raises(duckdb.ConstraintException):
        _insert(conn, "cards", cards)


def test_olap_schema_and_reference_dimensions(reference_tables):
    conn = duckdb.connect()
    for path in OLAP_SCHEMA:
        conn.execute(path.read_text())

    reference = reference_tables
    for table, dimension in OLAP_DIMENSIONS.items():
        _insert(conn, dimension, reference[table])

    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert {"fact_transactions", "fact_balance_movements", "dim_card_wallets"} <= tables
    assert len(tables) == 12


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
