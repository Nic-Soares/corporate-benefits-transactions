# %% Cell 1 - Setup
import sys
from pathlib import Path

project_root = Path.cwd().parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from src.utils.parquet_utils import save_df_to_parquet
from src.utils.csv_utils import save_df_to_csv
from src.data_generators.reference_data.mcc_and_cnae_loader import extract_mcc_data

output_dir = project_root / "data" / "output"

# %% Cell 2 - Criar DataFrame de teste
df = extract_mcc_data()

print(df)

# %% Cell 3 - Salvar como Parquet (snappy)
save_df_to_parquet(df, output_dir / "test_snappy.parquet", compression="snappy")

# %% Cell 4 - Salvar como Parquet (zstd)
save_df_to_parquet(df, output_dir / "test_zstd.parquet", compression="zstd")

# %% Cell 5 - Salvar como CSV (ISO 8601)
save_df_to_csv(df, output_dir / "test.csv")

# %% Cell 6 - Salvar CSV com ponto e vírgula
save_df_to_csv(df, output_dir / "test_semicolon.csv", separator=";")

# %%
