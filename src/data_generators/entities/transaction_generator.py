"""Purchase attempts shaped like a benefits-card market.

Who buys, where, when and how much follow `simulation_config.yaml →
usage_patterns` and `establishment_categories`. Spending follows the credit:
each wallet makes about (monthly credit × the cardholder's spending ratio ÷ the
average ticket where it is used) attempts a month, at the kinds of place that
take it. Popular shops, lunch and evening peaks, more spending early in the
month, small tickets with a long tail. The attempt isn't validated here: the issuer routes
the wallet and answers later (`src/validators/`).
"""

import math
import random
from datetime import date, datetime, timedelta
from itertools import accumulate

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


MCC_WALLETS = {
    wallet: set(mccs) for wallet, mccs in _REFERENCE["mcc_wallets"].items() if mccs != "any"
}


def _category_wallets() -> dict[str, dict[str, set[str]]]:
    """Wallets each category takes, per network: by its CNAEs (own) and MCCs (brand)."""
    cnae_wallets = _REFERENCE["cnae_wallets"]
    result = {}
    for name, category in CATEGORIES.items():
        own = {w for cnae, ws in cnae_wallets.items() if _in(cnae, category) for w in ws}
        mccs = {mcc for cnae, mcc in _REFERENCE["cnae_mcc"].items() if _in(cnae, category)}
        brand = {wallet for wallet, codes in MCC_WALLETS.items() if codes & mccs}
        result[name] = {"own": own, "brand": brand}
    return result


def _in(cnae: str, category: dict) -> bool:
    return any(cnae.startswith(prefix) for prefix in category["cnae"])


def accepted_wallets(cnae: str, mcc: str) -> set[tuple[str, str]]:
    """(network, wallet) pairs an establishment takes: on the proprietary network
    the wallets of its CNAE's longest matching prefix, on a brand the wallets of
    its MCC plus the open one."""
    prefixes = [p for p in _REFERENCE["cnae_wallets"] if cnae.startswith(p)]
    own = _REFERENCE["cnae_wallets"][max(prefixes, key=len)] if prefixes else []
    brand = {w for w, codes in MCC_WALLETS.items() if mcc in codes} | {OPEN_WALLET}
    return {("own", w) for w in own} | {("brand", w) for w in brand}


CATEGORY_WALLETS = _category_wallets()
OPEN_WALLET = "GIFT"  # on a brand card, takes any MCC (and cash)
# The option on the terminal each wallet sits under (proprietary network)
OPTION_OF = {wallet: option for option, wallets in OPTIONS.items() for wallet in wallets}


def wallet_categories(wallet: str, network: str) -> list[str]:
    """Kinds of place a wallet is spent at: by CNAE on the proprietary network
    (`own`), by MCC on a brand (`brand`), anywhere for the brand's open wallet."""
    if network == "brand" and wallet == OPEN_WALLET:
        return list(CATEGORIES)
    return [c for c in CATEGORIES if wallet in CATEGORY_WALLETS[c][network]]


def mean_ticket(category: str) -> float:
    """Mean of the category's log-normal ticket."""
    amount = CATEGORIES[category]["amount"]
    sigma = math.log(amount["p90"] / amount["median"]) / 1.2816
    return min(amount["median"] * math.exp(sigma**2 / 2), amount["max"])


def wallet_mean_ticket(wallet: str, network: str) -> float:
    """Average ticket where the wallet is spent, by category weight."""
    categories = wallet_categories(wallet, network)
    weights = [CATEGORIES[c]["weight"] for c in categories]
    return sum(w * mean_ticket(c) for w, c in zip(weights, categories, strict=True)) / sum(weights)


