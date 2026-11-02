"""The issuer over time.

Attempts, monthly credits and reversals run in time order. A wallet activated
in the window starts empty and gets its first credit, pro rata to the days
left in the month, on the activation day. Some employers add a one-off
year-end credit (`seasons.year_end_credit`). Each attempt goes
through the validators in `validation_rules.yaml → validation_order`; the
first failure declines it with its ISO code and reason, an approval debits the
routed card wallet. The daily amount, daily count and monthly amount of each
wallet are tracked for the limits.
"""

import calendar
import heapq
import random
import string
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

import polars as pl

from src.config import load_simulation_config
from src.entities import fake
from src.simulation import seasons
from src.simulation.balance import HISTORY_SCHEMA, credit, debit, reverse
from src.simulation.disputes import mark_disputes
from src.table import Table, find_one
from src.validators import balance_validators as balance
from src.validators import business_rules_validators as business
from src.validators import infrastructure_validators as infrastructure
from src.validators import security_validators as security
from src.validators import status_validators as status
from src.validators import temporal_validators as temporal
from src.validators._common import RULES

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
    card_wallets: pl.DataFrame | None = None  # with the balances at the end (`run`)


def _status_on(day: pl.Expr, status: str = "status", since: str = "status_since") -> pl.Expr:
    """The status on `day`: active before the current status began."""
    return pl.when(pl.col(since) > day).then(pl.lit("active")).otherwise(pl.col(status))


