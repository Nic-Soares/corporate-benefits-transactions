"""Purchase attempts shaped like a benefits-card market.

Who buys follows the credit (`demand.Demand`), when follows the calendar
(`seasons.Calendar`), where follows the shops near home that take the wallet
(`pools.TerminalPools`); how much is a log-normal ticket of the kind of place
(`establishment_categories`). The attempt isn't validated here: the issuer
routes the wallet and answers later (`simulator`).
"""

import random
from datetime import date, datetime

import polars as pl

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.providers import fake
from src.simulation.demand import (
    ACCEPTANCE,
    CATEGORY_WALLETS,
    PROPRIETARY_MODALITIES,
    Demand,
    network,
    wallet_categories,
)
from src.simulation.pools import PHYSICAL_CAPTURES, TerminalPools
from src.simulation.seasons import Calendar
from src.utils.read_yamls import load_simulation_config, load_validation_rules

USAGE = load_simulation_config()["usage_patterns"]
ROUTING = load_validation_rules()["business_rules_validations"]["wallet_routing"]
OPTIONS: dict[str, list[str]] = ROUTING["proprietary_options"]
# The option on the terminal each wallet sits under (proprietary network)
OPTION_OF = {wallet: option for option, wallets in OPTIONS.items() for wallet in wallets}
# The option a cardholder means to pick at each kind of place
NATURAL_OPTION = {"supermarket": "FOOD", "food_retail": "FOOD", "restaurant": "MEAL"}
PIN_CAPTURES = {"CHIP", "MAG_STRIPE"}


def pin_status(capture_type: str) -> str:
    """`ok` or `wrong` when the capture asks for a PIN, `not_required` otherwise."""
    if capture_type not in PIN_CAPTURES:
        return "not_required"
    return "wrong" if random.random() < USAGE["wrong_pin_ratio"] else "ok"


