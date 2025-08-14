import duckdb
import yaml
import os

def carregar_config():
  with open("config/database.yaml", "r") as arquivo:
    db_config = yaml.safe_load(arquivo)
  return db_config

def conectar_banco(db_config):
  db_path = db_config["database"]["file_path"]
  conn = duckdb.connect(db_path, read_only=False)
  conn.execute("INSTALL spatial;")
  conn.execute("LOAD spatial;")
  return conn

def executar_sql_file(conn, file_path):
  if not os.path.exists(file_path):
    print(f"❌ Arquivo não encontrado: {file_path}")
    return

  print(f"📄 Executando: {file_path}")
  with open(file_path, "r") as file:
    sql_content = file.read()
    conn.execute(sql_content)
  print(f"✅ Concluído: {file_path}")
