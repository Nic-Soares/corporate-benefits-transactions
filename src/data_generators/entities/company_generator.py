import polars as pl
import random
from datetime import datetime
from mimesis import Person, Finance, Datetime
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
finance = Finance(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()


def generate_companies(n_companies, municipalities, segments):
    
    # Pre-select data for performance
    segment_ids = segments['segment_id'].to_list()
    municipality_ids = municipalities['municipality_id'].to_list()
    company_types = ["Privada", "Publica"]
    
    companies = []
    for idx in range(n_companies):
        parent_id = random.choice([None] + [c["company_id"] for c in companies]) if companies else None
        
        companies.append({
            'company_id': f"EMP_{idx}",
            'parent_company_id': parent_id,
            'name': finance.company(),
            'cnpj': brazil.cnpj(), 
            'company_type': random.choice(company_types),
            'segment_id': random.choice(segment_ids),
            'municipality_id': random.choice(municipality_ids),
            'contract_registration_date': datetime_provider.date(start=2019, end=2024),
            'created_at': datetime.now()
        })
    
    return pl.DataFrame(companies)
