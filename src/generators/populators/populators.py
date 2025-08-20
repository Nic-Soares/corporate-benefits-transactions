import os
import pandas as pd
import yaml
import random
from faker import Faker
fake = Faker('pt_BR')  # Brazilian locale for more realistic data

def load_config(file_path: str):
    """Carrega arquivo YAML"""
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

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

# Carrega configurações usando caminhos relativos (agora que o diretório está correto)
business_rules = load_config('./config/business_rules.yaml')
volumes = load_config('./config/data_volumes.yaml')
print("Configurações carregadas com sucesso!")


# Recarregando o módulo para garantir que temos a versão corrigida
import importlib
import src.extractors.municipality_data_importer
importlib.reload(src.extractors.municipality_data_importer)
from src.extractors.municipality_data_importer import generate_municipality_data

shapefile_path = './data/raw/municipios/municipios.shp'

municipalities = generate_municipality_data(shapefile_path)

def generate_products(business_rules):
    """Generates products DataFrame based on business rules"""
    produtos = []
    for codigo, dados in business_rules['tipos_produto'].items():
      produto = {
          'product_id': str(f"PROD_{dados['code'].upper()}"),
          'code': dados['code'],
          'name': dados['name'],
          'category': dados['category'],
          'description': str(f"Produto de {dados['name']}"),
          'created_at': pd.Timestamp.now()
      }
      produtos.append(produto)
    produtos = pd.DataFrame(produtos)
    produtos['code'] = produtos['code'].astype('category')
    produtos['name'] = produtos['name'].astype('category')
    produtos['category'] = produtos['category'].astype('category')

    return produtos

products = generate_products(business_rules)
products

from src.extractors.kaggle_downloader import download_kaggle_dataset

def extract_cnae_data():
    download_kaggle_dataset("diovanimerlo/cnae-brazil-2024")

    cnaes = pd.read_csv(
        './data/raw/cnae_dataset_2024.csv',
        sep=',',
        encoding='utf-8',
        dtype={
            "secao_id": str,
            "secao": "category",
            "divisao_id": int,
            "divisao": "category",
            "grupo_id": int,
            "grupo": "category",
            "classe_id": int,
            "classe": "category",
            "subclasse_id": int,
            "subclasse": "category"
        }
    )
    return cnaes

cnaes = extract_cnae_data()

def generate_segments(business_rules):
    # Acessa a lista de segmentos dentro do dicionário
    segments_list = business_rules['segments']

    # Cria o DataFrame diretamente da lista carregada
    segments = pd.DataFrame(segments_list)

    # Adiciona a coluna 'created_at' após a criação do DataFrame para eficiência
    segments['created_at'] = pd.Timestamp.now()
    segments['name'] = segments['name'].astype('category')
    segments['category'] = segments['category'].astype('category')

    return segments
segments = generate_segments(business_rules)

def generate_acquirers(business_rules):
    """Generates DataFrame for Acquirers based on business rules"""
    adquirentes = []
    for idx, name in enumerate(business_rules['adquirentes'], start=1):
        acquirer = {
            "acquirer_id": f"ACQ_{idx:03d}",
            "name": name,
            "active": True,
            "created_at": pd.Timestamp.now()
        }
        adquirentes.append(acquirer)

    return pd.DataFrame(adquirentes)

generate_acquirers(business_rules)


def generate_transaction_modalities(business_rules):
    """Generates DataFrame for Transaction Modalities based on business rules"""
    modalidades = []
    modalidades_yaml = business_rules['modalidades']
    # Se for dict, usa .items(); se for lista, itera direto
    if isinstance(modalidades_yaml, dict):
        iterator = modalidades_yaml.values()
    else:
        iterator = modalidades_yaml
    for idx, dados in enumerate(iterator, start=1):
        modality = {
            "modality_id": f"MOD_{idx:03d}",
            "name": dados["name"],
            "commission": dados.get("commission", 0.0),
            'created_at': pd.Timestamp.now()
        }
        modalidades.append(modality)
    return pd.DataFrame(modalidades)

transaction_modalities = generate_transaction_modalities(business_rules)
transaction_modalities

import pandas as pd

def extract_mcc_data():
    mcc = pd.read_csv(
        './data/raw/mcc.csv',
        sep=',',
        encoding='utf-8',
        dtype={
            "mcc_id": str,
            "mcc_code": str,
            "mcc_description": str,
            "valid_payment_brands": str,
            "category": "category"
        }
    )
    return mcc

mcc_data = extract_mcc_data()
mcc_data

def generate_capture_technologies():
    """Generate basic capture technologies"""
    technologies = ["POS", "Mobile", "Online", "QR Code", "NFC", "Manual"]
    return pd.DataFrame([
        {
            "capture_technology_id": f"CPT_{idx:03d}",
            "name": name,
            "active": True,
            "created_at": pd.Timestamp.now()
        }
        for idx, name in enumerate(technologies, start=1)
    ])

capture_technologies = generate_capture_technologies()
capture_technologies

