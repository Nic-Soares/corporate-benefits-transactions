import polars as pl
import random
from datetime import datetime
from mimesis import Person, Address, Finance, Datetime
from src.data_generators.providers.brazil_provider import BrazilProvider
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
address = Address(Locale.PT_BR)
finance = Finance(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilProvider()


def generate_establishments(n_establishments, df_cnae, df_mcc, df_municipalities, cnae_products_mapping, cnae_with_products_ratio=0.85):
    """Generate establishments DataFrame with intelligent CNAE selection
    Args:
        n_establishments: Number of establishments to generate
        df_cnae: Polars DataFrame with CNAE codes
        df_mcc: Polars DataFrame with MCC codes
        df_municipalities: Polars DataFrame with municipalities
        cnae_products_mapping: Dictionary mapping CNAE patterns to products
        cnae_with_products_ratio: Ratio of establishments that should have CNAEs accepting products (default 0.85)
    """

    establishments = []
    
    # Get CNAEs that accept products and all available CNAEs
    cnaes_with_products = set()
    for cnae_pattern in cnae_products_mapping.keys():
        # Find CNAEs that match patterns (exact or partial)
        matching_cnaes = df_cnae.filter(
            pl.col('subclasse_id').str.starts_with(cnae_pattern)
        )['subclasse_id'].to_list()
        cnaes_with_products.update(matching_cnaes)
    
    cnaes_with_products = list(cnaes_with_products)
    all_cnaes = df_cnae['subclasse_id'].to_list()
    cnaes_without_products = [cnae for cnae in all_cnaes if cnae not in cnaes_with_products]
    
    # Calculate how many establishments should have product-accepting CNAEs
    n_with_products = int(n_establishments * cnae_with_products_ratio)
    n_without_products = n_establishments - n_with_products
    
    # Get lists for random selection
    mcc_codes = df_mcc['mcc_code'].to_list()
    municipality_ids = df_municipalities['municipality_id'].to_list()
    
    # Status options
    statuses = ["ATIVA", "INATIVA", "SUSPENSA", "BAIXADA"]
    
    for i in range(n_establishments):
        # Intelligent CNAE selection
        if i < n_with_products and cnaes_with_products:
            # Select from CNAEs that accept products
            main_cnae_id = random.choice(cnaes_with_products)
        else:
            # Select from any CNAE (including those without products)
            main_cnae_id = random.choice(all_cnaes)
        
        # Select municipality and get corresponding state
        selected_municipality_id = random.choice(municipality_ids)
        state_id = df_municipalities.filter(
            pl.col('municipality_id') == selected_municipality_id
        )['state_id'].item()
        
        establishment = {
            'establishment_id': f"EST_{i}",
            'cnpj': brazil.cnpj(),  # CNPJ format
            'legal_name': finance.company(),
            'trade_name': f"{finance.company()} {person.surname()}",
            'main_cnae': main_cnae_id,
            'mcc_code': random.choice(mcc_codes),
            'municipality_id': selected_municipality_id,
            'state_id': state_id,
            'status': random.choice(statuses),
            'accreditation_date': datetime_provider.date(start=2010, end=2024),
            'created_date': datetime.now(),
            'updated_at': datetime.now()
        }
        establishments.append(establishment)
    
    return pl.DataFrame(establishments)