class TransactionGenerator:
    """Draws purchase attempts over the `days_back` days before the reference date."""

    def __init__(
        self,
        cards_df: pl.DataFrame,
        cardholders_df: pl.DataFrame,
        card_wallets_df: pl.DataFrame,
        establishments_df: pl.DataFrame,
        terminals_df: pl.DataFrame,
        days_back: int = 30,
    ) -> None:
        self.home = {
            row["id"]: (row["city"], row["state"])
            for row in cardholders_df.select("id", "city", "state").iter_rows(named=True)
        }
        self.cards = cards_df.select(
            "id",
            "cardholder_id",
            "modality_id",
            "card_type",
            "status",
            "status_since",
            "issue_date",
        ).to_dicts()
        self.calendar = Calendar(fake.reference_date, days_back, list(CATEGORIES))
        self.days = self.calendar.days
        self.pools = TerminalPools(
            establishments_df,
            terminals_df,
            ACCEPTANCE,
            self.calendar.dates[0],
            self.calendar.dates[-1],
        )
        self.terminals = self.pools.terminals
        self.local = self.pools.local
        self.demand = Demand(
            self.cards, cardholders_df, card_wallets_df, self.calendar, self._places
        )
        self.wallets_by_card = self.demand.wallets_by_card

    def _places(self, wallet: str, network: str) -> list[str]:
        """The wallet's kinds of place that have terminals."""
        return [c for c in wallet_categories(wallet, network) if c in self.terminals]

    def expected_attempts(self) -> float:
        return self.demand.expected_attempts()

    def opening_balances(self) -> dict[str, float]:
        return self.demand.opening_balances()

    def _fits(self, category: str, card: dict) -> bool:
        """Some wallet of the card is meant for this kind of place."""
        wallets = self.wallets_by_card[card["id"]]
        if card["modality_id"] in PROPRIETARY_MODALITIES:
            return not CATEGORIES[category].get("atm") and bool(
                CATEGORY_WALLETS[category]["own"] & wallets
            )
        if CATEGORIES[category].get("atm"):
            return bool(set(ROUTING["withdrawal_wallets"]) & wallets)
        return bool(CATEGORY_WALLETS[category]["brand"] & wallets)

    def _category(self, card: dict, wallet: str) -> str:
        """A kind of place the wallet is spent at; now and then any place
        (`off_pattern_ratio`)."""
        net = network(card)
        available = self._places(wallet, net)
        if random.random() < USAGE["off_pattern_ratio"]:
            # anywhere, but a proprietary-network card doesn't go to a cash machine
            available = [
                c
                for c in CATEGORIES
                if c in self.terminals and (net == "brand" or not CATEGORIES[c].get("atm"))
            ]
        return random.choices(available, weights=[CATEGORIES[c]["weight"] for c in available])[0]

    def _option(self, category: str, card: dict, wallet: str | None = None) -> str | None:
        """Proprietary network: the option picked on the terminal (FOOD, MEAL, OTHERS):
        the one of the wallet the cardholder means to use, or of the kind of place."""
        if card["modality_id"] not in PROPRIETARY_MODALITIES:
            return None
        wallets = self.wallets_by_card[card["id"]]
        held = [option for option, members in OPTIONS.items() if set(members) & wallets]
        natural = OPTION_OF[wallet] if wallet else NATURAL_OPTION.get(category, "OTHERS")
        if natural in held and random.random() >= USAGE["wrong_option_ratio"]:
            return natural
        return random.choice(held)

    def _capture(self, terminal_type: str, card_type: str) -> str:
        weights = USAGE["capture_by_terminal_type"][terminal_type]
        if card_type == "virtual":
            weights = {c: w for c, w in weights.items() if c not in PHYSICAL_CAPTURES}
            if not weights:  # a virtual card where only a physical one works
                return "MOBILE_NFC"
        return fake.weighted_key(weights)

    def _moment(self, category: str, earliest: date) -> datetime:
        """A day of the window from `earliest` on, then an hour of the category's day."""
        return self.calendar.moment(category, earliest)

    def generate(self) -> dict:
        """One attempt: columns of `transactions`, before the issuer answers."""
        slot = self.demand.draw()
        card, wallet, _ = slot
        category = self._category(card, wallet)
        # The day first (once the wallet is usable), then a terminal installed by
        # then: nearby if there is one, else anywhere in the category. A virtual
        # card goes where it can be used
        day = self.demand.day(slot, category)
        virtual = card["card_type"] == "virtual"
        nearby = self.pools.nearby(
            category, self.home[card["cardholder_id"]], network(card), wallet
        )
        terminal = self.pools.draw(nearby, day, virtual) or self.pools.draw(
            self.pools.everywhere[category], day, virtual
        )
        if terminal is None:  # none installed yet: a day after one is
            pool = self.pools.everywhere[category]
            terminal = random.choices(pool.terminals, cum_weights=pool.cum)[0]
            day = self.calendar.day(max(day.date(), terminal["installation_date"]), category)
        return self.attempt(
            card,
            category,
            terminal,
            self.calendar.at(day, category),
            self._capture(terminal["type"], card["card_type"]),
            wallet=wallet,
        )

    def amount(self, category: str, factor: float = 1.0) -> float:
        """A log-normal ticket of the category; `factor` scales median and 90th percentile."""
        amount = CATEGORIES[category]["amount"]
        return fake.lognormal_amount(
            amount["median"] * factor,
            amount["p90"] * factor,
            amount["max"],
            amount.get("step", 0.01),
        )

    def attempt(
        self,
        card: dict,
        category: str,
        terminal: dict,
        moment: datetime,
        capture_type: str,
        amount: float | None = None,
        pin: str | None = None,
        fraud_scenario: str | None = None,
        wallet: str | None = None,
    ) -> dict:
        """One attempt: columns of `transactions`, before the issuer answers."""
        return {
            "id": fake.new_id("tx"),
            "card_id": card["id"],
            "card_wallet_id": None,
            "transaction_type": "withdrawal" if CATEGORIES[category].get("atm") else "purchase",
            "wallet_option": self._option(category, card, wallet),
            "establishment_id": terminal["establishment_id"],
            "terminal_id": terminal["id"],
            "amount": amount if amount is not None else self.amount(category),
            "date": moment,
            "capture_type": capture_type,
            "pin_status": pin or pin_status(capture_type),
            "response_code": None,
            "decline_reason": None,
            "nsu": f"{random.randrange(10**12):012d}",
            "authorization_code": None,
            "related_transaction_id": None,
            "is_fraud": fraud_scenario is not None,
            "fraud_scenario": fraud_scenario,
            "disputed": False,
        }
