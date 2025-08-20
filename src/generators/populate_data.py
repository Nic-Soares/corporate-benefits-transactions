from src.common.config_loaders import carregar_business_rules, carregar_config_volumes

def populate_data():
    """Função principal que orquestra a população do banco de dados"""
    # Carrega configurações
    business_rules = carregar_business_rules()
    volumes = carregar_config_volumes()['volumes']

    # Conecta ao banco
    db_config = load_config()
    conn = connect_database_from_config(db_config)

    # Import external data
    _import_municipalities(conn)

    # Populate dimension tables
    _populate_dimensions(conn, business_rules, volumes)

    # Populate entity tables
    _populate_entities(conn, volumes)

    print("🎯 População de dados concluída com sucesso!")
    conn.close()


def _import_municipalities(conn):
    """Import municipality data from shapefile"""
    if not check_table_has_data(conn, "dim_municipios"):
        print("📍 Importing municipality data...")
        df = generate_municipality_data()
        duckdb_manager.insert_dataframe(conn, df, "dim_municipios")
        print(f"✅ {len(df)} municipalities imported")
    else:
        print("dim_municipios já possui dados. Nenhuma importação realizada.")


def _populate_dimensions(conn, business_rules, volumes):
    """Populate all dimension tables"""
    _populate_if_empty(conn, "dim_produtos", generate_dim_products_data, business_rules)
    _populate_if_empty(conn, "dim_bandeiras", generate_dim_flags_data, business_rules)
    _populate_if_empty(conn, "dim_segmentos", generate_dim_segments_data, volumes)
    _populate_if_empty(conn, "dim_cnae", generate_dim_cnae_data, volumes)


def _populate_entities(conn, volumes):
    """Populate all main entity tables"""
    # Get required IDs from database
    municipio_ids = get_municipio_ids(conn)
    cnae_ids = get_cnae_ids(conn)

    # Populate companies
    if count_records(conn, "companies") == 0:
        df = generate_companies_data(volumes, municipio_ids)
        duckdb_manager.insert_dataframe(conn, df, "companies")
        print(f"✅ {len(df)} companies inserted")
    else:
        print("companies já possui dados. Nenhuma inserção realizada.")

    # Populate establishments
    if count_records(conn, "establishments") == 0:
        df = generate_establishments_data(volumes, municipio_ids, cnae_ids)
        duckdb_manager.insert_dataframe(conn, df, "establishments")
        print(f"✅ {len(df)} establishments inserted")
    else:
        print("establishments já possui dados. Nenhuma inserção realizada.")


def _populate_if_empty(conn, table_name, generate_func, *args, **kwargs):
    """Helper function to populate table only if empty"""
    if count_records(conn, table_name) == 0:
        df = generate_func(*args, **kwargs)
        duckdb_manager.insert_dataframe(conn, df, table_name)
        print(f"✅ {len(df)} records inserted into {table_name}")
    else:
        print(f"{table_name} já possui dados. Nenhuma inserção realizada.")


if __name__ == "__main__":
    populate_data()
