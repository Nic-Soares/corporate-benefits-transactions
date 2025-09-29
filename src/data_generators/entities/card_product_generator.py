import polars as pl
import random
from datetime import datetime
from mimesis import Person, Datetime
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)


def generate_card_products(cards_df, products_df, min_products=1, max_products=3):
    """Generate products associated with cards"""
    person = Person(Locale.PT_BR)
    
    card_ids = cards_df['card_id'].to_list()
    product_ids = products_df['product_id'].to_list()
    statuses = ['active', 'suspended', 'cancelled']
    
    card_products = []
    for card_id in card_ids:
        n_products = random.randint(min_products, max_products)
        for _ in range(n_products):
            activation_date = datetime_provider.date(start=2010, end=2024)
            
            # 30% chance of being deactivated
            if random.random() < 0.3:
                deactivation_date = datetime_provider.date(start=activation_date.year, end=2024)
                status = random.choice(['suspended', 'cancelled'])
            else:
                deactivation_date = None
                status = 'active'
            
            card_products.append({
                "card_product_id": person.identifier(),
                "card_id": card_id,
                "product_id": random.choice(product_ids),
                "current_balance": round(random.uniform(0, 5000), 2),
                "daily_limit": round(random.uniform(100, 2000), 2),
                "monthly_limit": round(random.uniform(1000, 10000), 2),
                "activation_date": activation_date,
                "deactivation_date": deactivation_date,
                "status": status,
                "created_at": datetime.now()
            })
    
    return pl.DataFrame(card_products)