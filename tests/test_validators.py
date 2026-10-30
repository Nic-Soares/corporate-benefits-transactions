from datetime import date, datetime

import polars as pl
import pytest

from src.validators.balance_and_limits_validations import (
    validate_current_balance,
    validate_daily_limit,
    validate_monthly_limit,
)
from src.validators.business_rules_validators import validate_cnae_product, validate_mcc_modality
from src.validators.infrastructure_validations import validate_capture_type_support
from src.validators.status_validators import (
    validate_acquirer_active,
    validate_card_product_status,
    validate_card_status,
    validate_cardholder_status,
    validate_establishment_status,
    validate_modality_active,
    validate_product_active,
    validate_terminal_status,
)
from src.validators.temporal_validators import (
    validate_card_expiration,
    validate_cardholder_admission,
    validate_establishment_accreditation,
    validate_terminal_installation,
)

PASS = {"passed": True, "error_code": None}


def declined(code):
    return {"passed": False, "error_code": code}


@pytest.fixture
def tx():
    """A transaction that passes every validation against `data`."""
    return {
        "card_id": "card_branded",
        "product_id": "VR",
        "establishment_id": "est_restaurant",
        "terminal_id": "term_pos",
        "amount": 50.0,
        "date": datetime(2026, 6, 15, 12, 30),
        "capture_type": "contactless",
    }


@pytest.fixture
def data():
    return {
        "cards": pl.DataFrame(
            {
                "id": ["card_branded", "card_own", "card_blocked"],
                "cardholder_id": ["holder_1", "holder_1", "holder_off"],
                "modality_id": ["VISA", "OWN", "ELO"],
                "expiration_date": [date(2028, 1, 31)] * 3,
                "status": ["active", "active", "blocked"],
            }
        ),
        "cardholders": pl.DataFrame(
            {
                "id": ["holder_1", "holder_off"],
                "admission_date": [date(2020, 3, 1), date(2027, 1, 1)],
                "status": ["active", "terminated"],
            }
        ),
        "establishments": pl.DataFrame(
            {
                "id": ["est_restaurant", "est_closed"],
                "main_cnae": ["5611201", "4711302"],
                "mcc_code": ["5812", "5411"],
                "status": ["active", "terminated"],
                "accreditation_date": [date(2015, 5, 1), date(2027, 1, 1)],
            }
        ),
        "terminals": pl.DataFrame(
            {
                "id": ["term_pos", "term_tef"],
                "acquirer_id": ["CIE", "OFF"],
                "type": ["POS", "TEF"],
                "status": ["active", "inactive"],
                "installation_date": [date(2022, 1, 1), date(2027, 1, 1)],
            }
        ),
        "card_products": pl.DataFrame(
            {
                "card_id": ["card_branded", "card_own", "card_own"],
                "product_id": ["VR", "VR", "GF"],
                "current_balance": [500.0, 500.0, 500.0],
                "daily_limit": [100.0, 0.0, 0.0],
                "monthly_limit": [1000.0, 0.0, 0.0],
                "status": ["active", "active", "suspended"],
            }
        ),
        "products": pl.DataFrame({"id": ["VR", "GF"], "active": [True, False]}),
        "modalities": pl.DataFrame({"id": ["VISA", "OWN", "ELO"], "active": [True, True, False]}),
        "acquirers": pl.DataFrame({"id": ["CIE", "OFF"], "active": [True, False]}),
        "mcc_modalities": pl.DataFrame(
            {
                "mcc_code": ["5812", "5411"],
                "modality_id": ["VISA", "VISA"],
                "active": [True, False],
            }
        ),
        "cnae_products": pl.DataFrame(
            {
                "cnae_code": ["5611", "5611", "5611201", "4711"],
                "product_id": ["VR", "GF", "VR", "VA"],
                "active": [True, True, True, False],
            }
        ),
    }


# --- status ---------------------------------------------------------------


def test_card_status(tx, data):
    assert validate_card_status(tx, data["cards"]) == PASS
    assert validate_card_status(tx | {"card_id": "card_blocked"}, data["cards"]) == declined("14")
    assert validate_card_status(tx | {"card_id": "nope"}, data["cards"]) == declined("92")


def test_cardholder_status(tx, data):
    assert validate_cardholder_status(tx, data["cards"], data["cardholders"]) == PASS
    off = tx | {"card_id": "card_blocked"}
    assert validate_cardholder_status(off, data["cards"], data["cardholders"]) == declined("17")


def test_establishment_status(tx, data):
    assert validate_establishment_status(tx, data["establishments"]) == PASS
    closed = tx | {"establishment_id": "est_closed"}
    assert validate_establishment_status(closed, data["establishments"]) == declined("21")
    missing = tx | {"establishment_id": "nope"}
    assert validate_establishment_status(missing, data["establishments"]) == declined("97")


def test_terminal_status(tx, data):
    assert validate_terminal_status(tx, data["terminals"]) == PASS
    tef = tx | {"terminal_id": "term_tef"}
    assert validate_terminal_status(tef, data["terminals"]) == declined("22")


def test_card_product_status(tx, data):
    assert validate_card_product_status(tx, data["card_products"]) == PASS
    suspended = tx | {"card_id": "card_own", "product_id": "GF"}
    assert validate_card_product_status(suspended, data["card_products"]) == declined("23")
    missing = tx | {"product_id": "VA"}
    assert validate_card_product_status(missing, data["card_products"]) == declined("93")


