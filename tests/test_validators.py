from datetime import date, datetime, timedelta

import polars as pl
import pytest

from src.simulation.balance import credit, debit
from src.table import Table, find_all, find_one
from src.validators.balance_validators import (
    validate_current_balance,
    validate_daily_count,
    validate_daily_limit,
    validate_monthly_limit,
)
from src.validators.business_rules_validators import route_wallet, validate_mcc_brand
from src.validators.infrastructure_validators import validate_capture_type_support
from src.validators.security_validators import validate_pin
from src.validators.status_validators import (
    validate_acquirer_active,
    validate_card_status,
    validate_cardholder_status,
    validate_establishment_status,
    validate_modality_active,
    validate_terminal_status,
)
from src.validators.temporal_validators import (
    validate_card_expiration,
    validate_cardholder_admission,
    validate_establishment_accreditation,
    validate_terminal_installation,
)

PASS = {"passed": True, "error_code": None, "reason": None}


def declined(code, reason):
    return {"passed": False, "error_code": code, "reason": reason}


@pytest.fixture
def tx():
    """A proprietary-network purchase that passes every validation against `data`.

    The cardholder picked Meal on the terminal; `card_wallet_id` is what the
    issuer routed it to.
    """
    return {
        "id": "tx_1",
        "card_id": "card_own",
        "card_wallet_id": "cw_1",  # MEAL
        "transaction_type": "purchase",
        "wallet_option": "MEAL",
        "establishment_id": "est_restaurant",
        "terminal_id": "term_pos",
        "amount": 50.0,
        "date": datetime(2026, 6, 15, 12, 30),
        "capture_type": "CONTACTLESS",
        "pin_status": "not_required",
    }


@pytest.fixture
def brand_tx(tx):
    """The same purchase on a brand card: the issuer still has to route the wallet."""
    return tx | {"card_id": "card_brand", "card_wallet_id": None, "wallet_option": None}


@pytest.fixture
def data():
    return {
        "cards": pl.DataFrame(
            {
                "id": ["card_own", "card_brand", "card_blocked", "card_meal"],
                "cardholder_id": ["holder_1", "holder_1", "holder_off", "holder_1"],
                "program_id": ["MULTI_3P", "MULTI_4P", "MULTI_4P", "MEAL"],
                "modality_id": ["OWN", "VISA", "ELO", "OWN"],
                "expiration_date": [date(2028, 1, 31)] * 4,
                "status": ["active", "active", "blocked", "active"],
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
                "id": ["est_restaurant", "est_closed", "est_pharmacy", "est_atm"],
                "main_cnae": ["5611201", "4711302", "4771701", "6422100"],
                "mcc_code": ["5812", "5411", "5912", "6011"],
                "status": ["active", "terminated", "active", "active"],
                "accreditation_date": [date(2015, 5, 1), date(2027, 1, 1)] + [date(2015, 5, 1)] * 2,
            }
        ),
        "terminals": pl.DataFrame(
            {
                "id": ["term_pos", "term_tef"],
                "acquirer_id": ["CIE", "OFF"],
                "type": ["POS", "TEF"],
                "status": ["active", "maintenance"],
                "installation_date": [date(2022, 1, 1), date(2027, 1, 1)],
            }
        ),
        "card_wallets": pl.DataFrame(
            {
                "id": ["cw_1", "cw_2", "cw_3", "cw_4", "cw_5", "cw_6", "cw_7", "cw_8", "cw_9"],
                "card_id": ["card_own"] * 3 + ["card_brand"] * 4 + ["card_own", "card_meal"],
                "wallet_id": [
                    *["MEAL", "FOOD", "GIFT"],
                    *["MEAL", "FOOD", "HEALTH", "GIFT"],
                    *["PREMIUM", "MEAL"],
                ],
                "current_balance": [500.0, 500.0, 500.0, 20.0, 500.0, 300.0, 1000.0, 500.0, 80.0],
                "monthly_credit": [800.0] * 9,
                "daily_limit": [100.0] + [0.0] * 8,
                "monthly_limit": [1000.0] + [0.0] * 8,
                "daily_count_limit": [3] + [0] * 8,
                "status": ["active", "active", "suspended"] + ["active"] * 6,
            }
        ),
        "wallets": pl.DataFrame(
            {
                "id": ["MEAL", "FOOD", "HEALTH", "GIFT", "PREMIUM"],
                "active": [True, True, True, True, False],
            }
        ),
        "modalities": pl.DataFrame({"id": ["OWN", "VISA", "ELO"], "active": [True, True, False]}),
        "acquirers": pl.DataFrame({"id": ["CIE", "OFF"], "active": [True, False]}),
        "mcc_modalities": pl.DataFrame(
            {
                "mcc_code": ["5812", "5411", "5912"],
                "modality_id": ["VISA", "VISA", "VISA"],
                "active": [True, False, True],
            }
        ),
        "cnae_wallets": pl.DataFrame(
            {
                "cnae_code": ["5611", "5611", "5611201", "4711"],
                "wallet_id": ["MEAL", "GIFT", "MEAL", "FOOD"],
                "active": [True, True, True, False],
            }
        ),
        "mcc_wallets": pl.DataFrame(
            {"mcc_code": ["5812", "5411", "5912"], "wallet_id": ["MEAL", "FOOD", "HEALTH"]}
        ),
    }


