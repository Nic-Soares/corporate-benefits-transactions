from typing import Any

import polars as pl


def load_card_programs(pre_populated_data: dict[str, Any]) -> pl.DataFrame:
    """Card programs from `pre_populated_data.yaml` (columns of `card_programs`)."""
    programs = [
        {
            "id": program["id"],
            "name": program["name"],
            "network_type": program["network_type"],
            "active": True,
        }
        for program in pre_populated_data["card_programs"]
    ]
    return pl.DataFrame(programs)


def load_card_program_wallets(pre_populated_data: dict[str, Any]) -> pl.DataFrame:
    """Which wallets each program holds (`card_program_wallets`)."""
    rows = [
        {"program_id": program["id"], "wallet_id": wallet}
        for program in pre_populated_data["card_programs"]
        for wallet in program["wallets"]
    ]
    return pl.DataFrame(rows)


def load_mcc_wallets(pre_populated_data: dict[str, Any]) -> pl.DataFrame:
    """MCC × wallet for brand cards (`mcc_wallets`); the open GIFT wallet has no rows."""
    rows = [
        {"mcc_code": mcc, "wallet_id": wallet}
        for wallet, mccs in pre_populated_data["mcc_wallets"].items()
        if isinstance(mccs, list)
        for mcc in mccs
    ]
    return pl.DataFrame(rows)


def load_cnae_wallets(pre_populated_data: dict[str, Any]) -> pl.DataFrame:
    """CNAE prefix × wallet for the proprietary network (`cnae_wallets`)."""
    rows = [
        {"cnae_code": cnae, "wallet_id": wallet, "active": True}
        for cnae, wallets in pre_populated_data["cnae_wallets"].items()
        for wallet in wallets
    ]
    return pl.DataFrame(rows)
