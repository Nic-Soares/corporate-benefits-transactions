# %% Cell 1
import os
import sys

from src.data_generators.reference_data.capture_technologies_loader import load_capture_technologies

# Define o caminho da raiz do projeto diretamente
project_root = '/home/nicolas/Projects/Personal/corporate-benefits-transactions'
os.chdir(project_root)

# Adiciona o diretório raiz ao path do Python para imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import polars as pl
from src.data_generators.reference_data.product_loader import load_products
from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.capture_technologies_loader import load_capture_technologies
from src.utils.read_yamls import load_pre_populated_data

# Carregar dados de configuração
pre_populated_data = load_pre_populated_data()

# %% Cell 2 - Teste do product_loader
print("=== Testando Product Loader ===")

print(f"Dados carregados do YAML: {list(pre_populated_data.keys())}")

# Testar o loader
df_products = load_products(pre_populated_data)

print(f"\n📊 DataFrame de Produtos:")
print(f"   Linhas: {len(df_products)}")
print(f"   Colunas: {df_products.columns}")
print(f"   Tipos: {df_products.dtypes}")

print(f"\n📋 Dados:")
print(df_products)

print(f"\n✅ Teste concluído!")

# %% Cell 3 - Teste do acquirer_loader
print("=== Testando Acquirer Loader ===")

print(f"Dados carregados do YAML: {list(pre_populated_data.keys())}")

df_acquirers = load_acquirers(pre_populated_data)

print(f"Lines: {len(df_acquirers)}")
print(f"Columns: {df_acquirers.columns}")
print(f"Data Types: {df_acquirers.dtypes}")

print(df_acquirers)

# %% Cell 4 - Teste do capture_technologies_loader

df_capture_technologies = load_capture_technologies(pre_populated_data)

print(df_capture_technologies)
