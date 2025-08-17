from src.common import database


def create_oltp():
  pass

def create_olap():
  pass

if __name__ == "__main__":
  print("Criando schema do banco")

  # Carregar configuração
  config = database.carregar_config()

  # Conectar no banco
  conn = database.conectar_banco(config)

  print("Banco conectado!")

  print(" Executando SQLs...")
  database.executar_sql_file(conn, "database/schema/01_dimensions.sql")
  database.executar_sql_file(conn, "database/schema/02_entities.sql")
  database.executar_sql_file(conn, "database/schema/03_facts.sql")
  # database.executar_sql_file(conn, "database/schema/04_views.sql")

  print("🎯 Schema criado com sucesso!")
  conn.close()
