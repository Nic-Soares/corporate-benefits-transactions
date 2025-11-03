# %% Cell 1
import os
import sys
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
print("=== Testando Capture Technologies Loader ===")

df_capture_technologies = load_capture_technologies(pre_populated_data)

print(f"Lines: {len(df_capture_technologies)}")
print(f"Columns: {df_capture_technologies.columns}")
print(f"Data Types: {df_capture_technologies.dtypes}")

print(df_capture_technologies)

# %% Cell 5 - Teste do modalities_loader
print("=== Testando Modalities Loader ===")

from src.data_generators.reference_data.modalities_loader import load_modalities

df_modalities = load_modalities(pre_populated_data)

print(f"Lines: {len(df_modalities)}")
print(f"Columns: {df_modalities.columns}")
print(f"Data Types: {df_modalities.dtypes}")

print(df_modalities)

# %% Cell 6 - Teste do segment_loader
print("=== Testando Segment Loader ===")

from src.data_generators.reference_data.segment_loader import load_segments

df_segments = load_segments(pre_populated_data)

print(f"Lines: {len(df_segments)}")
print(f"Columns: {df_segments.columns}")
print(f"Data Types: {df_segments.dtypes}")

print(df_segments)

# %% Cell 7 - Teste do mcc_and_cnae_loader
print("=== Testando MCC Loader ===")

from src.data_generators.reference_data.mcc_and_cnae_loader import extract_mcc_data

df_mcc = extract_mcc_data()

print(f"Lines: {len(df_mcc)}")
print(f"Columns: {df_mcc.columns}")
print(f"Data Types: {df_mcc.dtypes}")

print(df_mcc.head(10))

# %% Cell 8 - Teste do cnae_loader
print("=== Testando CNAE Loader ===")

from src.data_generators.reference_data.mcc_and_cnae_loader import extract_cnae_data

df_cnae = extract_cnae_data()

print(f"Lines: {len(df_cnae)}")
print(f"Columns: {df_cnae.columns}")
print(f"Data Types: {df_cnae.dtypes}")

print(df_cnae.head(10))

# %% Cell 9 - Teste do response_codes_loader
print("=== Testando Response Codes Loader ===")

from src.data_generators.reference_data.response_codes_loader import load_response_codes

df_response_codes = load_response_codes(pre_populated_data)

print(f"Lines: {len(df_response_codes)}")
print(f"Columns: {df_response_codes.columns}")
print(f"Data Types: {df_response_codes.dtypes}")

print(df_response_codes)

# %%
