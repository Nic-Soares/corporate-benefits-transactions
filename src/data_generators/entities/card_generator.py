import polars as pl
import random
from datetime import datetime
from mimesis import Person, Datetime, Numeric
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
numeric = Numeric()
datetime_provider = Datetime(Locale.PT_BR)


def generate_cards(n_cards, cardholders_df, modality_df):
    person = Person(Locale.PT_BR)
    numeric = Numeric()
    
    # Pre-select data for performance
    cardholder_ids = cardholders_df['cardholder_id'].to_list()
    modality_ids = modality_df['modality_id'].to_list()
    card_types = ['credit', 'debit']
    statuses = ['active', 'inactive', 'blocked', 'canceled']
    
    cards = []
    for idx in range(n_cards):
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        formatted_card_number = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
        cvv = "".join([str(random.randint(0, 9)) for _ in range(3)])
        
        cards.append({
            "card_id": idx,
            "cardholder_id": random.choice(cardholder_ids),
            "card_number": formatted_card_number,
            "modality_id": random.choice(modality_ids),
            "expiration_date": datetime_provider.date(start=2024, end=2029),
            "cvv": cvv,
            "card_type": random.choice(card_types),
            "issuance_date": datetime.now(),
            "status": random.choice(statuses),
            "created_at": datetime.now()
        })
    
    return pl.DataFrame(cards)
