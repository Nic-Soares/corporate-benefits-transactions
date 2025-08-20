# -*- coding: utf-8 -*-

from src.common.postgres_manager import connect_pg_db, execute_pg_sql_file
from src.common.duckdb_manager import connect_database, execute_sql_file
from src.utils.load_db_config import load_db_config


def create_schema_postgres():
    conn = connect_pg_db()
    if conn:
        config = load_db_config("oltp_postgres")
        sql_file_path = config["schema"]["tables"]
        if sql_file_path:
            execute_pg_sql_file(conn, sql_file_path)
        conn.close()

def create_schema_duckdb():
    config = load_db_config("olap_duck")
    conn = connect_database({"olap_duck": config}, "olap_duck")

    schema_files = config.get("schema", {})
    for schema_type, file_path in schema_files.items():
        if file_path:
            execute_sql_file(conn, file_path)

    conn.close()


if __name__ == "__main__":
  print("Criando schemas dos bancos...")

  print("📊 Criando schema PostgreSQL (OLTP)...")
  create_schema_postgres()

  print("🦆 Criando schema DuckDB (OLAP)...")
  create_schema_duckdb()

  print("🎯 Schemas criados com sucesso!")
