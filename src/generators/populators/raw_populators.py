import os
import pandas as pd
import yaml
import random
from faker import Faker
fake = Faker('pt_BR')

def load_config(file_path: str):
    """Carrega arquivo YAML"""
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# ========================================
# GERADORES DE DADOS RAW (BASE FONTE)
# Simulam a realidade antes de qualquer processamento
# ========================================

def generate_products(config_files_updated):
    """Generates products DataFrame based on business rules"""
    produtos = []
    for codigo, dados in config_files_updated['tipos_produto'].items():
        produto = {
            'product_id': f"PROD_{dados['code'].upper()}",
            'code': dados['code'],
            'name': dados['name'],
            'category': dados['category'],
            'description': f"Produto de {dados['name']}",
            'active': True,
            'created_at': pd.Timestamp.now()
        }
        produtos.append(produto)

    produtos_df = pd.DataFrame(produtos)
    produtos_df['code'] = produtos_df['code'].astype('category')
    produtos_df['name'] = produtos_df['name'].astype('category')
    produtos_df['category'] = produtos_df['category'].astype('category')

    return produtos_df

def generate_segments(config_files_updated):
    """Generate segments DataFrame from business rules"""
    segments_list = config_files_updated['segments']
    segments = pd.DataFrame(segments_list)
    segments['created_at'] = pd.Timestamp.now()
    segments['name'] = segments['name'].astype('category')
    segments['category'] = segments['category'].astype('category')
    return segments

def generate_acquirers(config_files_updated):
    """Generates DataFrame for Acquirers based on business rules"""
    adquirentes = []
    for idx, name in enumerate(config_files_updated['adquirentes'], start=1):
        acquirer = {
            "acquirer_id": f"ACQ_{idx:03d}",
            "name": name,
            "active": True,
            "created_at": pd.Timestamp.now()
        }
        adquirentes.append(acquirer)
    return pd.DataFrame(adquirentes)

def generate_transaction_modalities(config_files_updated):
    """Generates DataFrame for Transaction Modalities based on business rules"""
    modalidades = []
    modalidades_yaml = config_files_updated['modalidades']

    # Se for dict, usa .values(); se for lista, itera direto
    iterator = modalidades_yaml.values() if isinstance(modalidades_yaml, dict) else modalidades_yaml

    for idx, dados in enumerate(iterator, start=1):
        modality = {
            "modality_id": f"MOD_{idx:03d}",
            "code": dados["name"].upper().replace(" ", "_"),
            "name": dados["name"],
            "type": "brand" if dados["name"].upper() in ["ELO", "MASTERCARD", "VISA"] else "proprietary_network",
            "active": True,
            "created_at": pd.Timestamp.now()
        }
        modalidades.append(modality)
    return pd.DataFrame(modalidades)

def generate_companies(n_companies, segments_df):
    """Generate RAW companies data - simulates real world data"""
    companies = []

    for i in range(n_companies):
        # Alguns companies podem ter parent companies
        parent_id = None
        if companies and random.random() < 0.1:  # 10% chance de ter parent
            parent_id = random.choice([c['company_id'] for c in companies])

        company = {
            'company_id': f"EMP_{i:06d}",
            'parent_company_id': parent_id,
            'name': fake.company(),
            'cnpj': fake.cnpj(),  # CNPJ REAL
            'company_type': random.choice(["Privada", "Publica"]),
            'segment_id': random.choice(segments_df['segment_id'].tolist()),
            'municipality_id': f"MUN_{random.randint(1, 5570):06d}",  # Referencia municipios brasileiros
            'contract_registration_date': fake.date_between(start_date='-10y', end_date='today'),
            'created_at': pd.Timestamp.now()
        }
        companies.append(company)

    return pd.DataFrame(companies)

