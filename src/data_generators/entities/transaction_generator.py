"""Purchase attempts shaped like a benefits-card market.

Who buys, where, when and how much follow `simulation_config.yaml →
usage_patterns` and `establishment_categories`. Spending follows the credit:
each wallet makes about (monthly credit × the cardholder's spending ratio ÷ the
average ticket where it is used) attempts a month, at the kinds of place that
take it. Popular shops, lunch and evening peaks, more spending early in the
month, small tickets with a long tail. The attempt isn't validated here: the issuer routes
the wallet and answers later (`src/validators/`).
"""

import calendar
import math
import random
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta
from itertools import accumulate
from typing import NamedTuple

import polars as pl

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.providers import fake, seasons
from src.domain.acceptance import OPEN_WALLET, Acceptance
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
# Terminal types a virtual card can't use: every capture needs the plastic
PHYSICAL_TERMINALS = {
    kind
    for kind, captures in USAGE["capture_by_terminal_type"].items()
    if not set(captures) - PHYSICAL_CAPTURES
}
# Draws of a pool before giving up on a terminal that fits the day and the card
DRAWS = 20
PROPRIETARY_MODALITIES = {
    m["id"] for m in _REFERENCE["transaction_modalities"] if m["type"] == "proprietary_network"
}
# The option a cardholder means to pick at each kind of place
NATURAL_OPTION = {"supermarket": "FOOD", "food_retail": "FOOD", "restaurant": "MEAL"}


ACCEPTANCE = Acceptance.from_config()


def _category_wallets() -> dict[str, dict[str, set[str]]]:
    """Wallets each category takes, per network: by its CNAEs (own) and MCCs (brand),
    the open wallet aside."""
    result = {}
    for name, category in CATEGORIES.items():
        own = {
            w
            for cnae in ACCEPTANCE.cnae_rules
            if _in(cnae, category)
            for w in ACCEPTANCE.by_cnae(cnae)
        }
        mccs = {mcc for cnae, mcc in _REFERENCE["cnae_mcc"].items() if _in(cnae, category)}
        brand = {w for mcc in mccs for w in ACCEPTANCE.by_mcc(mcc)} - {OPEN_WALLET}
        result[name] = {"own": own, "brand": brand}
    return result


def _in(cnae: str, category: dict) -> bool:
    return any(cnae.startswith(prefix) for prefix in category["cnae"])


CATEGORY_WALLETS = _category_wallets()
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


class Pool(NamedTuple):
    """Terminals with their weights, and the cumulative weights to draw from."""

    terminals: list[dict]
    weights: list[float]
    cum: list[float]


def _pool(terminals: list[dict], weights: list[float]) -> Pool:
    return Pool(terminals, weights, list(accumulate(weights)))


def _out_from(row: dict) -> date | None:
    """The day a record stopped being active (`status_since`); None while it is."""
    return None if row["status"] == "active" else row["status_since"]


