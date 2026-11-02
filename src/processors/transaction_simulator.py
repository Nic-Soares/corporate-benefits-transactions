"""The issuer over time.

Attempts, monthly credits and reversals run in time order. Each attempt goes
through the validators in `validation_rules.yaml → validation_order`; the
first failure declines it with its ISO code and reason, an approval debits the
routed card wallet. The daily amount, daily count and monthly amount of each
wallet are tracked for the limits.
"""

import heapq
import random
import string
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import polars as pl

from src.data_generators.providers import fake
from src.processors.balance import HISTORY_SCHEMA, credit, debit, reverse
from src.processors.disputes import mark_disputes
from src.utils.read_yamls import load_simulation_config
from src.validators import balance_and_limits_validations as balance
from src.validators import business_rules_validators as business
from src.validators import infrastructure_validations as infrastructure
from src.validators import security_validators as security
from src.validators import status_validators as status
from src.validators import temporal_validators as temporal
from src.validators._common import RULES, Table

SIMULATION = load_simulation_config()["simulation"]
CREDIT_DAY: int = fake.SETTINGS["benefit_credit_day"]
CREDIT_HOUR = 6
APPROVED = "00"

# Tables the simulator reads (columns of the OLTP schema)
TABLES = [
    "cards",
    "cardholders",
    "card_wallets",
    "establishments",
    "terminals",
    "wallets",
    "transaction_modalities",
    "acquirers",
    "cnae_wallets",
    "mcc_wallets",
    "mcc_modalities",
]


@dataclass
class SimulationResult:
    transactions: pl.DataFrame
    balance_history: pl.DataFrame
    card_wallets: pl.DataFrame  # with the balances at the end


def credit_moments(start: datetime, end: datetime) -> list[datetime]:
    """The credit day of every month in [start, end), at 06:00."""
    moments, year, month = [], start.year, start.month
    while (moment := datetime(year, month, CREDIT_DAY, CREDIT_HOUR)) < end:
        if moment >= start:
            moments.append(moment)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return moments


