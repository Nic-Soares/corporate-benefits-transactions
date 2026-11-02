"""Who buys and how often: spending follows the credit.

Each wallet of a card is a slot that makes about (monthly credit × the
cardholder's spending ratio ÷ the average ticket where the wallet is used)
attempts a month, while card, cardholder and wallet are active; the year-end
credit adds its own slots. Also the balance each wallet opens the window with.
"""

import calendar
import math
import random
from bisect import bisect_left, bisect_right
from collections.abc import Callable
from datetime import date, timedelta
from itertools import accumulate

import polars as pl

from src.config import load_pre_populated_data, load_simulation_config
from src.domain.acceptance import OPEN_WALLET, Acceptance
from src.domain.status import earliest, out_from
from src.entities import fake
from src.entities.establishments import CATEGORIES
from src.simulation import seasons

USAGE = load_simulation_config()["usage_patterns"]
ACCEPTANCE = Acceptance.from_config()
_REFERENCE = load_pre_populated_data()
PROPRIETARY_MODALITIES = {
    m["id"] for m in _REFERENCE["transaction_modalities"] if m["type"] == "proprietary_network"
}


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


def network(card: dict) -> str:
    """`own` (proprietary network) or `brand`."""
    return "own" if card["modality_id"] in PROPRIETARY_MODALITIES else "brand"


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


# A slot: (card, wallet, window of days or None)
Slot = tuple[dict, str, tuple[date, date] | None]


class Demand:
    """The slots of a window, weighted by the attempts each makes."""

    def __init__(
        self,
        cards: list[dict],
        cardholders_df: pl.DataFrame,
        card_wallets_df: pl.DataFrame,
        cal: seasons.Calendar,
        places: Callable[[str, str], list[str]],
    ) -> None:
        """`places(wallet, network)`: the wallet's kinds of place that have terminals."""
        self.cal = cal
        dates = cal.dates
        days_back = len(dates)
        holder_out = {
            row["id"]: out_from(row)
            for row in cardholders_df.select("id", "status", "status_since").iter_rows(named=True)
        }

        # The wallets a cardholder means to use: the ones active when the window
        # starts (all, if none is)
        self.wallets_by_card: dict[str, set[str]] = {}
        held: dict[str, set[str]] = {}
        self.credit: dict[tuple[str, str], float] = {}
        self.activation: dict[tuple[str, str], date] = {}
        self.card_wallet_id: dict[tuple[str, str], str] = {}
        wallet_out = {}
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
            held.setdefault(row["card_id"], set()).add(row["wallet_id"])
            out = wallet_out[key] = out_from(row)
            if out is None or out > dates[0]:
                self.wallets_by_card.setdefault(row["card_id"], set()).add(row["wallet_id"])
            self.activation[key] = row["activation_date"]
            self.card_wallet_id[key] = row["id"]
            self.credit[key] = row["monthly_credit"]
        for card_id, wallets in held.items():
            self.wallets_by_card.setdefault(card_id, wallets)

        # One slot per wallet of a card, weighted by the attempts a month it
        # makes and the days of the window it is in use: from its activation, at
        # full rate until the card, cardholder or wallet stops being active
        # (`slot_out`), then now and then (`inactive_usage_factor`)
        self.slot_out: dict[tuple[str, str], date] = {}
        factor = USAGE["inactive_usage_factor"]
        self.slots: list[Slot] = []
        weights = []
        self.ratio_of: dict[str, float] = {}
        for card in cards:
            card_out = earliest(out_from(card), holder_out[card["cardholder_id"]])
            ratio = self.ratio_of[card["id"]] = spending_ratio()
            net = network(card)
            for wallet in sorted(self.wallets_by_card.get(card["id"], ())):
                if not places(wallet, net):
                    continue
                first = bisect_left(dates, self.usable_from(card, wallet))
                if first == len(dates):
                    continue
                out = earliest(card_out, wallet_out[card["id"], wallet])
                cut = max(first, bisect_left(dates, out)) if out else len(dates)
                days = (cut - first) + (len(dates) - cut) * factor
                if out:
                    self.slot_out[card["id"], wallet] = out
                monthly = self.credit[card["id"], wallet] * ratio / wallet_mean_ticket(wallet, net)
                self.slots.append((card, wallet, None))
                weights.append(monthly * days / days_back)

        # The year-end credit: the attempts it pays for, over the days after it
        # lands (`simulation.year_end_credit`), on cards in use by then
        bonus = seasons.YEAR_END_CREDIT
        wallet = bonus["wallet"]
        company_of = dict(cardholders_df.select("id", "company_id").iter_rows())
        for year in sorted({day.year for day in dates}):
            landing = seasons.year_end_credit_day(year)
            if not dates[0] <= landing <= dates[-1]:
                continue
            window = landing, landing + timedelta(days=bonus["spend_days"] - 1)
            for card in cards:
                net = network(card)
                out = self.slot_out.get((card["id"], wallet))
                if (
                    wallet not in self.wallets_by_card.get(card["id"], ())
                    or not places(wallet, net)
                    or self.usable_from(card, wallet) > landing
                    or (out and out <= landing)
                ):
                    continue
                amount = seasons.year_end_credit(company_of[card["cardholder_id"]], year)
                if amount:
                    attempts = amount * self.ratio_of[card["id"]] / wallet_mean_ticket(wallet, net)
                    self.slots.append((card, wallet, window))
                    weights.append(attempts * 30 / days_back)
        self.cum_weights = list(accumulate(weights))
        self.monthly_attempts = sum(weights)

    def usable_from(self, card: dict, wallet: str | None) -> date:
        """The card's issue, or the wallet's activation when later."""
        activated = self.activation.get((card["id"], wallet))
        return max(card["issue_date"], activated) if activated else card["issue_date"]

    def draw_index(self) -> int:
        """A slot, by weight: its index in `slots`."""
        point = random.random() * self.cum_weights[-1]
        return min(bisect_right(self.cum_weights, point), len(self.slots) - 1)

    def day(self, slot: Slot, category: str):
        """A day once the wallet is usable (within the slot's window, if any);
        after the card, cardholder or wallet stopped being active, kept only now
        and then (`inactive_usage_factor`)."""
        card, wallet, window = slot
        start, latest = self.usable_from(card, wallet), None
        if window:
            start, latest = max(start, window[0]), window[1]
        out = self.slot_out.get((card["id"], wallet))
        day = self.cal.day(start, category, latest)
        if out is None or start >= out:
            return day
        for _ in range(20):
            if day.date() < out or random.random() < USAGE["inactive_usage_factor"]:
                break
            day = self.cal.day(start, category, latest)
        return day

    def expected_attempts(self) -> float:
        """Attempts the window should hold: the slots' monthly attempts over its days."""
        return self.monthly_attempts * len(self.cal.dates) / 30

    def opening_balances(self) -> dict[str, float]:
        """The balance at the window's start of each wallet activated before it,
        in line with how its cardholder spends (`usage_patterns.opening_balance`):
        a spender keeps a little of past months, a saver what built up. When the
        window starts after the month's credit, what is left of it too."""
        opening = USAGE["opening_balance"]
        leftover = opening["spender_leftover"]
        start = self.cal.dates[0]
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
