"""PostgreSQL access for the pipeline (psycopg 3).

The functions don't commit: the caller decides the transaction, so a setup
either lands whole or not at all.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import polars as pl
import psycopg
from dotenv import load_dotenv

from src.config import load_database

load_dotenv()


def connect_pg_db() -> psycopg.Connection:
    """Connect to the OLTP database (host and name from `config/database.yaml`,
    credentials from `.env`)."""
    config = load_database()["oltp"]
    return psycopg.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )


def run_sql_file(conn: psycopg.Connection, path: str | Path) -> None:
    conn.execute(Path(path).read_text())


def count_rows(conn: psycopg.Connection, table: str) -> int:
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def copy_dataframe(conn: psycopg.Connection, table: str, df: pl.DataFrame) -> None:
    """Append the rows with COPY, as CSV written by Polars (fast; fails on a
    duplicate key). An empty field is NULL, a quoted empty one an empty string."""
    columns = ", ".join(df.columns)
    with (
        conn.cursor() as cur,
        cur.copy(f"COPY {table} ({columns}) FROM STDIN (FORMAT csv)") as copy,
    ):
        copy.write(df.write_csv(include_header=False))


def upsert_dataframe(
    conn: psycopg.Connection, table: str, df: pl.DataFrame, key: list[str]
) -> None:
    """Insert the rows, or update them when the key exists: running twice changes nothing."""
    columns = ", ".join(df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    updates = [f"{c} = EXCLUDED.{c}" for c in df.columns if c not in key]
    action = f"DO UPDATE SET {', '.join(updates)}" if updates else "DO NOTHING"
    query = (
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(key)}) {action}"
    )
    with conn.cursor() as cur:
        cur.executemany(query, list(df.iter_rows()))


# Postgres column types as Polars types (numeric as floats)
POLARS_TYPES = {
    "character varying": pl.String,
    "text": pl.String,
    "numeric": pl.Float64,
    "integer": pl.Int32,
    "bigint": pl.Int64,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "timestamp without time zone": pl.Datetime("us"),
    "timestamp with time zone": pl.Datetime("us", "UTC"),
    "smallint": pl.Int16,
    "double precision": pl.Float64,
    "real": pl.Float32,
}


def table_schema(conn: psycopg.Connection, table: str) -> dict[str, pl.DataType]:
    """The table's columns as a Polars schema, from the database (no guessing)."""
    rows = conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = %s AND table_schema = current_schema() ORDER BY ordinal_position",
        (table,),
    ).fetchall()
    return {name: POLARS_TYPES[data_type] for name, data_type in rows}


def read_table(conn: psycopg.Connection, table: str) -> pl.DataFrame:
    """A whole table as a DataFrame; numeric columns as floats."""
    schema = table_schema(conn, table)
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    return pl.DataFrame(rows, schema=schema, orient="row")


def read_chunks(
    conn: psycopg.Connection, table: str, size: int = 200_000
) -> Iterator[pl.DataFrame]:
    """A table in DataFrames of `size` rows, read through a server-side cursor:
    memory holds one chunk, not the table."""
    schema = table_schema(conn, table)
    with conn.cursor(name=f"read_{table}") as cur:
        cur.execute(f"SELECT * FROM {table}")
        while rows := cur.fetchmany(size):
            yield pl.DataFrame(rows, schema=schema, orient="row")


@contextmanager
def bulk_load(conn: psycopg.Connection, tables: list[str]) -> Iterator[None]:
    """Drop the foreign keys and secondary indexes of `tables` and build them
    back at the end: Postgres checks each key in one pass and builds each index
    once, instead of once per row loaded. Inside the caller's transaction, so a
    broken reference fails it whole."""
    keys = conn.execute(
        "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE contype = 'f' AND conrelid = ANY(%s::regclass[])",
        (tables,),
    ).fetchall()
    indexes = conn.execute(
        "SELECT i.indexrelid::regclass::text, pg_get_indexdef(i.indexrelid) FROM pg_index i "
        "WHERE i.indrelid = ANY(%s::regclass[]) AND NOT i.indisprimary AND NOT i.indisunique",
        (tables,),
    ).fetchall()
    for table, name, _ in keys:
        conn.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
    for name, _ in indexes:
        conn.execute(f"DROP INDEX {name}")
    yield
    for _, definition in indexes:
        conn.execute(definition)
    for table, name, definition in keys:
        conn.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} {definition}")
