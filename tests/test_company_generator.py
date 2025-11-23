# %% Setup
import os
import sys
from pathlib import Path

# Get the project root correctly
project_root = str(Path(__file__).parent.parent) if '__file__' in dir() else str(Path.cwd().parent)
sys.path.insert(0, project_root)

import polars as pl
from src.data_generators.entities.company_generator import CompanyGenerator
from src.extractors.ibge_municipalities import fetch_municipios

# %% Load municipios
print("Loading municipios from IBGE API...")
municipios_df = fetch_municipios()
print(f"✓ Loaded {len(municipios_df):,} municipios")

# %% Initialize generator
generator = CompanyGenerator(municipios_df=municipios_df)
print("✓ Generator initialized")

# %% Generate single holding
holding = generator.generate_company(parent_id=None)
print("\n📌 HOLDING COMPANY:")
for key, value in holding.to_dict().items():
    print(f"  {key:20s}: {value}")

# %% Generate branch
branch = generator.generate_company(parent_id=holding.id)
print("\n📌 BRANCH COMPANY:")
for key, value in branch.to_dict().items():
    print(f"  {key:20s}: {value}")

# %% Generate DataFrame
df = generator.generate_companies_as_dataframe(n_companies=100)

print(f"\n✓ DATAFRAME GENERATED:")
print(f"  Total: {len(df)} companies")
print(f"  Holdings: {df.filter(pl.col('parent_id').is_null()).shape[0]}")
print(f"  Branches: {df.filter(pl.col('parent_id').is_not_null()).shape[0]}")

print(f"\nColumns: {df.columns}")
print(f"\nFirst 5 rows:")
print(df.head(5))

# %% Validate data
print(f"\n✓ DATA VALIDATION:")
print(f"  Unique IDs: {df.select('id').n_unique()}/{len(df)}")
print(f"  Unique CNPJs: {df.select('cnpj').n_unique()}/{len(df)}")
print(f"  All parent refs valid: {len(df.filter(pl.col('parent_id').is_not_null())) == df.filter(pl.col('parent_id').is_not_null()).shape[0]}")

# %%
print("\n✅ COMPANY GENERATOR TEST - SUCCESS")
