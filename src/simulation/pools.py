"""Where an attempt happens: the terminals of each kind of place, weighted by
the shop's popularity, indexed by city and state for purchases near home and by
the (network, wallet) the shop takes (`usage_patterns`)."""

import random
from datetime import date, datetime
from itertools import accumulate
from typing import NamedTuple

import polars as pl

from src.config import load_reference, load_simulation
from src.domain.acceptance import Acceptance
from src.domain.status import earliest, out_from
from src.entities.establishments import CATEGORIES

USAGE = load_simulation()["usage_patterns"]
PHYSICAL_CAPTURES = {
    code
    for code, rule in load_reference()["transaction_technology_rules"].items()
    if rule["requires_physical_card"]
}
# Terminal types a virtual card can't use: every capture needs the plastic
PHYSICAL_TERMINALS = {
    kind
    for kind, captures in USAGE["capture_by_terminal_type"].items()
    if not set(captures) - PHYSICAL_CAPTURES
}
# Draws of a pool before giving up on a terminal that fits the day and the card
DRAWS = 20


class Pool(NamedTuple):
    """Terminals with their weights, and the cumulative weights to draw from."""

    terminals: list[dict]
    weights: list[float]
    cum: list[float]


def _pool(terminals: list[dict], weights: list[float]) -> Pool:
    return Pool(terminals, weights, list(accumulate(weights)))


class TerminalPools:
    """The pools of a window (`first` to `last` day).

    `everywhere[category]`; `local[(category, city, state)]` and
    `local[(category, state)]`; the same per (network, wallet) the shop takes in
    `fitting`, keyed ((network, wallet), category[, city], state). `open` holds
    the pool keys with a terminal working when the window starts (active, in an
    active shop). A terminal installed in the window, or out of use, is handled
    when drawn (`draw`).
    """

    def __init__(
        self,
        establishments_df: pl.DataFrame,
        terminals_df: pl.DataFrame,
        acceptance: Acceptance,
        first: date,
        last: date,
    ) -> None:
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
            if t["installation_date"] > last:
                continue  # installed after the window
            out = self.terminal_out[t["id"]] = earliest(out_from(t), out_from(shop))
            working = out is None or out > first
            places = [(category, shop["city"], shop["state"]), (category, shop["state"])]
            scopes = acceptance.wallets(shop["main_cnae"], shop["mcc_code"])
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
        self.everywhere = {key: _pool(*pool) for key, pool in everywhere.items()}
        self.terminals = {key: pool.terminals for key, pool in self.everywhere.items()}
        self.local = {key: _pool(*pool) for key, pool in local.items()}
        self.fitting = {key: _pool(*pool) for key, pool in fitting.items()}

    def nearby(
        self,
        category: str,
        home: tuple[str, str],
        network: str,
        wallet: str | None = None,
    ) -> Pool:
        """The category's terminals in the cardholder's city, else state, most of the
        time (`local_purchase_ratio`); anywhere otherwise and for online businesses.
        Mostly (`known_acceptance_ratio`) only shops that take the wallet, and near
        home only where some terminal works."""
        pools, scope = self.local, ()
        everywhere = self.everywhere[category]
        if wallet and random.random() < USAGE["known_acceptance_ratio"]:
            scope = ((network, wallet),)
            if (*scope, category) in self.fitting:
                pools, everywhere = self.fitting, self.fitting[(*scope, category)]
            else:
                scope = ()
        online = CATEGORIES[category].get("online")
        if online or random.random() >= USAGE["local_purchase_ratio"]:
            return everywhere
        city, state = home
        for key in ((*scope, category, city, state), (*scope, category, state)):
            if key in self.open:
                return pools[key]
        return everywhere

    def draw(self, pool: Pool, day: datetime, virtual: bool) -> dict | None:
        """A terminal of the pool by weight, installed by `day` and, for a virtual
        card, with a capture it can use; one out of use that day only now and
        then (`inactive_usage_factor`). None when a few draws find none.

        Drawing the day first and then a terminal installed by then gives a
        terminal installed in the window its share of those days and no more."""
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
