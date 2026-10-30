import os

import duckdb


def connect_database(db_config, modelo):
    db_path = db_config[modelo]["file_path"]
    conn = duckdb.connect(db_path, read_only=False)
    # conn.execute("INSTALL spatial;")
    # conn.execute("LOAD spatial;")
    return conn


def execute_sql_file(conn, file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"📄 Running: {file_path}")
    with open(file_path) as file:
        sql_content = file.read()
        try:
            conn.execute(sql_content)
        except duckdb.CatalogException as e:
            if "already exists" in str(e):
                print(f"⚠️ Object already exists in DuckDB (skipped): {file_path} - {e}")
            else:
                raise e  # Re-raise if it's another CatalogException
    print(f"✅ Done: {file_path}")


def insert_dataframe(conn, df, table_name):
    """Insert DataFrame into DuckDB"""
    conn.register("temp_df", df)
    conn.execute(f"INSERT INTO {table_name} SELECT * FROM temp_df")
    conn.unregister("temp_df")
