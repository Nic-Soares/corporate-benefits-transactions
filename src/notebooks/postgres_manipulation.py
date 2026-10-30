# %% import
import os
import sys

# Muda para o diretório raiz do projeto
project_root = "/home/nicolas/Projects/Personal/corporate-benefits-transactions"
os.chdir(project_root)
sys.path.insert(0, project_root)

# Agora as importações funcionam normalmente
from src.infrastructure.database.postgres_manager import connect_pg_db, execute_pg_sql_file
from src.utils.read_yamls import load_database

database = load_database()
schema_path = database["oltp_postgres"]["schema"]

# %% Conectar com o banco de dados Postgres
pg_conn = connect_pg_db()

# %% Criar tabelas
execute_pg_sql_file(pg_conn, schema_path)


# %% Alimentar tabelas Pré Populadas
def populate_products():
    pass


def populate_modalities():
    pass


def populate_acquirers():
    pass


def populate_mcc_modalities():
    pass


def populate_cnae_products():
    pass


# %% Transação e criação ON DEMAND
def generate_transaction():
    company = get_or_create_company()
    cardholder = get_or_create_cardholder(company)
    card = get_or_create_card(cardholder)
    card_product = get_or_create_card_product(card)
    establishment = get_or_create_establishment()
    terminal = get_or_create_terminal(establishment)

    # Transação real
    transaction = create_transaction(...)
    authorization = create_authorization(transaction)
    balance_history = update_balance_history(card_product, transaction)