def _earliest(*days: date | None) -> date | None:
    known = [day for day in days if day is not None]
    return min(known) if known else None


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
        holder_out = {
            row["id"]: _out_from(row)
            for row in cardholders_df.select("id", "status", "status_since").iter_rows(named=True)
        }
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
        end = datetime.combine(fake.reference_date, datetime.min.time())
        self.days = [end - timedelta(days=d) for d in range(days_back, 0, -1)]
        self.dates = [day.date() for day in self.days]
        # Cumulative day weights per category (None: any): its week, the
        # calendar, and the intensity each month draws
        sigma = USAGE["seasonality"]["month_noise_sigma"]
        intensity = {
            month: random.lognormvariate(0, sigma)
            for month in sorted({(day.year, day.month) for day in self.dates})
        }
        weeks = USAGE["weekday_weights_by_category"]
        self.day_cum = {
            category: list(
                accumulate(
                    self._day_weight(day, weeks.get(category, USAGE["weekday_weights"]), category)
                    * intensity[day.year, day.month]
                    for day in self.days
                )
            )
            for category in [None, *CATEGORIES]
        }

        # The wallets a cardholder means to use: the ones active when the window
        # starts (all, if none is)
        self.wallets_by_card: dict[str, set[str]] = {}
        held: dict[str, set[str]] = {}
        for row in card_wallets_df.select(
            "card_id", "wallet_id", "status", "status_since"
        ).iter_rows(named=True):
            held.setdefault(row["card_id"], set()).add(row["wallet_id"])
            out = _out_from(row)
            if out is None or out > self.dates[0]:
                self.wallets_by_card.setdefault(row["card_id"], set()).add(row["wallet_id"])
        for card_id, wallets in held.items():
            self.wallets_by_card.setdefault(card_id, wallets)

        # Terminals of each category, weighted by the shop's popularity; also
        # indexed by the shop's city and state, for purchases near home. The
        # same pools per (network, wallet) the shop takes are in `fitting`,
        # keyed ((network, wallet), category[, city], state). `open` holds the
        # pool keys with a terminal working when the window starts (active, in an
        # active shop). A terminal out of use is drawn only now and then (`_terminal`).
        establishments = {row["id"]: row for row in establishments_df.to_dicts()}
        popularity = {
            id_: random.lognormvariate(0, USAGE["establishment_popularity_sigma"])
            for id_ in establishments
        }
        self.terminal_out: dict[str, date | None] = {}
        everywhere: dict[str, tuple[list[dict], list[float]]] = {}
        local: dict[tuple, tuple[list[dict], list[float]]] = {}
        fitting: dict[tuple, tuple[list[dict], list[float]]] = {}
        self.open: set[tuple] = set()
        for t in terminals_df.select(
            "id", "establishment_id", "type", "status", "status_since", "installation_date"
        ).to_dicts():
            shop = establishments[t["establishment_id"]]
            category = shop["category"]
            weight = popularity[t["establishment_id"]]
            if t["installation_date"] > self.dates[-1]:
                continue  # installed after the window
            out = self.terminal_out[t["id"]] = _earliest(_out_from(t), _out_from(shop))
            working = out is None or out > self.dates[0]
            places = [(category, shop["city"], shop["state"]), (category, shop["state"])]
            scopes = ACCEPTANCE.wallets(shop["main_cnae"], shop["mcc_code"])
            keys = (
                [(everywhere, category)]
                + [(local, key) for key in places]
                + [(fitting, (scope, *key)) for scope in scopes for key in [(category,), *places]]
            )
            for pools, key in keys:
                terminals, weights = pools.setdefault(key, ([], []))
                terminals.append(t)
                weights.append(weight)
                if working:
                    self.open.add(key)
        # A terminal installed in the window is drawn only on the days after
        # (`_terminal`), so it takes its share of those days and no more
        self.everywhere = {key: _pool(*pool) for key, pool in everywhere.items()}
        self.terminals = {key: pool.terminals for key, pool in self.everywhere.items()}
        self.local = {key: _pool(*pool) for key, pool in local.items()}
        self.fitting = {key: _pool(*pool) for key, pool in fitting.items()}

        # Who buys: one slot per wallet of a card, weighted by the attempts a
        # month it makes and the days of the window it is in use: from its
        # activation, at full rate until the card, cardholder or wallet stops
        # being active (`slot_out`), then now and then (`inactive_usage_factor`)
        credit = self.credit = {}
        wallet_out = {}
        self.activation: dict[tuple[str, str], date] = {}
        self.card_wallet_id: dict[tuple[str, str], str] = {}
        for row in card_wallets_df.select(
            "id",
            "card_id",
            "wallet_id",
            "monthly_credit",
            "status",
            "status_since",
            "activation_date",
        ).iter_rows(named=True):
            key = row["card_id"], row["wallet_id"]
            self.activation[key] = row["activation_date"]
            self.card_wallet_id[key] = row["id"]
            credit[key] = row["monthly_credit"]
            wallet_out[key] = _out_from(row)
        self.slot_out: dict[tuple[str, str], date] = {}
        factor = USAGE["inactive_usage_factor"]
        # A slot can be bound to a window of days (first, last): the year-end credit
        self.slots: list[tuple[dict, str, tuple[date, date] | None]] = []
        weights = []
        ratio_of = self.ratio_of = {}
        for card in self.cards:
            card_out = _earliest(_out_from(card), holder_out[card["cardholder_id"]])
            ratio = ratio_of[card["id"]] = spending_ratio()
            network = self._network(card)
            for wallet in sorted(self.wallets_by_card.get(card["id"], ())):
                if not self._places(wallet, network):
                    continue
                first = bisect_left(self.dates, self._usable_from(card, wallet))
                if first == len(self.dates):
                    continue
                out = _earliest(card_out, wallet_out[card["id"], wallet])
                cut = max(first, bisect_left(self.dates, out)) if out else len(self.dates)
                days = (cut - first) + (len(self.dates) - cut) * factor
                if out:
                    self.slot_out[card["id"], wallet] = out
                monthly = credit[card["id"], wallet] * ratio / wallet_mean_ticket(wallet, network)
                self.slots.append((card, wallet, None))
                weights.append(monthly * days / days_back)

        # The year-end credit: the attempts it pays for, over the days after it
        # lands (`simulation.year_end_credit`), on cards in use by then
        bonus = seasons.YEAR_END_CREDIT
        wallet = bonus["wallet"]
        company_of = dict(cardholders_df.select("id", "company_id").iter_rows())
        for year in sorted({day.year for day in self.dates}):
            landing = seasons.year_end_credit_day(year)
            if not self.dates[0] <= landing <= self.dates[-1]:
                continue
            window = landing, landing + timedelta(days=bonus["spend_days"] - 1)
            for card in self.cards:
                network = self._network(card)
                out = self.slot_out.get((card["id"], wallet))
                if (
                    wallet not in self.wallets_by_card.get(card["id"], ())
                    or not self._places(wallet, network)
                    or self._usable_from(card, wallet) > landing
                    or (out and out <= landing)
                ):
                    continue
                amount = seasons.year_end_credit(company_of[card["cardholder_id"]], year)
                if amount:
                    attempts = amount * ratio_of[card["id"]] / wallet_mean_ticket(wallet, network)
                    self.slots.append((card, wallet, window))
                    weights.append(attempts * 30 / days_back)
        self.slot_cum_weights = list(accumulate(weights))
        self.monthly_attempts = sum(weights)
        self.days_back = days_back

    def _usable_from(self, card: dict, wallet: str | None) -> date:
        """The card's issue, or the wallet's activation when later."""
        activated = self.activation.get((card["id"], wallet))
        return max(card["issue_date"], activated) if activated else card["issue_date"]

    def opening_balances(self) -> dict[str, float]:
        """The balance at the window's start of each wallet activated before it,
        in line with how its cardholder spends (`usage_patterns.opening_balance`):
        a spender keeps a little of past months, a saver what built up. When the
        window starts after the month's credit, what is left of it too."""
        opening = USAGE["opening_balance"]
        leftover = opening["spender_leftover"]
        start = self.dates[0]
        credit_day = fake.SETTINGS["benefit_credit_day"]
        days = calendar.monthrange(start.year, start.month)[1]
        elapsed = (start.day - credit_day) / days if start.day > credit_day else None
        balances = {}
        for (card_id, wallet), activated in self.activation.items():
            if activated >= start:
                continue
            credit, ratio = self.credit[card_id, wallet], self.ratio_of.get(card_id, 1.0)
            if ratio >= 1:
                past = random.uniform(leftover["min"], leftover["max"])
            else:
                months = (start.year - activated.year) * 12 + start.month - activated.month
                past = (1 - ratio) * min(months, opening["saver_months"])
            this_month = max(0.0, 1 - ratio * elapsed) if elapsed is not None else 0.0
            balances[self.card_wallet_id[card_id, wallet]] = round(credit * (past + this_month), 2)
        return balances

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
    def _day_weight(day: datetime, week: list[float], category: str | None) -> float:
        """The weekday's weight (a holiday's is Saturday's), higher early in the
        month (the credit lands), times the calendar's (`seasons.day_factor`)."""
        month = USAGE["month_day_weights"]
        progress = (day.day - 1) / 30
        weekday = 5 if seasons.is_holiday(day.date()) else day.weekday()
        return (
            week[weekday]
            * (month["first"] + (month["last"] - month["first"]) * progress)
            * seasons.day_factor(day.date(), category)
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
        network = self._network(card)
        available = self._places(wallet, network)
        if random.random() < USAGE["off_pattern_ratio"]:
            # anywhere, but a proprietary-network card doesn't go to a cash machine
            available = [
                c
                for c in CATEGORIES
                if c in self.terminals and (network == "brand" or not CATEGORIES[c].get("atm"))
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

    def _day(self, earliest: date, category: str, latest: date | None = None) -> datetime:
        """A day of the window from `earliest` on (to `latest`), by the category's
        day weights (the nearest day when none is left)."""
        first = bisect_left(self.dates, earliest)
        stop = bisect_right(self.dates, latest) if latest else len(self.days)
        if first >= stop:
            return self.days[min(first, len(self.days) - 1)]
        cum = self.day_cum.get(category) or self.day_cum[None]
        low = cum[first - 1] if first else 0.0
        point = low + random.random() * (cum[stop - 1] - low)
        return self.days[min(bisect_right(cum, point, first, stop), stop - 1)]

    @staticmethod
    def _at(day: datetime, category: str) -> datetime:
        """A moment of `day` at an hour of the category's day."""
        hours = USAGE["hour_weights_by_category"].get(category, USAGE["hour_weights"])
        hour = random.choices(range(24), weights=hours)[0]
        return day + timedelta(hours=hour, seconds=random.randint(0, 3599))

    def _moment(self, category: str, earliest: date) -> datetime:
        """A day of the window from `earliest` on, then an hour of the category's day."""
        return self._at(self._day(earliest, category), category)

    def _slot_day(
        self, card: dict, wallet: str, category: str, window: tuple[date, date] | None = None
    ) -> datetime:
        """A day once the wallet is usable (within the slot's window, if any);
        after the card, cardholder or wallet stopped being active, kept only now
        and then (`inactive_usage_factor`)."""
        start, latest = self._usable_from(card, wallet), None
        if window:
            start, latest = max(start, window[0]), window[1]
        out = self.slot_out.get((card["id"], wallet))
        day = self._day(start, category, latest)
        if out is None or start >= out:
            return day
        for _ in range(DRAWS):
            if day.date() < out or random.random() < USAGE["inactive_usage_factor"]:
                break
            day = self._day(start, category, latest)
        return day

    def _terminal(self, pool: Pool, day: datetime, virtual: bool) -> dict | None:
        """A terminal of the pool by weight, installed by `day` and, for a virtual
        card, with a capture it can use; one out of use that day only now and
        then (`inactive_usage_factor`). None when a few draws find none."""
        for _ in range(DRAWS):
            terminal = random.choices(pool.terminals, cum_weights=pool.cum)[0]
            if terminal["installation_date"] > day.date() or (
                virtual and terminal["type"] in PHYSICAL_TERMINALS
            ):
                continue
            out = self.terminal_out[terminal["id"]]
            if out is None or day.date() < out or random.random() < USAGE["inactive_usage_factor"]:
                return terminal
        return None

    def _nearby(self, category: str, card: dict, wallet: str | None = None) -> Pool:
        """The category's terminals in the cardholder's city, else state, most of the
        time (`local_purchase_ratio`); anywhere otherwise and for online businesses.
        Mostly (`known_acceptance_ratio`) only shops that take the wallet, and near
        home only where some terminal works."""
        pools, scope = self.local, ()
        everywhere = self.everywhere[category]
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
        card, wallet, window = random.choices(self.slots, cum_weights=self.slot_cum_weights)[0]
        category = self._category(card, wallet)
        # The day first (once the wallet is usable), then a terminal installed by
        # then: nearby if there is one, else anywhere in the category. A virtual
        # card goes where it can be used
        day = self._slot_day(card, wallet, category, window)
        virtual = card["card_type"] == "virtual"
        terminal = self._terminal(
            self._nearby(category, card, wallet), day, virtual
        ) or self._terminal(self.everywhere[category], day, virtual)
        if terminal is None:  # none installed yet: a day after one is
            pool = self.everywhere[category]
            terminal = random.choices(pool.terminals, cum_weights=pool.cum)[0]
            day = self._day(max(day.date(), terminal["installation_date"]), category)
        return self.attempt(
            card,
            category,
            terminal,
            self._at(day, category),
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