def generate_cardholders(n_funcionarios, companies_df, municipalities_df):
    """Generate RAW cardholders data - simulates real world data"""
    cardholders = []

    for i in range(n_funcionarios):
        cardholder = {
            'cardholder_id': f"FUNC_{i:08d}",
            'company_id': random.choice(companies_df['company_id'].tolist()),
            'full_name': fake.name(),
            'cpf': fake.cpf(),  # CPF REAL - será processado depois
            'municipality_id': random.choice(municipalities_df['municipality_id'].tolist()) if 'municipality_id' in municipalities_df.columns else f"MUN_{random.randint(1, 5570):06d}",
            'admission_date': fake.date_this_decade(),
            'position': fake.job(),
            'department': random.choice(['TI', 'RH', 'Financeiro', 'Vendas', 'Marketing', 'Operações']),
            'status': random.choice(['active', 'inactive', 'terminated']),
            'created_at': pd.Timestamp.now()
        }
        cardholders.append(cardholder)

    return pd.DataFrame(cardholders)

def generate_cards(n_cards, cardholders_df, modality_df):
    """Generate RAW cards data - simulates real world data"""
    cards = []

    for idx in range(n_cards):
        # Número do cartão REAL (16 dígitos)
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        formatted_card_number = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])

        # CVV REAL (3 dígitos)
        cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])

        card = {
            "card_id": f"CARD_{idx:08d}",
            "cardholder_id": random.choice(cardholders_df['cardholder_id'].tolist()),
            "card_number": formatted_card_number,  # NÚMERO REAL
            "modality_id": random.choice([None] + modality_df['modality_id'].tolist()),  # NULL = rede proprietária
            "expiration_date": fake.date_between(start_date='today', end_date='+5y'),
            "cvv": cvv,  # CVV REAL
            "card_type": random.choice(['physical', 'virtual']),
            "issuance_date": fake.date_between(start_date='-2y', end_date='today'),
            "status": random.choice(['active', 'blocked', 'cancelled']),
            "created_at": pd.Timestamp.now()
        }
        cards.append(card)

    return pd.DataFrame(cards)

