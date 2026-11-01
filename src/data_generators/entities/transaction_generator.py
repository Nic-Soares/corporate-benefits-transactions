"""Purchase attempts shaped like a benefits-card market.

Who buys, where, when and how much follow `simulation_config.yaml →
usage_patterns` and `establishment_categories`: a few heavy cards, popular
shops, lunch and evening peaks, more spending early in the month, small
tickets with a long tail. The attempt isn't validated here: the issuer routes
the wallet and answers later (`src/validators/`).
"""

import random
from datetime import date, datetime, timedelta

import polars as pl

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.providers import fake
from src.utils.read_yamls import (
    load_business_rules,
    load_pre_populated_data,
    load_simulation_config,
    load_validation_rules,
)

_REFERENCE = load_pre_populated_data()
USAGE = load_simulation_config()["usage_patterns"]
ROUTING = load_validation_rules()["business_rules_validations"]["wallet_routing"]
OPTIONS: dict[str, list[str]] = ROUTING["proprietary_options"]
PHYSICAL_CAPTURES = {
    code
    for code, rule in load_business_rules()["transaction_technology_rules"].items()
    if rule["requires_physical_card"]
}
PIN_CAPTURES = {"CHIP", "MAG_STRIPE"}
PROPRIETARY_MODALITIES = {
    m["id"] for m in _REFERENCE["transaction_modalities"] if m["type"] == "proprietary_network"
}
# The option a cardholder means to pick at each kind of place
NATURAL_OPTION = {"supermarket": "FOOD", "food_retail": "FOOD", "restaurant": "MEAL"}


def _category_wallets() -> dict[str, dict[str, set[str]]]:
    """Wallets each category takes, per network: by its CNAEs (own) and MCCs (brand)."""
    cnae_wallets = _REFERENCE["cnae_wallets"]
    mcc_wallets = {
        wallet: set(mccs) for wallet, mccs in _REFERENCE["mcc_wallets"].items() if mccs != "any"
    }
    result = {}
    for name, category in CATEGORIES.items():
        own = {w for cnae, ws in cnae_wallets.items() if _in(cnae, category) for w in ws}
        mccs = {mcc for cnae, mcc in _REFERENCE["cnae_mcc"].items() if _in(cnae, category)}
        brand = {wallet for wallet, codes in mcc_wallets.items() if codes & mccs}
        result[name] = {"own": own, "brand": brand}
    return result


def _in(cnae: str, category: dict) -> bool:
    return any(cnae.startswith(prefix) for prefix in category["cnae"])


CATEGORY_WALLETS = _category_wallets()


def pin_status(capture_type: str) -> str:
    """`ok` or `wrong` when the capture asks for a PIN, `not_required` otherwise."""
    if capture_type not in PIN_CAPTURES:
        return "not_required"
    return "wrong" if random.random() < USAGE["wrong_pin_ratio"] else "ok"


