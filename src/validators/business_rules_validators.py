"""Business-rule validations: where each wallet can be used.

Proprietary-network cards (`OWN`, the 3-party model): the cardholder picks an
option on the terminal (Food, Meal or Others) and the issuer routes inside it;
the establishment's CNAE must accept the wallet. Brand cards (Visa,
Mastercard, Elo: the 4-party model): the brand must accept the establishment's
MCC, and the issuer picks the wallet from that MCC.
"""

from typing import Any

import polars as pl

from src.validators._common import (
    PASS,
    PROPRIETARY_MODALITIES,
    RULES,
    Table,
    as_table,
    fail,
    find_all,
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


def _accepted_by_cnae(cnae: str, cnae_wallets_df: pl.DataFrame | Table) -> set[str]:
    """Wallets the CNAE takes: the active rules of its longest matching prefix."""
    matching = [r for r in as_table(cnae_wallets_df).rows if cnae.startswith(r["cnae_code"])]
    if not matching:
        return set()
    longest = max(len(r["cnae_code"]) for r in matching)
    return {r["wallet_id"] for r in matching if len(r["cnae_code"]) == longest and r["active"]}


def route_wallet(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    card_wallets_df: pl.DataFrame | Table,
    wallets_df: pl.DataFrame,
    cnae_wallets_df: pl.DataFrame,
    mcc_wallets_df: pl.DataFrame,
) -> dict[str, Any]:
    """The card wallet the issuer charges; it comes back as `card_wallet_id`.

    The candidates, in order: proprietary network — the wallets of the option
    picked on the terminal (`wallet_option`); brand — `wallet_priority`; cash
    withdrawal — `withdrawal_wallets`, brand cards only. Each must be held by
    the card, active (card wallet and wallet), accepted here (CNAE on the
    proprietary network, MCC on a brand; GIFT takes any MCC) and have the
    balance; the first that passes wins. The first step no candidate passes
    gives the reason (57), and balance is last (51), with the first candidate.
    """
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure

    rule = BUSINESS_RULES["wallet_routing"]
    proprietary = card["modality_id"] in PROPRIETARY_MODALITIES
    if transaction["transaction_type"] == "withdrawal":
        if proprietary:
            return fail(rule["error_code"], "withdrawal_not_allowed")
        priority = rule["withdrawal_wallets"]
    elif proprietary:
        priority = rule["proprietary_options"].get(transaction["wallet_option"], [])
    else:
        priority = rule["wallet_priority"]

    held = {row["wallet_id"]: row for row in find_all(card_wallets_df, card_id=card["id"])}
    candidates = [held[wallet] for wallet in priority if wallet in held]
    if not candidates:
        return fail(rule["error_code"], "wallet_not_on_card")

    enabled = {row["id"] for row in find_all(wallets_df, active=True)}
    candidates = [c for c in candidates if c["status"] == "active" and c["wallet_id"] in enabled]
    if not candidates:
        return fail(rule["error_code"], "card_wallet_inactive")

    if proprietary:
        accepted = _accepted_by_cnae(establishment["main_cnae"], cnae_wallets_df)
        reason = "wallet_not_accepted_at_cnae"
    else:
        accepted = {
            row["wallet_id"] for row in find_all(mcc_wallets_df, mcc_code=establishment["mcc_code"])
        }
        accepted.add(OPEN_WALLET)
        reason = "no_wallet_for_mcc"
    candidates = [c for c in candidates if c["wallet_id"] in accepted]
    if not candidates:
        return fail(rule["error_code"], reason)

    for card_wallet in candidates:
        if card_wallet["current_balance"] >= transaction["amount"]:
            return PASS | {"card_wallet_id": card_wallet["id"]}
    # Declined for balance: the wallet it would have charged first comes back too
    balance_code = RULES["balance_and_limits_validations"]["current_balance"]["error_code"]
    return fail(balance_code, "insufficient_balance") | {"card_wallet_id": candidates[0]["id"]}