def authorization_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class TransactionSimulator:
    def __init__(self, tables: dict[str, pl.DataFrame]) -> None:
        self.t = tables
        # The balances move in place (`Table`); every lookup is indexed
        self.card_wallets = Table(tables["card_wallets"])
        self.history: list[dict[str, Any]] = []
        self.daily_amount: dict[tuple[str, date], float] = defaultdict(float)
        self.daily_count: dict[tuple[str, date], int] = defaultdict(int)
        self.monthly_amount: dict[tuple[str, int, int], float] = defaultdict(float)
        # (card, option or kind of place) declined for lack of balance since the last credit
        self.out_of_balance: set[tuple[str, str]] = set()
        self.category_of = dict(tables["establishments"].select("id", "category").iter_rows())
        self.checks = self._checks()

    def _checks(self) -> dict[str, list[Callable[[dict], dict]]]:
        """The validators of each group, bound to the tables."""
        t = self
        return {
            "status_validations": [
                lambda tx: status.validate_card_status(tx, t.t["cards"]),
                lambda tx: status.validate_cardholder_status(tx, t.t["cards"], t.t["cardholders"]),
                lambda tx: status.validate_establishment_status(tx, t.t["establishments"]),
                lambda tx: status.validate_terminal_status(tx, t.t["terminals"]),
                lambda tx: status.validate_modality_active(
                    tx, t.t["cards"], t.t["transaction_modalities"]
                ),
                lambda tx: status.validate_acquirer_active(tx, t.t["terminals"], t.t["acquirers"]),
            ],
            "temporal_validations": [
                lambda tx: temporal.validate_card_expiration(tx, t.t["cards"]),
                lambda tx: temporal.validate_cardholder_admission(
                    tx, t.t["cards"], t.t["cardholders"]
                ),
                lambda tx: temporal.validate_establishment_accreditation(tx, t.t["establishments"]),
                lambda tx: temporal.validate_terminal_installation(tx, t.t["terminals"]),
            ],
            "security_validations": [security.validate_pin],
            "business_rules_validations": [
                lambda tx: business.validate_mcc_brand(
                    tx, t.t["cards"], t.t["establishments"], t.t["mcc_modalities"]
                ),
                lambda tx: business.route_wallet(
                    tx,
                    t.t["cards"],
                    t.t["establishments"],
                    t.card_wallets,
                    t.t["wallets"],
                    t.t["cnae_wallets"],
                    t.t["mcc_wallets"],
                ),
            ],
            "balance_and_limits_validations": [
                lambda tx: balance.validate_current_balance(tx, t.card_wallets),
                lambda tx: balance.validate_daily_limit(
                    tx, t.card_wallets, t.daily_amount[t._day(tx)]
                ),
                lambda tx: balance.validate_monthly_limit(
                    tx, t.card_wallets, t.monthly_amount[t._month(tx)]
                ),
                lambda tx: balance.validate_daily_count(
                    tx, t.card_wallets, t.daily_count[t._day(tx)]
                ),
            ],
            "infrastructure_validations": [
                lambda tx: infrastructure.validate_capture_type_support(tx, t.t["terminals"])
            ],
        }

    @staticmethod
    def _day(tx: dict) -> tuple[str, date]:
        return tx["card_wallet_id"], tx["date"].date()

    @staticmethod
    def _month(tx: dict) -> tuple[str, int, int]:
        return tx["card_wallet_id"], tx["date"].year, tx["date"].month

    def authorize(self, tx: dict[str, Any]) -> dict[str, Any]:
        """Answer one attempt: the first failing validator declines it."""
        for group in RULES["validation_order"]:
            for check in self.checks[group]:
                result = check(tx)
                if "card_wallet_id" in result:  # the routing chose the wallet
                    tx["card_wallet_id"] = result["card_wallet_id"]
                if not result["passed"]:
                    return tx | {
                        "response_code": result["error_code"],
                        "decline_reason": result["reason"],
                    }

        tx = tx | {"response_code": APPROVED, "authorization_code": authorization_code()}
        self.history.append(debit(self.card_wallets, tx))
        self.daily_amount[self._day(tx)] += tx["amount"]
        self.daily_count[self._day(tx)] += 1
        self.monthly_amount[self._month(tx)] += tx["amount"]
        return tx

    def credit(self, moment: datetime) -> None:
        """The monthly credit, to every wallet still in use: not cancelled, on a card
        not cancelled, of an active cardholder (the employer stops crediting the
        others), already activated."""
        cards = self.t["cards"].join(
            self.t["cardholders"].select(pl.col("id").alias("cardholder_id"), holder="status"),
            on="cardholder_id",
        )
        in_use = cards.filter(pl.col("status") != "cancelled", pl.col("holder") == "active").select(
            pl.col("id").alias("card_id")
        )
        eligible = (
            self.t["card_wallets"]
            .join(in_use, on="card_id")
            .filter(pl.col("status") != "cancelled", pl.col("activation_date") <= moment.date())
        )
        self.history += [credit(self.card_wallets, id_, moment) for id_ in eligible["id"]]
        self.out_of_balance.clear()

    def _intent(self, tx: dict[str, Any]) -> tuple[str, str]:
        """What the cardholder was spending: the option picked on the terminal, or on a
        brand card the kind of place (the issuer routes there by MCC)."""
        return tx["card_id"], tx["wallet_option"] or self.category_of[tx["establishment_id"]]

    def reverse(self, original: dict[str, Any], moment: datetime) -> dict[str, Any]:
        """A reversal of an approved purchase: its own row, pointing to the original."""
        reversal = original | {
            "id": fake.new_id("tx"),
            "transaction_type": "reversal",
            "date": moment,
            "pin_status": "not_required",
            "response_code": APPROVED,
            "decline_reason": None,
            "nsu": f"{random.randrange(10**12):012d}",
            "authorization_code": authorization_code(),
            "related_transaction_id": original["id"],
            "is_fraud": False,
            "fraud_scenario": None,
            "disputed": False,
        }
        self.history.append(reverse(self.card_wallets, reversal))
        return reversal

    def run(
        self, attempts: list[dict[str, Any]], start: datetime, end: datetime
    ) -> SimulationResult:
        """Credits, attempts and reversals in time order within [start, end)."""
        events: list[tuple[datetime, int, str, Any]] = []
        for moment in credit_moments(start, end):
            events.append((moment, 0, "credit", None))
        for seq, tx in enumerate(sorted(attempts, key=lambda tx: tx["date"]), start=1):
            events.append((tx["date"], seq, "attempt", tx))
        heapq.heapify(events)
        seq = len(events)

        delay = SIMULATION["reversal_delay_minutes"]
        answered = []
        while events:
            moment, _, kind, payload = heapq.heappop(events)
            if kind == "credit":
                self.credit(moment)
                continue
            if kind == "reversal":
                answered.append(self.reverse(payload, moment))
                continue
            if (
                not payload["is_fraud"]
                and self._intent(payload) in self.out_of_balance
                and random.random() < SIMULATION["give_up_after_insufficient_balance"]
            ):
                continue  # the cardholder doesn't try: the balance is gone (a fraudster does)
            tx = self.authorize(payload)
            answered.append(tx)
            if tx["decline_reason"] == "insufficient_balance" and not tx["is_fraud"]:
                self.out_of_balance.add(self._intent(tx))
            if (
                tx["response_code"] == APPROVED
                and tx["transaction_type"] == "purchase"
                and not tx["is_fraud"]
                and random.random() < SIMULATION["reversal_ratio"]
            ):
                when = moment + timedelta(minutes=random.randint(delay["min"], delay["max"]))
                if when < end:
                    seq += 1
                    heapq.heappush(events, (when, seq, "reversal", tx))

        history = pl.DataFrame(self.history, schema=HISTORY_SCHEMA)
        return SimulationResult(
            transactions=mark_disputes(pl.DataFrame(answered, infer_schema_length=None)),
            balance_history=history.sort("operation_date"),
            card_wallets=self.card_wallets.to_frame(),
        )