def first_credit(monthly_credit: float, day: date) -> float:
    """The month's credit pro rata to the days left from `day` on."""
    days = calendar.monthrange(day.year, day.month)[1]
    return round(monthly_credit * (days - day.day + 1) / days, 2)


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
        # The validators get Tables: no DataFrame-to-Table lookup per check
        self.lookup = {name: Table(df) for name, df in tables.items()}
        self.lookup["card_wallets"] = self.card_wallets
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
        t, db = self, self.lookup
        return {
            "status_validations": [
                lambda tx: status.validate_card_status(tx, db["cards"]),
                lambda tx: status.validate_cardholder_status(tx, db["cards"], db["cardholders"]),
                lambda tx: status.validate_establishment_status(tx, db["establishments"]),
                lambda tx: status.validate_terminal_status(tx, db["terminals"]),
                lambda tx: status.validate_modality_active(
                    tx, db["cards"], db["transaction_modalities"]
                ),
                lambda tx: status.validate_acquirer_active(tx, db["terminals"], db["acquirers"]),
            ],
            "temporal_validations": [
                lambda tx: temporal.validate_card_expiration(tx, db["cards"]),
                lambda tx: temporal.validate_cardholder_admission(
                    tx, db["cards"], db["cardholders"]
                ),
                lambda tx: temporal.validate_establishment_accreditation(tx, db["establishments"]),
                lambda tx: temporal.validate_terminal_installation(tx, db["terminals"]),
            ],
            "security_validations": [security.validate_pin],
            "business_rules_validations": [
                lambda tx: business.validate_mcc_brand(
                    tx, db["cards"], db["establishments"], db["mcc_modalities"]
                ),
                lambda tx: business.route_wallet(
                    tx,
                    db["cards"],
                    db["establishments"],
                    t.card_wallets,
                    db["wallets"],
                    db["cnae_wallets"],
                    db["mcc_wallets"],
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
                lambda tx: infrastructure.validate_capture_type_support(tx, db["terminals"])
            ],
        }

    @staticmethod
    def _day(tx: dict) -> tuple[str, date]:
        return tx["card_wallet_id"], tx["date"].date()

    @staticmethod
    def _month(tx: dict) -> tuple[str, int, int]:
        return tx["card_wallet_id"], tx["date"].year, tx["date"].month

    def authorize(self, tx: dict[str, Any]) -> dict[str, Any]:
        """Answer one attempt, in place: the first failing validator declines it."""
        for group in RULES["validation_order"]:
            for check in self.checks[group]:
                result = check(tx)
                if "card_wallet_id" in result:  # the routing chose the wallet
                    tx["card_wallet_id"] = result["card_wallet_id"]
                if not result["passed"]:
                    tx["response_code"] = result["error_code"]
                    tx["decline_reason"] = result["reason"]
                    return tx

        tx["response_code"] = APPROVED
        tx["authorization_code"] = authorization_code()
        self.history.append(debit(self.card_wallets, tx))
        self.daily_amount[self._day(tx)] += tx["amount"]
        self.daily_count[self._day(tx)] += 1
        self.monthly_amount[self._month(tx)] += tx["amount"]
        return tx

    def credit(self, moment: datetime) -> None:
        """The monthly credit, to every wallet in use that day (`_in_use`)."""
        eligible = self._in_use(pl.lit(moment.date()))
        self.history += [credit(self.card_wallets, id_, moment) for id_ in eligible["id"]]
        self.out_of_balance.clear()

    def year_end_credit(self, moment: datetime) -> None:
        """The year-end credit, from the companies that give it that year, to
        their wallets of its kind in use that day."""
        eligible = self._in_use(pl.lit(moment.date())).filter(
            wallet_id=seasons.YEAR_END_CREDIT["wallet"]
        )
        for id_, company_id in eligible.select("id", "company_id").iter_rows():
            amount = seasons.year_end_credit(company_id, moment.year)
            if amount:
                self.history.append(credit(self.card_wallets, id_, moment, amount))

    def _in_use(self, day: pl.Expr) -> pl.DataFrame:
        """The card wallets the employer credits on `day` (a date, or a column of
        card_wallets): activated, not cancelled, on a card not cancelled, of an
        active cardholder."""
        holders = self.t["cardholders"].select(
            pl.col("id").alias("cardholder_id"),
            "company_id",
            holder="status",
            holder_since="status_since",
        )
        cards = (
            self.t["cards"]
            .join(holders, on="cardholder_id")
            .select(
                pl.col("id").alias("card_id"),
                "company_id",
                "holder",
                "holder_since",
                card="status",
                card_since="status_since",
            )
        )
        return (
            self.t["card_wallets"]
            .join(cards, on="card_id")
            .filter(
                pl.col("activation_date") <= day,
                _status_on(day) != "cancelled",
                _status_on(day, "card", "card_since") != "cancelled",
                _status_on(day, "holder", "holder_since") == "active",
            )
        )

    def _first_credits(self, start: datetime, end: datetime) -> list[tuple[datetime, str]]:
        """Wallets activated in the window: emptied (their balance at the start
        is for the wallets already in use), and the moment and id of their first
        credit, unless the monthly credit lands that day."""
        first = start.date()
        for row in self.card_wallets.rows:
            if row["activation_date"] >= first:
                row["current_balance"] = 0.0
        activated = self._in_use(pl.col("activation_date")).filter(
            pl.col("activation_date") >= first,
            pl.col("activation_date") < end.date(),
            pl.col("activation_date").dt.day() != CREDIT_DAY,
        )
        return [
            (datetime.combine(day, datetime.min.time()), id_)
            for id_, day in activated.select("id", "activation_date").iter_rows()
        ]

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

    def start(
        self, start: datetime, end: datetime, opening: dict[str, float] | None = None
    ) -> None:
        """Open the window [start, end): the balances (`opening`, by card wallet
        id, else the tables'), and the credits scheduled."""
        for row in self.card_wallets.rows:
            if opening and row["id"] in opening:
                row["current_balance"] = opening[row["id"]]
        self.end = end
        self.events: list[tuple[datetime, int, str, Any]] = []
        for moment in credit_moments(start, end):
            self.events.append((moment, 0, "credit", None))
        for year in range(start.year, end.year + 1):
            moment = datetime.combine(seasons.year_end_credit_day(year), time(CREDIT_HOUR))
            if start <= moment < end:
                self.events.append((moment, 0, "year_end_credit", None))
        for moment, card_wallet_id in self._first_credits(start, end):
            self.events.append((moment, 0, "first_credit", card_wallet_id))
        heapq.heapify(self.events)
        self.seq = 0
        self.sequence = 0  # balance movements answered so far
        self.reporting: dict[str, bool] = {}  # card → the cardholder reports its fraud

    def advance(self, attempts: list[dict[str, Any]], until: datetime) -> SimulationResult:
        """Add `attempts` and answer every event before `until` in time order:
        credits, attempts and reversals. Returns the period's transactions and
        balance movements; later events wait for the next call."""
        for tx in sorted(attempts, key=lambda tx: tx["date"]):
            self.seq += 1
            heapq.heappush(self.events, (tx["date"], self.seq, "attempt", tx))

        delay = SIMULATION["reversal_delay_minutes"]
        answered = []
        self.history = []
        while self.events and self.events[0][0] < until:
            moment, _, kind, payload = heapq.heappop(self.events)
            if kind == "credit":
                self.credit(moment)
                continue
            if kind == "year_end_credit":
                self.year_end_credit(moment)
                continue
            if kind == "first_credit":
                wallet = find_one(self.card_wallets, id=payload)
                amount = first_credit(wallet["monthly_credit"], moment.date())
                self.history.append(credit(self.card_wallets, payload, moment, amount))
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
                if when < self.end:
                    self.seq += 1
                    heapq.heappush(self.events, (when, self.seq, "reversal", tx))
        self._forget(until)

        # In the order they happened: the sequence breaks ties of the same second
        history = pl.DataFrame(self.history, schema=HISTORY_SCHEMA).with_columns(
            sequence_number=pl.int_range(
                self.sequence + 1, self.sequence + pl.len() + 1, dtype=pl.Int64
            )
        )
        self.sequence += history.height
        transactions = pl.DataFrame(answered, infer_schema_length=None)
        if transactions.height:
            transactions = mark_disputes(transactions, self.reporting)
        return SimulationResult(transactions=transactions, balance_history=history)

    def _forget(self, before: datetime) -> None:
        """Drop the limit counters of the days and months before `before`."""
        day, month = before.date(), (before.year, before.month)
        self.daily_amount = defaultdict(
            float, {k: v for k, v in self.daily_amount.items() if k[1] >= day}
        )
        self.daily_count = defaultdict(
            int, {k: v for k, v in self.daily_count.items() if k[1] >= day}
        )
        self.monthly_amount = defaultdict(
            float, {k: v for k, v in self.monthly_amount.items() if (k[1], k[2]) >= month}
        )

    def run(
        self,
        attempts: list[dict[str, Any]],
        start: datetime,
        end: datetime,
        opening: dict[str, float] | None = None,
    ) -> SimulationResult:
        """The whole window [start, end) at once (`start`, then `advance`)."""
        self.start(start, end, opening)
        result = self.advance(attempts, end)
        result.card_wallets = self.card_wallets.to_frame()
        return result
