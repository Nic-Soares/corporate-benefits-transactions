"""Security validations: the cardholder is who they say they are."""

from typing import Any

from src.validators._common import PASS, RULES, fail

SECURITY_RULES = RULES["security_validations"]


def validate_pin(transaction: dict[str, Any]) -> dict[str, Any]:
    """`pin_status` is `ok`, `wrong` or `not_required` (contactless, wallets, e-commerce)."""
    if transaction["pin_status"] == "wrong":
        return fail(SECURITY_RULES["pin"]["error_code"], "wrong_pin")
    return PASS
