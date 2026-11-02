"""Reference tables: `config/reference.yaml` in the columns of the OLTP
schema, and their load into Postgres."""

from typing import Any

import polars as pl
import psycopg

from src.config import load_reference
from src.postgres import upsert_dataframe


def load_wallets(data: dict[str, Any]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"id": w["id"], "name": w["name"], "category": w["category"], "active": True}
            for w in data["wallets"]
        ]
    )


def load_transaction_modalities(data: dict[str, Any]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"id": m["id"], "name": m["name"], "type": m["type"], "active": True}
            for m in data["transaction_modalities"]
        ]
    )


def load_acquirers(data: dict[str, Any]) -> pl.DataFrame:
    return pl.DataFrame(
        [{"id": a["id"], "name": a["name"], "active": True} for a in data["acquirers"]]
    )


def load_response_codes(data: dict[str, Any]) -> pl.DataFrame:
    return pl.DataFrame(
        [{"id": code, "description": text} for code, text in data["response_codes"].items()]
    )


def load_card_programs(data: dict[str, Any]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"id": p["id"], "name": p["name"], "network_type": p["network_type"], "active": True}
            for p in data["card_programs"]
        ]
    )


def load_card_program_wallets(data: dict[str, Any]) -> pl.DataFrame:
    """Which wallets each program holds (`card_program_wallets`)."""
    return pl.DataFrame(
        [
            {"program_id": p["id"], "wallet_id": wallet}
            for p in data["card_programs"]
            for wallet in p["wallets"]
        ]
    )


def load_mcc_wallets(data: dict[str, Any]) -> pl.DataFrame:
    """MCC × wallet for brand cards (`mcc_wallets`); the open GIFT wallet has no rows."""
    return pl.DataFrame(
        [
            {"mcc_code": mcc, "wallet_id": wallet}
            for wallet, mccs in data["mcc_wallets"].items()
            if isinstance(mccs, list)
            for mcc in mccs
        ]
    )


def load_cnae_wallets(data: dict[str, Any]) -> pl.DataFrame:
    """CNAE prefix × wallet for the proprietary network (`cnae_wallets`)."""
    return pl.DataFrame(
        [
            {"cnae_code": cnae, "wallet_id": wallet, "active": True}
            for cnae, wallets in data["cnae_wallets"].items()
            for wallet in wallets
        ]
    )


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
    """MCC × brand that accepts it (`reference.yaml → mcc_acceptance_rules`)."""
    descriptions = dict(mcc_df.select("mcc_code", "description").iter_rows())
    rows = [
        {
            "mcc_code": mcc,
            "modality_id": BRANDS[letter.strip()],
            "mcc_description": descriptions.get(mcc, f"MCC {mcc}"),
            "observation": None,
            "active": True,
        }
        for mcc, letters in load_reference()["mcc_acceptance_rules"].items()
        for letter in letters.split(",")
    ]
    return pl.DataFrame(rows, schema_overrides={"observation": pl.String})


def build_reference_tables(cnae_df: pl.DataFrame, mcc_df: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Every reference table, in load order."""
    data = load_reference()
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
        upsert_dataframe(conn, table, df, REFERENCE_KEYS[table])