# --- status ---------------------------------------------------------------


def test_card_status(tx, data):
    assert validate_card_status(tx, data["cards"]) == PASS
    blocked = tx | {"card_id": "card_blocked"}
    assert validate_card_status(blocked, data["cards"]) == declined("62", "card_blocked")
    missing = tx | {"card_id": "nope"}
    assert validate_card_status(missing, data["cards"]) == declined("14", "card_not_found")


def test_status_begins_on_its_day(tx, data):
    """Before its status began the card was active; without the day, the status holds."""
    blocked = tx | {"card_id": "card_blocked"}
    since = tx["date"].date()
    cards = data["cards"].with_columns(status_since=pl.lit(since + timedelta(days=1)))
    assert validate_card_status(blocked, cards) == PASS
    cards = data["cards"].with_columns(status_since=pl.lit(since))
    assert validate_card_status(blocked, cards) == declined("62", "card_blocked")


def test_cardholder_status(tx, data):
    assert validate_cardholder_status(tx, data["cards"], data["cardholders"]) == PASS
    off = tx | {"card_id": "card_blocked"}
    assert validate_cardholder_status(off, data["cards"], data["cardholders"]) == declined(
        "62", "cardholder_terminated"
    )


def test_establishment_status(tx, data):
    assert validate_establishment_status(tx, data["establishments"]) == PASS
    closed = tx | {"establishment_id": "est_closed"}
    assert validate_establishment_status(closed, data["establishments"]) == declined(
        "03", "establishment_terminated"
    )
    missing = tx | {"establishment_id": "nope"}
    assert validate_establishment_status(missing, data["establishments"]) == declined(
        "03", "establishment_not_found"
    )


def test_terminal_status(tx, data):
    assert validate_terminal_status(tx, data["terminals"]) == PASS
    tef = tx | {"terminal_id": "term_tef"}
    assert validate_terminal_status(tef, data["terminals"]) == declined(
        "58", "terminal_maintenance"
    )


def test_modality_active(tx, data, brand_tx):
    assert validate_modality_active(tx, data["cards"], data["modalities"]) == PASS
    assert validate_modality_active(brand_tx, data["cards"], data["modalities"]) == PASS
    elo = tx | {"card_id": "card_blocked"}
    assert validate_modality_active(elo, data["cards"], data["modalities"]) == declined(
        "57", "modality_disabled"
    )


def test_acquirer_active(tx, data):
    assert validate_acquirer_active(tx, data["terminals"], data["acquirers"]) == PASS
    off = tx | {"terminal_id": "term_tef"}
    assert validate_acquirer_active(off, data["terminals"], data["acquirers"]) == declined(
        "58", "acquirer_disabled"
    )


def test_unknown_status(tx, data):
    odd = data["cards"].with_columns(status=pl.lit("lost"))
    assert validate_card_status(tx, odd) == declined("96", "unknown_card_status")


# --- temporal -------------------------------------------------------------


def test_card_expiration(tx, data):
    assert validate_card_expiration(tx, data["cards"]) == PASS
    late = tx | {"date": datetime(2028, 2, 1)}
    assert validate_card_expiration(late, data["cards"]) == declined("54", "card_expired")


def test_cardholder_admission(tx, data):
    assert validate_cardholder_admission(tx, data["cards"], data["cardholders"]) == PASS
    early = tx | {"card_id": "card_blocked"}
    assert validate_cardholder_admission(early, data["cards"], data["cardholders"]) == declined(
        "62", "before_admission"
    )


def test_establishment_accreditation(tx, data):
    assert validate_establishment_accreditation(tx, data["establishments"]) == PASS
    early = tx | {"establishment_id": "est_closed"}
    assert validate_establishment_accreditation(early, data["establishments"]) == declined(
        "03", "before_accreditation"
    )


def test_terminal_installation(tx, data):
    assert validate_terminal_installation(tx, data["terminals"]) == PASS
    early = tx | {"terminal_id": "term_tef"}
    assert validate_terminal_installation(early, data["terminals"]) == declined(
        "58", "before_installation"
    )


