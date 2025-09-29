import polars as pl
from datetime import datetime


def generate_transaction_modalities(config_files_updated):
    """Generates DataFrame for Transaction Modalities based on business rules"""
    transaction_modalities = []
    modalidades_yaml = config_files_updated['transaction_modalities']

    # Se for dict, usa .values(); se for lista, itera direto
    iterator = modalidades_yaml.values() if isinstance(modalidades_yaml, dict) else modalidades_yaml

    for idx, dados in enumerate(iterator, start=1):
        modality = {
            "modality_id": f"MOD_{idx}",
            "code": dados["name"].upper().replace(" ", "_"),
            "name": dados["name"],
            "type": "brand" if dados["name"].upper() in ["ELO", "MASTERCARD", "VISA"] else "proprietary_network",
            "active": True,
            "created_at": datetime.now()
        }
        transaction_modalities.append(modality)
    return pl.DataFrame(transaction_modalities)
