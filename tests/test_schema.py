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
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.product_loader import load_products
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
    "card_products",
    "establishments",
    "terminals",
]


def _insert(conn: duckdb.DuckDBPyConnection, table: str, df: pl.DataFrame) -> None:
    columns = ", ".join(df.columns)
    conn.register("rows", df)
    conn.execute(f"INSERT INTO {table} ({columns}) SELECT {columns} FROM rows").fetchall()
    conn.unregister("rows")


def _reference_tables() -> dict[str, pl.DataFrame]:
    data = load_pre_populated_data()
    return {
        "products": load_products(data),
        "transaction_modalities": load_transaction_modalities(data),
        "acquirers": load_acquirers(data),
    }


def test_oltp_takes_reference_and_generated_data(build_tables):
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

    for table, df in _reference_tables().items():
        _insert(conn, f"dim_{table}", df)

    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert "fact_transactions" in tables
    assert len(tables) == 9


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
        assert count == 14
    finally:
        conn.rollback()
        conn.close()
