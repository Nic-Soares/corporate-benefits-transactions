"""PostgreSQL access for the pipeline (psycopg 3).

The functions don't commit: the caller decides the transaction, so a setup
either lands whole or not at all.
"""

import os
from pathlib import Path

import polars as pl
import psycopg
from dotenv import load_dotenv

from src.utils.read_yamls import load_database

load_dotenv()


def connect_pg_db() -> psycopg.Connection:
    """Connect to the OLTP database (host and name from `config/database.yaml`,
    credentials from `.env`)."""
    config = load_database()["oltp_postgres"]
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
    """Append the rows with COPY (fast; fails on a duplicate key)."""
    columns = ", ".join(df.columns)
    with conn.cursor() as cur, cur.copy(f"COPY {table} ({columns}) FROM STDIN") as copy:
        for row in df.iter_rows():
            copy.write_row(row)


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
