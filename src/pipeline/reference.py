"""Reference tables: the config's rules, in the columns of the OLTP schema."""

import polars as pl
import psycopg

from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.card_program_loader import (
    load_card_program_wallets,
    load_card_programs,
    load_cnae_wallets,
    load_mcc_wallets,
)
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.response_codes_loader import load_response_codes
from src.data_generators.reference_data.wallet_loader import load_wallets
from src.infrastructure.database.postgres_manager import upsert_dataframe
from src.utils.read_yamls import load_pre_populated_data, load_validation_rules

# Brand letters of `mcc_acceptance_rules` → modality id
BRANDS = {"E": "ELO", "M": "MASTERCARD", "V": "VISA"}

# Primary key of each table, in load order (parents first)
REFERENCE_KEYS: dict[str, list[str]] = {
    "wallets": ["id"],
    "transaction_modalities": ["id"],
    "acquirers": ["id"],
    "response_codes": ["id"],
    "card_programs": ["id"],
    "card_program_wallets": ["program_id", "wallet_id"],
    "cnae_wallets": ["cnae_code", "wallet_id"],
    "mcc_wallets": ["mcc_code", "wallet_id"],
    "mcc_modalities": ["mcc_code", "modality_id"],
}


def cnae_descriptions(cnae_df: pl.DataFrame) -> dict[str, str]:
    """CNAE code → description, for classes (4 digits, no check digit) and subclasses."""
    classes = cnae_df.select(pl.col("classe_id").str.slice(0, 4), "classe").unique("classe_id")
    subclasses = cnae_df.select("subclasse_id", "subclasse")
    return dict(classes.iter_rows()) | dict(subclasses.iter_rows())


def mcc_modalities(mcc_df: pl.DataFrame) -> pl.DataFrame:
    """MCC × brand that accepts it (`validation_rules.yaml → mcc_acceptance_rules`)."""
    descriptions = dict(mcc_df.select("mcc_code", "description").iter_rows())
    rows = [
        {
            "mcc_code": mcc,
            "modality_id": BRANDS[letter.strip()],
            "mcc_description": descriptions.get(mcc, f"MCC {mcc}"),
            "observation": None,
            "active": True,
        }
        for mcc, letters in load_validation_rules()["mcc_acceptance_rules"].items()
        for letter in letters.split(",")
    ]
    return pl.DataFrame(rows, schema_overrides={"observation": pl.String})


def build_reference_tables(cnae_df: pl.DataFrame, mcc_df: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Every reference table, in load order."""
    data = load_pre_populated_data()
    descriptions = cnae_descriptions(cnae_df)
    cnae_wallets = load_cnae_wallets(data).with_columns(
        cnae_description=pl.col("cnae_code").replace_strict(
            descriptions, default=None, return_dtype=pl.String
        )
    )
    tables = {
        "wallets": load_wallets(data),
        "transaction_modalities": load_transaction_modalities(data),
        "acquirers": load_acquirers(data),
        "response_codes": load_response_codes(data),
        "card_programs": load_card_programs(data),
        "card_program_wallets": load_card_program_wallets(data),
        "cnae_wallets": cnae_wallets,
        "mcc_wallets": load_mcc_wallets(data),
        "mcc_modalities": mcc_modalities(mcc_df),
    }
    return {name: tables[name] for name in REFERENCE_KEYS}


def load_reference_tables(conn: psycopg.Connection, tables: dict[str, pl.DataFrame]) -> None:
    """Upsert: a second run leaves the same rows."""
    for table, df in tables.items():
        upsert_dataframe(
            conn,
            table,
            df.with_columns(pl.col(pl.Categorical).cast(pl.String)),
            REFERENCE_KEYS[table],
        )
