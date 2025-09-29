# %% Cell 1
import os
import pandas as pd
import polars as pl
import yaml
import random
from datetime import datetime

from mimesis import Person, Address, Finance, Datetime
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale
from mimesis import Numeric
import faker

fake = faker.Faker('pt_BR')

# Locale em português
person = Person(Locale.PT_BR)
address = Address(Locale.PT_BR)
finance = Finance(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()

print(person.full_name())
print(person.email())
print(address.city())
print(finance.company())  
def load_config(file_path: str):
    """Carrega arquivo YAML"""
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# %% Cell 2
# Configura o diretório de trabalho para a raiz do projeto
import os
import sys

# Define o caminho da raiz do projeto diretamente
project_root = '/home/nicolas/Projects/Personal/corporate-benefits-transactions'
os.chdir(project_root)
print(f"Diretório de trabalho atual: {os.getcwd()}")

# Adiciona o diretório raiz ao path do Python para imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Carrega configurações usando os novos arquivos reorganizados
business_data = load_config('./config/business_rules.yaml')       # Dados estáticos para DataFrames
parameters = load_config('./config/transaction_simulation.yaml')  # Parâmetros de configuração
validation_rules = load_config('./config/validation_rules.yaml')

cnae_products_mapping = business_data.get('cnae_products_mapping', {})

print("Configurações carregadas com sucesso!")
print(f"Dados de negócio carregados: {list(business_data.keys())}")
print(f"Parâmetros de simulação carregados: {list(parameters.keys())}")

# %% Cell 3
# Recarregando o módulo para garantir que temos a versão corrigida
import importlib
import src.extractors.municipality_data_importer
importlib.reload(src.extractors.municipality_data_importer)
from src.extractors.municipality_data_importer import generate_municipality_data

shapefile_path = './data/raw/municipios/municipios.shp'

# %% Cell 4
# Imports dos geradores migrados
from src.data_generators.entities.product_generator import generate_products
from src.data_generators.entities.company_generator import generate_companies
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.cardholder_generator import generate_cardholders
from src.data_generators.entities.card_generator import generate_cards
from src.data_generators.entities.terminal_generator import generate_terminals
from src.data_generators.entities.card_product_generator import generate_card_products
from src.data_generators.entities.transaction_generator import generate_single_transaction, gerar_valor_transacao, _sample_scalar
from src.data_generators.reference_data.segment_generator import generate_segments
from src.data_generators.reference_data.acquirer_generator import generate_acquirers
from src.data_generators.reference_data.modality_generator import generate_transaction_modalities
from src.data_generators.reference_data.response_code_generator import generate_response_codes, generate_capture_technologies
from src.data_generators.reference_data.data_extractors import extract_cnae_data, extract_mcc_data


# %% Cell 18
municipalities_df = generate_municipality_data(shapefile_path)
products_df = generate_products(business_data)
cnaes_df = extract_cnae_data()
segments_df = generate_segments(business_data)
acquirers_df = generate_acquirers(business_data)
transaction_modalities_df = generate_transaction_modalities(business_data)
mcc_df = extract_mcc_data()
capture_tech_df = generate_capture_technologies(business_data)
establishments_df = generate_establishments(
    parameters['data_volumes']['establishments'], 
    cnaes_df, 
    mcc_df, 
    municipalities_df,
    cnae_products_mapping,
    parameters['generation_settings'].get('cnae_with_products_ratio', 0.85)
)
terminals_df = generate_terminals(parameters['data_volumes']['terminals'], establishments_df, acquirers_df, business_data)
companies_df = generate_companies(parameters['data_volumes']['companies'], municipalities_df, segments_df)
cardholders_df = generate_cardholders(parameters['data_volumes']['cardholders'], companies_df, municipalities_df)
cards_df = generate_cards(parameters['data_volumes']['cards'], cardholders_df, transaction_modalities_df)
card_products_df = generate_card_products(cards_df, products_df, min_products=1, max_products=3)

# %% Cell 19
# Funções gerar_valor_transacao, _sample_scalar e generate_single_transaction foram movidas para src.data_generators.entities.transaction_generator

# %% Cell 20

# Exemplo de uso: gerar uma única transação
single_transaction = generate_single_transaction(cards_df, establishments_df, terminals_df, card_products_df)
print("Transação gerada:")
print(single_transaction)

# %% Cell 21