def spending_ratio() -> float:
    """Share of the monthly credit a cardholder spends: most spend nearly all,
    savers let the balance build up (`usage_patterns.spend_profile`)."""
    profile = USAGE["spend_profile"]
    bounds = profile["saver"] if random.random() < profile["saver_share"] else profile["spender"]
    return random.uniform(bounds["min"], bounds["max"])


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
        # indexed by the shop's city and state, for purchases near home. The
        # same pools per (network, wallet) the shop takes are in `fitting`,
        # keyed ((network, wallet), category[, city], state). `open` holds the
        # pool keys with a working terminal (active, in an active shop).
        establishments = {row["id"]: row for row in establishments_df.to_dicts()}
        popularity = {
            id_: _activity(USAGE["establishment_popularity_sigma"], e["status"] == "active")
            for id_, e in establishments.items()
        }
        self.terminals: dict[str, list[dict]] = {}
        self.terminal_weights: dict[str, list[float]] = {}
        self.local: dict[tuple, tuple[list[dict], list[float]]] = {}
        self.fitting: dict[tuple, tuple[list[dict], list[float]]] = {}
        self.open: set[tuple] = set()
        for t in terminals_df.select(
            "id", "establishment_id", "type", "status", "installation_date"
        ).to_dicts():
            shop = establishments[t["establishment_id"]]
            category = shop["category"]
            weight = popularity[t["establishment_id"]]
            if t["status"] != "active":
                weight *= USAGE["inactive_usage_factor"]
            # Like a card, in proportion to the days it was installed
            weight *= sum(day.date() >= t["installation_date"] for day in self.days) / days_back
            if not weight:
                continue
            self.terminals.setdefault(category, []).append(t)
            self.terminal_weights.setdefault(category, []).append(weight)
            working = t["status"] == "active" and shop["status"] == "active"
            places = [(category, shop["city"], shop["state"]), (category, shop["state"])]
            scopes = accepted_wallets(shop["main_cnae"], shop["mcc_code"])
            keys = [(self.local, key) for key in places] + [
                (self.fitting, (scope, *key)) for scope in scopes for key in [(category,), *places]
            ]
            for pools, key in keys:
                terminals, weights = pools.setdefault(key, ([], []))
                terminals.append(t)
                weights.append(weight)
                if working:
                    self.open.add(key)

        # Who buys: one slot per active wallet of a card, weighted by the
        # attempts a month it makes, the days the card existed in the window,
        # and whether card and cardholder are active
        credit = {
            (card_id, wallet_id): amount
            for card_id, wallet_id, amount, status in card_wallets_df.select(
                "card_id", "wallet_id", "monthly_credit", "status"
            ).iter_rows()
            if status == "active"
        }
        self.slots: list[tuple[dict, str]] = []
        weights = []
        for card in self.cards:
            alive = sum(day.date() >= card["issue_date"] for day in self.days) / days_back
            if not alive:
                continue
            in_use = card["status"] == "active" and holder_active[card["cardholder_id"]]
            factor = 1.0 if in_use else USAGE["inactive_usage_factor"]
            ratio = spending_ratio()
            network = self._network(card)
            for wallet in sorted(self.wallets_by_card.get(card["id"], ())):
                if (card["id"], wallet) not in credit or not self._places(wallet, network):
                    continue
                monthly = credit[card["id"], wallet] * ratio / wallet_mean_ticket(wallet, network)
                self.slots.append((card, wallet))
                weights.append(monthly * alive * factor)
        self.slot_cum_weights = list(accumulate(weights))
        self.monthly_attempts = sum(weights)
        self.days_back = days_back

    def expected_attempts(self) -> float:
        """Attempts the window should hold: the slots' monthly attempts over its days."""
        return self.monthly_attempts * self.days_back / 30

    @staticmethod
    def _network(card: dict) -> str:
        return "own" if card["modality_id"] in PROPRIETARY_MODALITIES else "brand"

    def _places(self, wallet: str, network: str) -> list[str]:
        """The wallet's kinds of place that have terminals."""
        return [c for c in wallet_categories(wallet, network) if c in self.terminals]

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

    def _category(self, card: dict, wallet: str) -> str:
        """A kind of place the wallet is spent at; now and then any place
        (`off_pattern_ratio`)."""
        available = self._places(wallet, self._network(card))
        if random.random() < USAGE["off_pattern_ratio"]:
            available = [c for c in CATEGORIES if c in self.terminals]
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
        days = [
            (d, w) for d, w in zip(self.days, self.day_weights, strict=True) if d.date() >= earliest
        ]
        days = days or [(self.days[-1], 1.0)]
        day = random.choices([d for d, _ in days], weights=[w for _, w in days])[0]
        hours = USAGE["hour_weights_by_category"].get(category, USAGE["hour_weights"])
        hour = random.choices(range(24), weights=hours)[0]
        return day + timedelta(hours=hour, seconds=random.randint(0, 3599))

    def _everywhere(self, category: str) -> tuple[list[dict], list[float]]:
        return self.terminals[category], self.terminal_weights[category]

    def _nearby(
        self, category: str, card: dict, wallet: str | None = None
    ) -> tuple[list[dict], list[float]]:
        """The category's terminals in the cardholder's city, else state, most of the
        time (`local_purchase_ratio`); anywhere otherwise and for online businesses.
        Mostly (`known_acceptance_ratio`) only shops that take the wallet, and near
        home only where some terminal works."""
        pools, scope = self.local, ()
        everywhere = self.terminals[category], self.terminal_weights[category]
        if wallet and random.random() < USAGE["known_acceptance_ratio"]:
            scope = ((self._network(card), wallet),)
            if (*scope, category) in self.fitting:
                pools, everywhere = self.fitting, self.fitting[(*scope, category)]
            else:
                scope = ()
        online = CATEGORIES[category].get("online")
        if online or random.random() >= USAGE["local_purchase_ratio"]:
            return everywhere
        city, state = self.home[card["cardholder_id"]]
        for key in ((*scope, category, city, state), (*scope, category, state)):
            if key in self.open:
                return pools[key]
        return everywhere

    def generate(self) -> dict:
        """One attempt: columns of `transactions`, before the issuer answers."""
        card, wallet = random.choices(self.slots, cum_weights=self.slot_cum_weights)[0]
        category = self._category(card, wallet)
        terminals, weights = self._nearby(category, card, wallet)
        if card["card_type"] == "virtual":
            # A virtual card goes where it can be used: nearby if there is such a
            # terminal, else anywhere in the category
            for pool in ((terminals, weights), self._everywhere(category)):
                usable = [
                    (t, w)
                    for t, w in zip(*pool, strict=True)
                    if set(USAGE["capture_by_terminal_type"][t["type"]]) - PHYSICAL_CAPTURES
                ]
                if usable:
                    terminals, weights = [t for t, _ in usable], [w for _, w in usable]
                    break
        terminal = random.choices(terminals, weights=weights)[0]
        return self.attempt(
            card,
            category,
            terminal,
            # Not before the card exists or the terminal is installed
            self._moment(category, max(card["issue_date"], terminal["installation_date"])),
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