# --- security -------------------------------------------------------------


def test_pin(tx):
    assert validate_pin(tx) == PASS
    assert validate_pin(tx | {"capture_type": "CHIP", "pin_status": "ok"}) == PASS
    wrong = tx | {"capture_type": "CHIP", "pin_status": "wrong"}
    assert validate_pin(wrong) == declined("55", "wrong_pin")


# --- business rules -------------------------------------------------------


def test_mcc_brand(tx, data, brand_tx):
    args = data["cards"], data["establishments"], data["mcc_modalities"]
    assert validate_mcc_brand(brand_tx, *args) == PASS
    # proprietary network: not an MCC decision
    assert validate_mcc_brand(tx, *args) == PASS
    inactive_rule = brand_tx | {"establishment_id": "est_closed"}
    assert validate_mcc_brand(inactive_rule, *args) == declined("57", "mcc_rule_inactive")
    no_rule = brand_tx | {"card_id": "card_blocked"}  # ELO × 5812
    assert validate_mcc_brand(no_rule, *args) == declined("57", "mcc_not_accepted_by_brand")


@pytest.fixture
def route(data):
    def run(transaction):
        return route_wallet(
            transaction,
            data["cards"],
            data["establishments"],
            data["card_wallets"],
            data["wallets"],
            data["cnae_wallets"],
            data["mcc_wallets"],
        )

    return run


def test_route_proprietary_option(tx, route):
    # Meal picked at a restaurant: the MEAL wallet
    assert route(tx) == PASS | {"card_wallet_id": "cw_1"}
    # Food picked at a restaurant: the card holds it, the CNAE doesn't take it
    food = tx | {"wallet_option": "FOOD"}
    assert route(food) == declined("57", "wallet_not_accepted_at_cnae")
    # Others: GIFT is suspended and PREMIUM disabled
    others = tx | {"wallet_option": "OTHERS"}
    assert route(others) == declined("57", "card_wallet_inactive")
    # A Meal card asked for Food
    meal_card = tx | {"card_id": "card_meal", "wallet_option": "FOOD"}
    assert route(meal_card) == declined("57", "wallet_not_on_card")
    # The rule for supermarkets (4711) is inactive
    closed = tx | {"establishment_id": "est_closed", "wallet_option": "FOOD"}
    assert route(closed) == declined("57", "wallet_not_accepted_at_cnae")
    # Accepted, but not enough balance: the wallet it would have charged comes back
    short = declined("51", "insufficient_balance") | {"card_wallet_id": "cw_1"}
    assert route(tx | {"amount": 600.0}) == short


def test_route_brand_by_mcc(brand_tx, route):
    # restaurant MCC: MEAL (cw_4) first...
    assert route(brand_tx | {"amount": 10.0}) == PASS | {"card_wallet_id": "cw_4"}
    # ...but MEAL has 20.00, so 50.00 falls through to GIFT, the open wallet
    assert route(brand_tx) == PASS | {"card_wallet_id": "cw_7"}
    # pharmacy MCC goes to HEALTH (FOOD isn't accepted there)
    pharmacy = brand_tx | {"establishment_id": "est_pharmacy"}
    assert route(pharmacy) == PASS | {"card_wallet_id": "cw_6"}
    # candidates exist, none with enough balance: the first in priority comes back
    short = declined("51", "insufficient_balance") | {"card_wallet_id": "cw_4"}
    assert route(brand_tx | {"amount": 5000.0}) == short
    # the card holds no wallet in the priority list
    empty = brand_tx | {"card_id": "card_blocked"}
    assert route(empty) == declined("57", "wallet_not_on_card")


def test_route_withdrawal(tx, brand_tx, route):
    cash = {"transaction_type": "withdrawal", "establishment_id": "est_atm", "amount": 200.0}
    # brand cards withdraw from GIFT only
    assert route(brand_tx | cash) == PASS | {"card_wallet_id": "cw_7"}
    # no withdrawal on the proprietary network
    assert route(tx | cash) == declined("57", "withdrawal_not_allowed")


# --- balance and limits ---------------------------------------------------


def test_current_balance(tx, data):
    assert validate_current_balance(tx, data["card_wallets"]) == PASS
    big = tx | {"amount": 501.0}
    assert validate_current_balance(big, data["card_wallets"]) == declined(
        "51", "insufficient_balance"
    )


def test_daily_limit(tx, data):
    assert validate_daily_limit(tx, data["card_wallets"], daily_usage=50) == PASS
    assert validate_daily_limit(tx, data["card_wallets"], daily_usage=51) == declined(
        "61", "daily_limit_exceeded"
    )
    # limit 0 = no limit
    food = tx | {"card_wallet_id": "cw_2"}
    assert validate_daily_limit(food, data["card_wallets"], daily_usage=10_000) == PASS


