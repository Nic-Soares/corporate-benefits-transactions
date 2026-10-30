from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.capture_technologies_loader import load_capture_technologies
from src.data_generators.reference_data.card_program_loader import (
    load_card_program_wallets,
    load_card_programs,
    load_cnae_wallets,
    load_mcc_wallets,
)
from src.data_generators.reference_data.mcc_and_cnae_loader import (
    extract_cnae_data,
    extract_mcc_data,
)
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.response_codes_loader import load_response_codes
from src.data_generators.reference_data.segment_loader import load_segments
from src.data_generators.reference_data.wallet_loader import load_wallets
from src.utils.parquet_utils import save_multiple_dfs_to_parquet
from src.utils.read_yamls import CONFIG_DIR, load_pre_populated_data


def main() -> None:
    pre_populated_data = load_pre_populated_data()

    dfs = {
        "wallets": load_wallets(pre_populated_data),
        "card_programs": load_card_programs(pre_populated_data),
        "card_program_wallets": load_card_program_wallets(pre_populated_data),
        "cnae_wallets": load_cnae_wallets(pre_populated_data),
        "mcc_wallets": load_mcc_wallets(pre_populated_data),
        "acquirers": load_acquirers(pre_populated_data),
        "response_codes": load_response_codes(pre_populated_data),
        "capture_technologies": load_capture_technologies(pre_populated_data),
        "modalities": load_transaction_modalities(pre_populated_data),
        "segments": load_segments(pre_populated_data),
        "mcc": extract_mcc_data(),
        "cnae": extract_cnae_data(),
    }

    save_multiple_dfs_to_parquet(
        dfs, str(CONFIG_DIR.parent / "data/reference_data"), compression="zstd"
    )


if __name__ == "__main__":
    main()
