import psycopg
import os
from dotenv import load_dotenv
load_dotenv()
from src.utils.load_db_config import load_db_config

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

def connect_pg_db():
    """Conecta ao banco de dados PostgreSQL."""
    pg_config = load_db_config("oltp_postgres")
    if not pg_config:
        print("❌ Configurações do PostgreSQL não carregadas. Não é possível conectar.")
        return None
    try:
        conn = psycopg.connect(
            host=pg_config.get("host"),
            port=pg_config.get("port"),
            dbname=pg_config.get("dbname"),
            user=db_user,
            password=db_password
        )
        print("✅ Conectado ao PostgreSQL com sucesso!")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return None

def execute_pg_query(conn, query, params=None):
    """Executa uma query SQL no PostgreSQL."""
    if not conn:
        print("❌ Conexão PostgreSQL não estabelecida.")
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            else:
                conn.commit()
                print("✅ Query executada com sucesso.")
                return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao executar query no PostgreSQL: {e}")
        return False

def execute_pg_sql_file(conn, file_path):
    """Executa um arquivo SQL no PostgreSQL."""
    if not conn:
        print("❌ Conexão PostgreSQL não estabelecida.")
        return False
    if not os.path.exists(file_path):
        print(f"❌ Arquivo SQL não encontrado: {file_path}")
        return False

    print(f"📄 Executando arquivo SQL PostgreSQL: {file_path}")
    try:
        with open(file_path, "r") as file:
            sql_content = file.read()
            # psycop.connect() automatically commits DDL statements, but DML needs explicit commit
            # execute_pg_query handles commit for DML
            execute_pg_query(conn, sql_content)
        print(f"✅ Concluído: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar arquivo SQL PostgreSQL: {e}")
        return False

def import_csv_to_pg(conn, csv_file_path, table_name, columns=None):
    """
    Importa dados de um arquivo CSV para uma tabela no PostgreSQL usando COPY.

    Args:
        conn: Objeto de conexão com o PostgreSQL.
        csv_file_path: Caminho para o arquivo CSV a ser importado.
        table_name: Nome da tabela no PostgreSQL para onde os dados serão importados.
        columns: Lista de nomes de colunas no PostgreSQL, se diferente da ordem no CSV.
                 Se None, assume a ordem das colunas no CSV.
    """
    if not conn:
        print("❌ Conexão PostgreSQL não estabelecida.")
        return False
    if not os.path.exists(csv_file_path):
        print(f"❌ Arquivo CSV não encontrado: {csv_file_path}")
        return False

    print(f"📥 Importando {csv_file_path} para a tabela {table_name} no PostgreSQL...")
    try:
        with conn.cursor() as cur:
            # Construindo o comando COPY
            copy_command = f"COPY {table_name}"
            if columns:
                copy_command += f" ({', '.join(columns)})"
            copy_command += f" FROM STDIN WITH (FORMAT CSV, HEADER TRUE);"

            with open(csv_file_path, 'r') as f:
                cur.copy_expert(copy_command, f)
            conn.commit()
            print(f"✅ Dados de {csv_file_path} importados com sucesso para {table_name}.")
            return True
    except Exception as e:
        conn.rollback() # Rollback in case of error during copy
        print(f"❌ Erro ao importar CSV para PostgreSQL: {e}")
        return False


def insert_dataframe(conn, df, table_name):
    """Insert DataFrame into PostgreSQL using pandas to_sql or COPY"""
    try:
        # Convert DataFrame to CSV string and use COPY
        csv_buffer = df.to_csv(index=False, header=False)
        with conn.cursor() as cur:
            cur.copy_expert(
                f"COPY {table_name} FROM STDIN WITH (FORMAT CSV)",
                csv_buffer
            )
        conn.commit()
        print(f"✅ {len(df)} rows inserted into PostgreSQL table {table_name}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting DataFrame into PostgreSQL: {e}")
        return False
