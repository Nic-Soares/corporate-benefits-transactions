import os

import psycopg
from dotenv import load_dotenv

from src.utils.read_yamls import load_database

load_dotenv()

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")


def connect_pg_db():
    """Connect to the PostgreSQL database (credentials from .env)."""
    pg_config = load_database()["oltp_postgres"]
    if not pg_config:
        print("❌ PostgreSQL settings not loaded; cannot connect.")
        return None
    try:
        conn = psycopg.connect(
            host=pg_config.get("host"),
            port=pg_config.get("port"),
            dbname=pg_config.get("dbname"),
            user=db_user,
            password=db_password,
        )
        print("✅ Connected to PostgreSQL.")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None


def execute_pg_query(conn, query, params=None):
    """Run a SQL query on PostgreSQL."""
    if not conn:
        print("❌ No PostgreSQL connection.")
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            else:
                conn.commit()
                print("✅ Query executed.")
                return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Query failed on PostgreSQL: {e}")
        return False


def execute_pg_sql_file(conn, file_path):
    """Run a SQL file on PostgreSQL."""
    if not conn:
        print("❌ No PostgreSQL connection.")
        return False
    if not os.path.exists(file_path):
        print(f"❌ SQL file not found: {file_path}")
        return False

    print(f"📄 Running SQL file on PostgreSQL: {file_path}")
    try:
        with open(file_path) as file:
            sql_content = file.read()
            # psycop.connect() automatically commits DDL statements, but DML needs explicit commit
            # execute_pg_query handles commit for DML
            execute_pg_query(conn, sql_content)
        print(f"✅ Done: {file_path}")
        return True
    except Exception as e:
        print(f"❌ SQL file failed on PostgreSQL: {e}")
        return False


def import_csv_to_pg(conn, csv_file_path, table_name, columns=None):
    """
    Import a CSV file into a PostgreSQL table with COPY.

    Args:
        conn: PostgreSQL connection.
        csv_file_path: CSV file to import.
        table_name: Destination table.
        columns: Destination columns, when they differ from the CSV order.
                 Se None, assume a ordem das colunas no CSV.
    """
    if not conn:
        print("❌ No PostgreSQL connection.")
        return False
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False

    print(f"📥 Importing {csv_file_path} into {table_name}...")
    try:
        with conn.cursor() as cur:
            # Construindo o comando COPY
            copy_command = f"COPY {table_name}"
            if columns:
                copy_command += f" ({', '.join(columns)})"
            copy_command += " FROM STDIN WITH (FORMAT CSV, HEADER TRUE);"

            with open(csv_file_path) as f:
                cur.copy_expert(copy_command, f)
            conn.commit()
            print(f"✅ Imported {csv_file_path} into {table_name}.")
            return True
    except Exception as e:
        conn.rollback()  # Rollback in case of error during copy
        print(f"❌ CSV import into PostgreSQL failed: {e}")
        return False


def insert_dataframe(conn, df, table_name):
    """Insert DataFrame into PostgreSQL using pandas to_sql or COPY"""
    try:
        # Convert DataFrame to CSV string and use COPY
        csv_buffer = df.to_csv(index=False, header=False)
        with conn.cursor() as cur:
            cur.copy_expert(f"COPY {table_name} FROM STDIN WITH (FORMAT CSV)", csv_buffer)
        conn.commit()
        print(f"✅ {len(df)} rows inserted into PostgreSQL table {table_name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting DataFrame into PostgreSQL: {e}")
        return False
