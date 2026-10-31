"""Business-rule validations: where each wallet can be used.

Proprietary-network cards (`OWN`, the 3-party model): the cardholder picks the
wallet on the terminal, and the establishment's CNAE must accept it.
Brand cards (Visa, Mastercard, Elo: the 4-party model): the brand must accept
the establishment's MCC, and the issuer picks the wallet from that MCC.
Each validator passes the cards of the other network, so a caller runs all.
"""

from typing import Any

import polars as pl

from src.validators._common import (
    PASS,
    PROPRIETARY_MODALITIES,
    RULES,
    fail,
    find_one,
    not_found,
)

BUSINESS_RULES = RULES["business_rules_validations"]
OPEN_WALLET = "GIFT"  # takes any MCC the brand accepts


def _card_and_establishment(
    transaction: dict[str, Any], cards_df: pl.DataFrame, establishments_df: pl.DataFrame
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """(card, establishment, failure) — failure is set when a record is missing."""
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return None, None, not_found("card")
    establishment = find_one(establishments_df, id=transaction["establishment_id"])
    if establishment is None:
        return card, None, not_found("establishment")
    return card, establishment, None


def validate_cnae_wallet(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    card_wallets_df: pl.DataFrame,
    cnae_wallets_df: pl.DataFrame,
) -> dict[str, Any]:
    """The establishment's CNAE accepts the chosen wallet.

    `cnae_wallets.cnae_code` holds CNAE prefixes at several levels (e.g. `5611`,
    `5611201`); the longest prefix of the establishment's CNAE decides.
    """
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure
    if card["modality_id"] not in PROPRIETARY_MODALITIES:
        return PASS  # brand card: the MCC rules apply
    card_wallet = find_one(
        card_wallets_df, id=transaction["card_wallet_id"], card_id=transaction["card_id"]
    )
    if card_wallet is None:
        return not_found("card_wallet")

    prefix_len = pl.col("cnae_code").str.len_chars()
    matching = cnae_wallets_df.filter(
        pl.lit(establishment["main_cnae"]).str.starts_with(pl.col("cnae_code"))
    )
    most_specific = matching.filter(prefix_len == prefix_len.max())

    error_code = BUSINESS_RULES["cnae_wallet"]["error_code"]
    rule = find_one(most_specific, wallet_id=card_wallet["wallet_id"])
    if rule is None:
        return fail(error_code, "wallet_not_accepted_at_cnae")
    if not rule["active"]:
        return fail(error_code, "cnae_rule_inactive")
    return PASS


def validate_mcc_brand(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    mcc_modalities_df: pl.DataFrame,
) -> dict[str, Any]:
    """The card's brand accepts the establishment's MCC."""
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure
    if card["modality_id"] in PROPRIETARY_MODALITIES:
        return PASS  # proprietary network: the CNAE rule applies

    error_code = BUSINESS_RULES["mcc_brand"]["error_code"]
    rule = find_one(
        mcc_modalities_df, mcc_code=establishment["mcc_code"], modality_id=card["modality_id"]
    )
    if rule is None:
        return fail(error_code, "mcc_not_accepted_by_brand")
    if not rule["active"]:
        return fail(error_code, "mcc_rule_inactive")
    return PASS


def route_wallet(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    card_wallets_df: pl.DataFrame,
    mcc_wallets_df: pl.DataFrame,
) -> dict[str, Any]:
    """Brand cards: the wallet the issuer charges, in `wallet_priority` order.

    A candidate is a wallet the card holds, active, whose MCC list covers the
    establishment (GIFT takes any MCC). The first candidate with enough balance
    wins and comes back as `card_wallet_id`. No candidate → 57; candidates but none
    with enough balance → 51. Proprietary-network cards keep their chosen wallet.
    """
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure
    if card["modality_id"] in PROPRIETARY_MODALITIES:
        return PASS | {"card_wallet_id": transaction["card_wallet_id"]}

    rule = BUSINESS_RULES["wallet_routing"]
    at_mcc = set(mcc_wallets_df.filter(mcc_code=establishment["mcc_code"])["wallet_id"])
    held = {
        row["wallet_id"]: row
        for row in card_wallets_df.filter(card_id=card["id"], status="active").iter_rows(named=True)
    }
    candidates = [
        held[wallet]
        for wallet in rule["wallet_priority"]
        if wallet in held and (wallet in at_mcc or wallet == OPEN_WALLET)
    ]
    if not candidates:
        return fail(rule["error_code"], "no_wallet_for_mcc")
    for card_wallet in candidates:
        if card_wallet["current_balance"] >= transaction["amount"]:
            return PASS | {"card_wallet_id": card_wallet["id"]}
    balance_code = RULES["balance_and_limits_validations"]["current_balance"]["error_code"]
    return fail(balance_code, "insufficient_balance")
