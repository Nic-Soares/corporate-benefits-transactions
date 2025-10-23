from src.data_generators.reference_data.product_loader import load_products
from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.utils.parquet_utils import save_df_to_parquet, save_multiple_dfs_to_parquet

dfs ={"products": load_products, "acquirers": load_acquirers}
  
save_multiple_dfs_to_parquet(dfs, "data/reference_data/", compression="zstd")