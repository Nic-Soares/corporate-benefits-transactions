import polars as pl
from datetime import datetime


def generate_products(config_files_updated):
    """Generates products DataFrame based on business rules"""
    produtos = []
    for codigo, dados in config_files_updated['products'].items():
        produto = {
            'product_id': f"PROD_{dados['code'].upper()}",
            'code': dados['code'],
            'name': dados['name'],
            'category': dados['category'],
            'description': f"Produto de {dados['name']}",
            'active': True,
            'created_at': datetime.now()
        }
        produtos.append(produto)

    produtos_df = pl.DataFrame(produtos)
    # Em polars, para categorizar, use pl.Categorical
    produtos_df = produtos_df.with_columns([
        pl.col('code').cast(pl.Categorical),
        pl.col('name').cast(pl.Categorical),
        pl.col('category').cast(pl.Categorical)
    ])
    return produtos_df