def generate_establishments(n_establishments, df_cnae, df_mcc, df_municipalities):
    """Generate establishments DataFrame based on existing CNAE, MCC and municipalities data"""
    establishments = []

    # Tipos de natureza jurídica mais comuns
    legal_natures = ["LTDA", "EIRELI", "SA", "MEI", "EPP", "COOPERATIVA"]
    company_sizes = ["MEI", "ME", "EPP", "PEQUENO PORTE", "MEDIO PORTE", "GRANDE PORTE"]
    statuses = ["ATIVA", "INATIVA", "SUSPENSA", "BAIXADA"]
    status_reasons = ["NORMAL", "IRREGULARIDADE", "FALTA DE MOVIMENTO", "MUDANÇA DE ENDEREÇO"]

    for i in range(n_establishments):
        establishment = {
            'establishment_id': f"EST_{i:06d}",
            'cnpj': fake.cnpj(),
            'legal_name': fake.company(),
            'trade_name': fake.company_suffix() + " " + fake.last_name(),
            'main_cnae_id': random.choice(df_cnae['subclasse_id'].tolist()),
            'mcc_code': random.choice(df_mcc['mcc_code'].tolist()),
            'legal_nature': random.choice(legal_natures),
            'company_size': random.choice(company_sizes),
            'municipality_id': random.choice(df_municipalities['municipio_id'].tolist()),
            'postal_code': fake.postcode(),
            'street': fake.street_name(),
            'number': str(fake.building_number()),
            'complement': random.choice([None, "Sala " + str(random.randint(1, 100)), "Loja " + str(random.randint(1, 50))]),
            'neighborhood': fake.neighborhood(),
            'email': fake.company_email(),
            'phone': fake.phone_number(),
            'registration_status': random.choice(statuses),
            'status_date': fake.date_between(start_date='-2y', end_date='today'),
            'status_reason': random.choice(status_reasons),
            'opening_date': fake.date_between(start_date='-10y', end_date='-1y'),
            'created_at': pd.Timestamp.now()
        }
        establishments.append(establishment)

    return pd.DataFrame(establishments)

# Gerar dados de establishments usando o volume configurado
establishments_df = generate_establishments(volumes['volumes']['empresas'], cnaes, mcc_data, municipalities)
establishments_df

def generate_companies(n_companies, segments):
    companies = []
    for i in range(n_companies):
        company = {
            'company_id': f"EMP_{i}",
            'parent_company_id': random.choice([None] + [c["company_id"] for c in companies]) if companies else None,
            'name': fake.company(),
            'cnpj': fake.cnpj(),
            'company_type': random.choice(["Privada", "Publica"]),
            'segment_id': random.choice(segments['segment_id'].tolist()),
            'municipality_id': random.choice(municipalities['municipality_id'].tolist()),
            'contract_registration_date': fake.date_between(start_date='-5y', end_date='today'),
            'created_at': pd.Timestamp.now()
        }
        companies.append(company)
    return pd.DataFrame(companies)  # Return as DataFrame for consistency

# Fixed the volumes access - need to access volumes['volumes']['empresas']
companies_df = generate_companies(volumes['volumes']['empresas'], segments)
companies_df

def generate_cardholders(n_funcionarios, companies_df, municipalities_df):
    """Generate cardholders DataFrame based on existing companies data"""
    cardholders = []

    for i in range(n_funcionarios):
        cardholder = {
            'cardholder_id': f"FUNC_{i}",
            'company_id': random.choice(companies_df['company_id'].tolist()),
            'name': fake.name(),
            'cpf': fake.cpf(),
            'municipality_id': random.choice(municipalities_df['municipality_id'].tolist()),
            'admission_date': fake.date_this_decade(),
            'position': fake.job(),
            'department': fake.word(),
            'status': random.choice(['active', 'inactive', 'terminated']),
            'created_at': pd.Timestamp.now()
        }
        cardholders.append(cardholder)

    return pd.DataFrame(cardholders)

cardholders = generate_cardholders(volumes['volumes']['funcionarios'], companies_df, municipalities)
cardholders

def generate_cards(n_cards, cardholders_df, modality_df):
    cards = []

    for idx in range(n_cards):
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        formatted_card_number = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])

        cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])

        card = {
            "card_id": idx,
            "cardholder_id": random.choice(cardholders_df['cardholder_id'].tolist()),
            "card_number": formatted_card_number,
            "modality_id": random.choice(modality_df['modality_id'].tolist()),
            "expiration_date": fake.date_between(start_date='today', end_date='+5y'),
            "cvv": cvv,
            "card_type": random.choice(['credit', 'debit']),
            "issuance_date": pd.Timestamp.now(),
            "status": random.choice(['active', 'inactive']),
            "created_at": pd.Timestamp.now()
        }
        cards.append(card)

    return pd.DataFrame(cards)

cards = generate_cards(volumes['volumes']['cartoes'], cardholders, transaction_modalities)
cards


def generate_card_products(cards_df, products_df, min_products=1, max_products=3):
    """
    Gera produtos associados aos cartões.
    Cada cartão pode ter entre min_products e max_products produtos.
    """
    card_products = []

    for card_id in cards_df['card_id'].tolist():
        n_products = random.randint(min_products, max_products)

        for _ in range(n_products):
            activation_date = fake.date_between(start_date='-2y', end_date='today')

            # 30% de chance de já ter sido desativado
            if random.random() < 0.3:
                deactivation_date = fake.date_between(start_date=activation_date, end_date='today')
                status = random.choice(['suspended', 'cancelled'])
            else:
                deactivation_date = None
                status = 'active'

            card_product = {
                "card_product_id": fake.uuid4(),
                "card_id": card_id,
                "product_id": random.choice(products_df['product_id'].tolist()),
                "current_balance": round(random.uniform(0, 5000), 2),
                "daily_limit": round(random.uniform(100, 2000), 2),
                "monthly_limit": round(random.uniform(1000, 10000), 2),
                "activation_date": activation_date,
                "deactivation_date": deactivation_date,
                "status": status,
                "created_at": pd.Timestamp.now()
            }
            card_products.append(card_product)

    return pd.DataFrame(card_products)

# uso
card_products = generate_card_products(cards, products, min_products=1, max_products=3)
card_products
