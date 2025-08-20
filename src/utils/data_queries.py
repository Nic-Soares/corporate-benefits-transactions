def get_municipio_ids(conn):
    """Busca IDs válidos de municípios no banco"""
    result = conn.execute("SELECT municipio_id FROM dim_municipios").fetchall()
    return [row[0] for row in result]


def get_cnae_ids(conn):
    """Busca IDs válidos de CNAEs no banco"""
    result = conn.execute("SELECT cnae_id FROM dim_cnae").fetchall()
    return [row[0] for row in result]


def get_segmento_ids(conn):
    """Busca IDs válidos de segmentos no banco"""
    result = conn.execute("SELECT segmento_id FROM dim_segmentos").fetchall()
    return [row[0] for row in result]


def get_produto_ids(conn):
    """Busca IDs válidos de produtos no banco"""
    result = conn.execute("SELECT produto_id FROM dim_produtos").fetchall()
    return [row[0] for row in result]


def get_bandeira_ids(conn):
    """Busca IDs válidos de bandeiras no banco"""
    result = conn.execute("SELECT bandeira_id FROM dim_bandeiras").fetchall()
    return [row[0] for row in result]


def get_company_ids(conn):
    """Busca IDs válidos de empresas no banco"""
    result = conn.execute("SELECT company_id FROM companies").fetchall()
    return [row[0] for row in result]


def get_establishment_ids(conn):
    """Busca IDs válidos de estabelecimentos no banco"""
    result = conn.execute("SELECT establishment_id FROM establishments").fetchall()
    return [row[0] for row in result]


def check_table_has_data(conn, nome_tabela):
    """Verifica se uma tabela possui dados"""
    result = conn.execute(f"SELECT COUNT(*) FROM {nome_tabela}").fetchone()
    return result and result[0] > 0


def count_records(conn, nome_tabela):
    """Conta número de registros em uma tabela"""
    result = conn.execute(f"SELECT COUNT(*) FROM {nome_tabela}").fetchone()
    return result[0] if result else 0