def test_product_active(tx, data):
    assert validate_product_active(tx, data["products"]) == PASS
    assert validate_product_active(tx | {"product_id": "GF"}, data["products"]) == declined("24")


def test_modality_active(tx, data):
    assert validate_modality_active(tx, data["cards"], data["modalities"]) == PASS
    own = tx | {"card_id": "card_own"}
    assert validate_modality_active(own, data["cards"], data["modalities"]) == PASS
    elo = tx | {"card_id": "card_blocked"}
    assert validate_modality_active(elo, data["cards"], data["modalities"]) == declined("25")


def test_acquirer_active(tx, data):
    assert validate_acquirer_active(tx, data["terminals"], data["acquirers"]) == PASS
    off = tx | {"terminal_id": "term_tef"}
    assert validate_acquirer_active(off, data["terminals"], data["acquirers"]) == declined("26")


# --- temporal -------------------------------------------------------------


def test_card_expiration(tx, data):
    assert validate_card_expiration(tx, data["cards"]) == PASS
    late = tx | {"date": datetime(2028, 2, 1)}
    assert validate_card_expiration(late, data["cards"]) == declined("54")


def test_cardholder_admission(tx, data):
    assert validate_cardholder_admission(tx, data["cards"], data["cardholders"]) == PASS
    early = tx | {"card_id": "card_blocked"}
    assert validate_cardholder_admission(early, data["cards"], data["cardholders"]) == declined(
        "56"
    )


def test_establishment_accreditation(tx, data):
    assert validate_establishment_accreditation(tx, data["establishments"]) == PASS
    early = tx | {"establishment_id": "est_closed"}
    assert validate_establishment_accreditation(early, data["establishments"]) == declined("57")


def test_terminal_installation(tx, data):
    assert validate_terminal_installation(tx, data["terminals"]) == PASS
    early = tx | {"terminal_id": "term_tef"}
    assert validate_terminal_installation(early, data["terminals"]) == declined("58")


# --- business rules -------------------------------------------------------


def test_mcc_modality(tx, data):
    args = data["cards"], data["establishments"], data["mcc_modalities"]
    assert validate_mcc_modality(tx, *args) == PASS
    # proprietary-network card: not an MCC decision
    assert validate_mcc_modality(tx | {"card_id": "card_own"}, *args) == PASS
    inactive_rule = tx | {"establishment_id": "est_closed"}
    assert validate_mcc_modality(inactive_rule, *args) == declined("29")
    no_rule = tx | {"card_id": "card_blocked"}  # ELO × 5812
    assert validate_mcc_modality(no_rule, *args) == declined("27")


def test_cnae_product(tx, data):
    args = data["cards"], data["establishments"], data["cnae_products"]
    own = tx | {"card_id": "card_own"}
    assert validate_cnae_product(own, *args) == PASS
    # branded card: not a CNAE decision
    assert validate_cnae_product(tx | {"product_id": "VA"}, *args) == PASS
    # 5611 accepts GF, but the more specific 5611201 only lists VR
    assert validate_cnae_product(own | {"product_id": "GF"}, *args) == declined("28")
    inactive_rule = own | {"establishment_id": "est_closed", "product_id": "VA"}
    assert validate_cnae_product(inactive_rule, *args) == declined("30")


# --- balance and limits ---------------------------------------------------


def test_current_balance(tx, data):
    assert validate_current_balance(tx, data["card_products"]) == PASS
    big = tx | {"amount": 501.0}
    assert validate_current_balance(big, data["card_products"]) == declined("51")


def test_daily_limit(tx, data):
    assert validate_daily_limit(tx, data["card_products"], daily_usage=50) == PASS
    assert validate_daily_limit(tx, data["card_products"], daily_usage=51) == declined("61")
    # limit 0 = no limit
    own = tx | {"card_id": "card_own"}
    assert validate_daily_limit(own, data["card_products"], daily_usage=10_000) == PASS


def test_monthly_limit(tx, data):
    assert validate_monthly_limit(tx, data["card_products"], monthly_usage=950) == PASS
    assert validate_monthly_limit(tx, data["card_products"], monthly_usage=951) == declined("62")


# --- infrastructure -------------------------------------------------------


def test_capture_type_support(tx, data):
    assert validate_capture_type_support(tx, data["terminals"]) == PASS
    tef = tx | {"terminal_id": "term_tef"}
    assert validate_capture_type_support(tef, data["terminals"]) == declined("32")
    assert validate_capture_type_support(tef | {"capture_type": "chip"}, data["terminals"]) == PASS
    missing = tx | {"terminal_id": "nope"}
    assert validate_capture_type_support(missing, data["terminals"]) == declined("98")


def test_unknown_status(tx, data):
    odd = data["cards"].with_columns(status=pl.lit("lost"))
    assert validate_card_status(tx, odd) == declined("96")


def test_codes_are_documented():
    """Every code a validator can return has a description in response_codes."""
    from src.utils.read_yamls import load_pre_populated_data, load_validation_rules

    def codes(node):
        if isinstance(node, dict):
            for value in node.values():
                yield from codes(value)
        elif isinstance(node, str) and len(node) == 2 and node.isdigit():
            yield node

    rules = load_validation_rules()
    sections = [*rules["validation_order"], "not_found", "unknown_status"]
    used = {code for section in sections for code in codes(rules[section])}
    described = set(load_pre_populated_data()["response_codes"])
    assert used <= described, used - described
