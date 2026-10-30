from src.infrastructure.database.duckdb_manager import connect_database, execute_sql_file
from src.infrastructure.database.postgres_manager import connect_pg_db, execute_pg_sql_file
from src.utils.read_yamls import CONFIG_DIR, load_database

# Paths in config/database.yaml are relative to the repository root
ROOT = CONFIG_DIR.parent


def create_schema_postgres():
    conn = connect_pg_db()
    if conn:
        config = load_database()["oltp_postgres"]
        execute_pg_sql_file(conn, ROOT / config["schema"])
        conn.close()


def create_schema_duckdb():
    config = load_database()["olap_duck"]
    conn = connect_database(
        {"olap_duck": config | {"file_path": str(ROOT / config["file_path"])}}, "olap_duck"
    )

    for file_path in config["schema"].values():
        execute_sql_file(conn, ROOT / file_path)

    conn.close()


if __name__ == "__main__":
    print("Creating database schemas...")

    print("📊 PostgreSQL schema (OLTP)...")
    create_schema_postgres()

    print("🦆 DuckDB schema (OLAP)...")
    create_schema_duckdb()

    print("🎯 Schemas created.")
