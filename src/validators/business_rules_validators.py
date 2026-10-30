"""Business-rule validations: where each card may be used.

Branded cards (`cards.modality_id` set) are authorized by the establishment's
MCC; proprietary-network cards (`modality_id` null) by its CNAE. Each
validator passes the cards the other network rule applies to.
"""

from typing import Any

import polars as pl

from src.validators._common import NOT_FOUND, PASS, RULES, fail, find_one

BUSINESS_RULES = RULES["business_rules_validations"]


def _card_and_establishment(
    transaction: dict[str, Any], cards_df: pl.DataFrame, establishments_df: pl.DataFrame
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """(card, establishment, failure) — failure is set when a record is missing."""
    card = find_one(cards_df, id=transaction["card_id"])
    if card is None:
        return None, None, fail(NOT_FOUND["card"])
    establishment = find_one(establishments_df, id=transaction["establishment_id"])
    if establishment is None:
        return card, None, fail(NOT_FOUND["establishment"])
    return card, establishment, None


def validate_mcc_modality(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    mcc_modalities_df: pl.DataFrame,
) -> dict[str, Any]:
    """`mcc_modality_mapping` (rule missing) and `mcc_modality_rules_active` (rule inactive)."""
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure
    if card["modality_id"] is None:
        return PASS  # proprietary network: the CNAE rule applies

    rule = find_one(
        mcc_modalities_df, mcc_code=establishment["mcc_code"], modality_id=card["modality_id"]
    )
    if rule is None:
        return fail(BUSINESS_RULES["mcc_modality_mapping"]["error_code"])
    if not rule["active"]:
        return fail(BUSINESS_RULES["mcc_modality_rules_active"]["error_code"])
    return PASS


def validate_cnae_product(
    transaction: dict[str, Any],
    cards_df: pl.DataFrame,
    establishments_df: pl.DataFrame,
    cnae_products_df: pl.DataFrame,
) -> dict[str, Any]:
    """`cnae_product_mapping` (rule missing) and `cnae_product_rules_active` (rule inactive).

    `cnae_products.cnae_code` holds CNAE prefixes at several levels (e.g. `5611`,
    `5611201`); the longest prefix of the establishment's CNAE decides.
    """
    card, establishment, failure = _card_and_establishment(transaction, cards_df, establishments_df)
    if failure:
        return failure
    if card["modality_id"] is not None:
        return PASS  # branded card: the MCC rule applies

    prefix_len = pl.col("cnae_code").str.len_chars()
    matching = cnae_products_df.filter(
        pl.lit(establishment["main_cnae"]).str.starts_with(pl.col("cnae_code"))
    )
    most_specific = matching.filter(prefix_len == prefix_len.max())

    rule = find_one(most_specific, product_id=transaction["product_id"])
    if rule is None:
        return fail(BUSINESS_RULES["cnae_product_mapping"]["error_code"])
    if not rule["active"]:
        return fail(BUSINESS_RULES["cnae_product_rules_active"]["error_code"])
    return PASS