def generate_card_products(cards_df, products_df, min_products=1, max_products=3):
    """Generate RAW card products - ensuring no duplicate products per card"""
    card_products = []
    available_products = products_df['product_id'].tolist()

    for card_id in cards_df['card_id'].tolist():
        # Determinar quantos produtos este cartão terá
        n_products = random.randint(min_products, min(max_products, len(available_products)))

        # Selecionar produtos únicos para este cartão
        selected_products = random.sample(available_products, n_products)

        for product_id in selected_products:
            activation_date = fake.date_between(start_date='-2y', end_date='today')

            # 30% de chance de já ter sido desativado
            deactivation_date = None
            if random.random() < 0.3:
                deactivation_date = fake.date_between(start_date=activation_date, end_date='today')
                status = random.choice(['suspended', 'cancelled'])
            else:
                status = 'active'

            card_product = {
                "card_product_id": f"CP_{fake.uuid4()}",
                "card_id": card_id,
                "product_id": product_id,
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

def generate_establishments(n_establishments, df_cnae, df_mcc, municipalities_df):
    """Generate RAW establishments data - simulates real world data"""
    establishments = []

    # Tipos de natureza jurídica mais comuns
    legal_natures = ["LTDA", "EIRELI", "SA", "MEI", "EPP", "COOPERATIVA"]
    company_sizes = ["MEI", "ME", "EPP", "PEQUENO PORTE", "MEDIO PORTE", "GRANDE PORTE"]
    statuses = ["ATIVA", "INATIVA", "SUSPENSA", "BAIXADA"]
    status_reasons = ["NORMAL", "IRREGULARIDADE", "FALTA DE MOVIMENTO", "MUDANÇA DE ENDEREÇO"]

    for i in range(n_establishments):
        establishment = {
            'establishment_id': f"EST_{i:08d}",
            'cnpj': fake.cnpj(),  # CNPJ REAL
            'legal_name': fake.company(),
            'trade_name': fake.company_suffix() + " " + fake.last_name(),
            'main_cnae_id': random.choice(df_cnae['subclasse_id'].astype(str).tolist()),
            'mcc_code': random.choice(df_mcc['mcc_code'].tolist()),
            'legal_nature': random.choice(legal_natures),
            'company_size': random.choice(company_sizes),
            'municipality_id': random.choice(municipalities_df['municipality_id'].tolist()) if 'municipality_id' in municipalities_df.columns else f"MUN_{random.randint(1, 5570):06d}",
            'postal_code': fake.postcode(),
            'street': fake.street_name(),
            'number': str(fake.building_number()),
            'complement': random.choice([None, f"Sala {random.randint(1, 100)}", f"Loja {random.randint(1, 50)}"]),
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

def generate_terminals(n_terminals, establishments_df, acquirers_df):
    """Generate terminals for establishments"""
    terminals = []

    terminal_models = ["POS Cielo LIO", "TEF Rede", "Stone Ton", "GetNet POS", "Moderninha Pro"]
    terminal_types = ["POS", "PDV", "TEF"]

    for i in range(n_terminals):
        terminal = {
            'terminal_id': f"TERM_{i:08d}",
            'terminal_code': f"T{random.randint(100000, 999999)}",
            'establishment_id': random.choice(establishments_df['establishment_id'].tolist()),
            'acquirer_id': random.choice(acquirers_df['acquirer_id'].tolist()),
            'terminal_model': random.choice(terminal_models),
            'terminal_type': random.choice(terminal_types),
            'status': random.choice(['active', 'inactive', 'maintenance']),
            'installation_date': fake.date_between(start_date='-3y', end_date='today'),
            'created_at': pd.Timestamp.now()
        }
        terminals.append(terminal)

    return pd.DataFrame(terminals)

def generate_capture_technologies():
    """Generate capture technologies"""
    technologies = [
        {"code": "CHIP", "category": "physical", "name": "Chip", "requires_physical_card": True},
        {"code": "MAG_STRIPE", "category": "physical", "name": "Magnetic Stripe", "requires_physical_card": True},
        {"code": "CONTACTLESS", "category": "physical", "name": "Contactless", "requires_physical_card": True},
        {"code": "MOBILE_NFC", "category": "digital", "name": "Mobile NFC", "requires_physical_card": False},
        {"code": "APPLE_PAY", "category": "digital", "name": "Apple Pay", "requires_physical_card": False},
        {"code": "GOOGLE_PAY", "category": "digital", "name": "Google Pay", "requires_physical_card": False}
    ]

    capture_tech_list = []
    for idx, tech in enumerate(technologies, start=1):
        capture_tech = {
            "technology_id": f"TECH_{idx:03d}",
            "technology_code": tech["code"],
            "technology_category": tech["category"],
            "technology_name": tech["name"],
            "requires_physical_card": tech["requires_physical_card"],
            "created_at": pd.Timestamp.now()
        }
        capture_tech_list.append(capture_tech)

    return pd.DataFrame(capture_tech_list)

def generate_response_codes():
    """Generate response codes for transaction processing"""
    response_codes = [
        {"code": "00", "description": "Approved", "category": "success", "is_fraud": False},
        {"code": "51", "description": "Insufficient funds", "category": "balance", "is_fraud": False},
        {"code": "14", "description": "Invalid card number", "category": "card", "is_fraud": True},
        {"code": "55", "description": "Incorrect PIN", "category": "password", "is_fraud": False},
        {"code": "96", "description": "System error", "category": "network", "is_fraud": False},
        {"code": "30", "description": "Format error", "category": "network", "is_fraud": False},
        {"code": "12", "description": "Invalid transaction", "category": "establishment", "is_fraud": True},
        {"code": "43", "description": "Stolen card", "category": "card", "is_fraud": True}
    ]

    codes_list = []
    for idx, code_info in enumerate(response_codes, start=1):
        response_code = {
            "response_code_id": f"RESP_{idx:03d}",
            "response_code": code_info["code"],
            "response_description": code_info["description"],
            "response_category": code_info["category"],
            "is_potential_fraud": code_info["is_fraud"],
            "created_at": pd.Timestamp.now()
        }
        codes_list.append(response_code)

    return pd.DataFrame(codes_list)
