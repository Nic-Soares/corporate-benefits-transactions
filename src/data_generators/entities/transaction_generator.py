import polars as pl
import random
import numpy as np
from datetime import datetime
import faker

fake = faker.Faker('pt_BR')


def gerar_valor_transacao(max_valor=1000, escala=250):
    """
    Gera um valor aleatório progressivo para transação.
    Quanto maior o valor, menor a chance de ocorrer.
    """
    valor = np.random.exponential(scale=escala)
    return round(min(valor, max_valor), 2)


def _sample_scalar(df: pl.DataFrame, col: str, filter_expr=None, default=None):
    """Retorna um valor aleatório da coluna `col`. Se vazio, retorna `default`."""
    sel = df.filter(filter_expr) if filter_expr is not None else df
    if sel.is_empty():
        return default
    return sel.select(pl.col(col)).sample(1).to_series()[0]


def generate_single_transaction(cards_df, establishments_df, terminals_df, card_products_df):
    # escolhe um terminal (garante estabelecimento com terminal)
    terminal_row = terminals_df.sample(1).to_dicts()[0]
    terminal_id = terminal_row['terminal_id']
    establishment_id = terminal_row['establishment_id']

    # escolhe cartão e produto (produto pode ser None)
    card_id = _sample_scalar(cards_df, 'card_id')
    product_id = _sample_scalar(card_products_df, 'product_id', filter_expr=(pl.col('card_id') == card_id), default=None)

    amount = gerar_valor_transacao(max_valor=500, escala=100)
    tx_date = fake.date_time_between(start_date='-30d', end_date='now')

    transaction = {
        "transaction_id": str(fake.uuid4()),
        "card_id": card_id,
        "product_id": product_id,
        "establishment_id": establishment_id,
        "terminal_id": terminal_id,
        "amount": amount,
        "date": tx_date,
        "capture_type": random.choice(['chip', 'magnetic_stripe', 'contactless', 'nfc']),
        "response_code": None,
        "response_message": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    return transaction
