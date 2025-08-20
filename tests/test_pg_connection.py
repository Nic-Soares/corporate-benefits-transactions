from src.common.postgres_manager import connect_pg_db

def test_pg_connection():
    """
    Testa a função connect_pg_db e imprime o status da conexão.
    """
    print("Iniciando teste de conexão ao PostgreSQL...")
    conn = None
    try:
        conn = connect_pg_db()
        if conn:
            print("✔️ Teste de conexão: Conexão bem-sucedida ao PostgreSQL!")
            # Opcional: Executar uma query simples para verificar se a conexão está ativa
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                print("✔️ Teste de query: Query simples executada com sucesso.")
            except Exception as e:
                print(f"❌ Teste de query: Falha ao executar query simples: {e}")
        else:
            print("❌ Teste de conexão: Falha ao conectar ao PostgreSQL.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado durante o teste: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão ao PostgreSQL fechada.")

if __name__ == "__main__":
    test_pg_connection()