def test_monthly_limit(tx, data):
    assert validate_monthly_limit(tx, data["card_wallets"], monthly_usage=950) == PASS
    assert validate_monthly_limit(tx, data["card_wallets"], monthly_usage=951) == declined(
        "61", "monthly_limit_exceeded"
    )


def test_daily_count(tx, data):
    assert validate_daily_count(tx, data["card_wallets"], daily_count=2) == PASS
    assert validate_daily_count(tx, data["card_wallets"], daily_count=3) == declined(
        "65", "daily_count_exceeded"
    )
    # limit 0 = no limit
    food = tx | {"card_wallet_id": "cw_2"}
    assert validate_daily_count(food, data["card_wallets"], daily_count=100) == PASS


def test_debit(tx, data):
    card_wallets = Table(data["card_wallets"])
    history = debit(card_wallets, tx)

    assert find_one(card_wallets, id="cw_1")["current_balance"] == 450.0
    assert history["card_wallet_id"] == "cw_1"
    assert history["operation_type"] == "purchase"
    assert (history["previous_balance"], history["posterior_balance"]) == (500.0, 450.0)
    # only that wallet moved
    after = card_wallets.to_frame()
    others = after.filter(pl.col("id") != "cw_1")["current_balance"]
    assert (
        others.to_list()
        == data["card_wallets"].filter(pl.col("id") != "cw_1")["current_balance"].to_list()
    )


def test_credit(data):
    moment = datetime(2026, 7, 1, 6, 0)
    card_wallets = Table(data["card_wallets"])
    history = credit(card_wallets, "cw_9", moment)

    assert find_one(card_wallets, id="cw_9")["current_balance"] == 880.0
    assert history["operation_type"] == "credit"
    assert history["transaction_id"] is None
    assert (history["previous_balance"], history["posterior_balance"]) == (80.0, 880.0)
    assert history["operation_date"] == moment


def test_table_lookups(data):
    """A Table finds the same rows as a filter, and sees a value changed in place."""
    card_wallets = Table(data["card_wallets"])
    rows = find_all(card_wallets, card_id="card_brand")
    assert rows == data["card_wallets"].filter(card_id="card_brand").to_dicts()
    assert find_one(card_wallets, id="missing") is None
    rows[0]["current_balance"] = 1.0
    assert find_one(card_wallets, id=rows[0]["id"])["current_balance"] == 1.0
    assert card_wallets.to_frame().schema == data["card_wallets"].schema


# --- infrastructure -------------------------------------------------------


def test_capture_type_support(tx, data):
    assert validate_capture_type_support(tx, data["terminals"]) == PASS
    tef = tx | {"terminal_id": "term_tef"}
    assert validate_capture_type_support(tef, data["terminals"]) == declined(
        "58", "capture_not_supported"
    )
    assert validate_capture_type_support(tef | {"capture_type": "CHIP"}, data["terminals"]) == PASS
    missing = tx | {"terminal_id": "nope"}
    assert validate_capture_type_support(missing, data["terminals"]) == declined(
        "58", "terminal_not_found"
    )


def test_codes_are_documented():
    """Every code a validator can return is an ISO 8583 code described in response_codes."""
    from src.config import load_authorization, load_reference

    def codes(node):
        if isinstance(node, dict):
            for value in node.values():
                yield from codes(value)
        elif isinstance(node, str) and len(node) == 2 and node.isdigit():
            yield node

    rules = load_authorization()
    sections = [*rules["validation_order"], "not_found", "unknown_status"]
    used = {code for section in sections for code in codes(rules[section])}
    described = set(load_reference()["response_codes"])
    assert used <= described, used - described


def test_route_skips_wallets_not_activated(tx, route, data):
    """A wallet activated after the attempt isn't charged: the card holds no usable one."""
    later = data["card_wallets"].with_columns(activation_date=pl.lit(date(2026, 7, 1)))
    result = route_wallet(
        tx,
        data["cards"],
        data["establishments"],
        later,
        data["wallets"],
        data["cnae_wallets"],
        data["mcc_wallets"],
    )
    assert result == declined("57", "card_wallet_inactive")
    earlier = later.with_columns(activation_date=pl.lit(date(2026, 1, 1)))
    assert route_wallet(
        tx,
        data["cards"],
        data["establishments"],
        earlier,
        data["wallets"],
        data["cnae_wallets"],
        data["mcc_wallets"],
    ) == PASS | {"card_wallet_id": "cw_1"}
