from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.capture_technologies_loader import load_capture_technologies
from src.data_generators.reference_data.mcc_and_cnae_loader import (
    extract_cnae_data,
    extract_mcc_data,
)
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.product_loader import load_products
from src.data_generators.reference_data.response_codes_loader import load_response_codes
from src.data_generators.reference_data.segment_loader import load_segments
from src.utils.parquet_utils import save_multiple_dfs_to_parquet
from src.utils.read_yamls import load_pre_populated_data

# Carregar dados de configuração
pre_populated_data = load_pre_populated_data()

# Dicionário com todos os loaders
dfs = {
    "products": load_products(pre_populated_data),
    "acquirers": load_acquirers(pre_populated_data),
    "response_codes": load_response_codes(pre_populated_data),
    "capture_technologies": load_capture_technologies(pre_populated_data),
    "modalities": load_transaction_modalities(pre_populated_data),
    "segments": load_segments(pre_populated_data),
    "mcc": extract_mcc_data(),
    "cnae": extract_cnae_data(),
}

save_multiple_dfs_to_parquet(dfs, "data/reference_data/", compression="zstd")