def _activity(sigma: float, active: bool) -> float:
    weight = random.lognormvariate(0, sigma)
    return weight if active else weight * USAGE["inactive_usage_factor"]


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
        holder_active = {
            row["id"]: row["status"] == "active"
            for row in cardholders_df.select("id", "status").iter_rows(named=True)
        }
        self.home = {
            row["id"]: (row["city"], row["state"])
            for row in cardholders_df.select("id", "city", "state").iter_rows(named=True)
        }
        self.cards = cards_df.select(
            "id", "cardholder_id", "modality_id", "card_type", "status", "issue_date"
        ).to_dicts()
        end = datetime.combine(fake.reference_date, datetime.min.time())
        self.days = [end - timedelta(days=d) for d in range(days_back, 0, -1)]
        self.day_weights = [self._day_weight(day) for day in self.days]

        # A card buys in proportion to its activity and to the days it existed
        sigma = USAGE["card_activity_sigma"]
        self.card_weights = [
            _activity(sigma, c["status"] == "active" and holder_active[c["cardholder_id"]])
            * sum(day.date() >= c["issue_date"] for day in self.days)
            / days_back
            for c in self.cards
        ]
        # The wallets a cardholder means to use: the active ones (all, if none is)
        self.wallets_by_card: dict[str, set[str]] = {}
        held: dict[str, set[str]] = {}
        for card_id, wallet_id, status in card_wallets_df.select(
            "card_id", "wallet_id", "status"
        ).iter_rows():
            held.setdefault(card_id, set()).add(wallet_id)
            if status == "active":
                self.wallets_by_card.setdefault(card_id, set()).add(wallet_id)
        for card_id, wallets in held.items():
            self.wallets_by_card.setdefault(card_id, wallets)

        # Terminals of each category, weighted by the shop's popularity; also
        # indexed by the shop's city and state, for purchases near home
        popularity = {
            row["id"]: _activity(USAGE["establishment_popularity_sigma"], row["status"] == "active")
            for row in establishments_df.select("id", "status").iter_rows(named=True)
        }
        category_of = dict(establishments_df.select("id", "category").iter_rows())
        place_of = {
            row["id"]: (row["city"], row["state"])
            for row in establishments_df.select("id", "city", "state").iter_rows(named=True)
        }
        self.terminals: dict[str, list[dict]] = {}
        self.terminal_weights: dict[str, list[float]] = {}
        self.local: dict[tuple, tuple[list[dict], list[float]]] = {}
        for t in terminals_df.select(
            "id", "establishment_id", "type", "status", "installation_date"
        ).to_dicts():
            category = category_of[t["establishment_id"]]
            weight = popularity[t["establishment_id"]]
            if t["status"] != "active":
                weight *= USAGE["inactive_usage_factor"]
            # Like a card, in proportion to the days it was installed
            weight *= sum(day.date() >= t["installation_date"] for day in self.days) / days_back
            if not weight:
                continue
            self.terminals.setdefault(category, []).append(t)
            self.terminal_weights.setdefault(category, []).append(weight)
            city, state = place_of[t["establishment_id"]]
            for key in ((category, city, state), (category, state)):
                terminals, weights = self.local.setdefault(key, ([], []))
                terminals.append(t)
                weights.append(weight)

    @staticmethod
    def _day_weight(day: datetime) -> float:
        month = USAGE["month_day_weights"]
        progress = (day.day - 1) / 30
        return USAGE["weekday_weights"][day.weekday()] * (
            month["first"] + (month["last"] - month["first"]) * progress
        )

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

    def _category(self, card: dict) -> str:
        available = [c for c in CATEGORIES if c in self.terminals]
        fitting = [c for c in available if self._fits(c, card)]
        if fitting and random.random() >= USAGE["off_pattern_ratio"]:
            available = fitting
        return random.choices(available, weights=[CATEGORIES[c]["weight"] for c in available])[0]

    def _option(self, category: str, card: dict) -> str | None:
        """Proprietary network: the option picked on the terminal (FOOD, MEAL, OTHERS)."""
        if card["modality_id"] not in PROPRIETARY_MODALITIES:
            return None
        wallets = self.wallets_by_card[card["id"]]
        held = [option for option, members in OPTIONS.items() if set(members) & wallets]
        natural = NATURAL_OPTION.get(category, "OTHERS")
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
        days = [
            (d, w) for d, w in zip(self.days, self.day_weights, strict=True) if d.date() >= earliest
        ]
        days = days or [(self.days[-1], 1.0)]
        day = random.choices([d for d, _ in days], weights=[w for _, w in days])[0]
        hours = USAGE["hour_weights_by_category"].get(category, USAGE["hour_weights"])
        hour = random.choices(range(24), weights=hours)[0]
        return day + timedelta(hours=hour, seconds=random.randint(0, 3599))

    def _nearby(self, category: str, card: dict) -> tuple[list[dict], list[float]]:
        """The category's terminals in the cardholder's city, else state, most of the
        time (`local_purchase_ratio`); anywhere otherwise and for online businesses."""
        everywhere = self.terminals[category], self.terminal_weights[category]
        online = CATEGORIES[category].get("online")
        if online or random.random() >= USAGE["local_purchase_ratio"]:
            return everywhere
        city, state = self.home[card["cardholder_id"]]
        return self.local.get((category, city, state)) or self.local.get(
            (category, state), everywhere
        )

    def generate(self) -> dict:
        """One attempt: columns of `transactions`, before the issuer answers."""
        card = random.choices(self.cards, weights=self.card_weights)[0]
        category = self._category(card)
        terminals, weights = self._nearby(category, card)
        if card["card_type"] == "virtual":
            # A virtual card goes where it can be used, when there is such a terminal
            usable = [
                (t, w)
                for t, w in zip(terminals, weights, strict=True)
                if set(USAGE["capture_by_terminal_type"][t["type"]]) - PHYSICAL_CAPTURES
            ]
            if usable:
                terminals, weights = [t for t, _ in usable], [w for _, w in usable]
        terminal = random.choices(terminals, weights=weights)[0]
        capture_type = self._capture(terminal["type"], card["card_type"])
        amount = CATEGORIES[category]["amount"]

        return {
            "id": fake.new_id("tx"),
            "card_id": card["id"],
            "card_wallet_id": None,
            "transaction_type": "withdrawal" if CATEGORIES[category].get("atm") else "purchase",
            "wallet_option": self._option(category, card),
            "establishment_id": terminal["establishment_id"],
            "terminal_id": terminal["id"],
            "amount": fake.lognormal_amount(
                amount["median"], amount["p90"], amount["max"], amount.get("step", 0.01)
            ),
            # Not before the card exists or the terminal is installed
            "date": self._moment(category, max(card["issue_date"], terminal["installation_date"])),
            "capture_type": capture_type,
            "pin_status": pin_status(capture_type),
            "response_code": None,
            "decline_reason": None,
            "nsu": f"{random.randrange(10**12):012d}",
            "authorization_code": None,
            "related_transaction_id": None,
        }
