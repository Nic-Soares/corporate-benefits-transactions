import polars as pl
import random
from datetime import datetime
from mimesis import Person, Datetime
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()


def generate_cardholders(n_funcionarios, companies_df, municipalities_df):
    """Generate cardholders DataFrame based on existing companies data"""
    
    # Pre-select data for performance
    company_ids = companies_df['company_id'].to_list()
    municipality_ids = municipalities_df['municipality_id'].to_list()
    statuses = ['active', 'inactive', 'terminated']
    
    cardholders = []
    for idx in range(n_funcionarios):
        cardholders.append({
            'cardholder_id': f"FUNC_{idx}",
            'company_id': random.choice(company_ids),
            'name': person.full_name(),
            'cpf': brazil.cpf(),
            'municipality_id': random.choice(municipality_ids),
            'admission_date': datetime_provider.date(start=2014, end=2024),
            'position': person.occupation(),
            # 'department': text.word().title(),
            'status': random.choice(statuses),
            'created_at': datetime.now()
        })
    
    return pl.DataFrame(cardholders)
