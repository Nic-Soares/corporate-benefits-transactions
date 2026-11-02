"""Reference-data loaders read config/reference.yaml into DataFrames."""

import pytest

from src.config import load_reference
from src.reference import (
    load_acquirers,
    load_card_program_wallets,
    load_card_programs,
    load_cnae_wallets,
    load_mcc_wallets,
    load_response_codes,
    load_transaction_modalities,
    load_wallets,
)

DATA = load_reference()


@pytest.mark.parametrize(
    ("loader", "key", "columns"),
    [
        (load_wallets, "wallets", ["id", "name", "category", "active"]),
        (load_acquirers, "acquirers", ["id", "name", "active"]),
        (load_transaction_modalities, "transaction_modalities", ["id", "name", "type", "active"]),
        (load_card_programs, "card_programs", ["id", "name", "network_type", "active"]),
        (load_response_codes, "response_codes", ["id", "description"]),
    ],
)
def test_loader(loader, key, columns):
    df = loader(DATA)

    assert df.columns == columns
    assert len(df) == len(DATA[key])
    assert df["id"].n_unique() == len(df)
    if "active" in columns:
        assert df["active"].all()


def test_program_wallet_and_rule_loaders():
    program_wallets = load_card_program_wallets(DATA)
    assert len(program_wallets) == sum(len(p["wallets"]) for p in DATA["card_programs"])
    assert set(program_wallets["wallet_id"]) <= {w["id"] for w in DATA["wallets"]}

    cnae = load_cnae_wallets(DATA)
    assert cnae.columns == ["cnae_code", "wallet_id", "active"]
    assert set(cnae["wallet_id"]) <= {w["id"] for w in DATA["wallets"]}

    mcc = load_mcc_wallets(DATA)
    assert mcc.columns == ["mcc_code", "wallet_id"]
    assert "GIFT" not in set(mcc["wallet_id"])  # the open wallet takes any MCC
    assert mcc.select("mcc_code", "wallet_id").n_unique() == len(mcc)
