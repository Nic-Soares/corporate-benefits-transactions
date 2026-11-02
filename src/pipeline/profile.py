"""The dataset's statistical profile: the shape a user relies on when testing a
dashboard, a metric or a pipeline. Each measure has the range the config
expects (`simulation.yaml → quality_profile`); the export fails when one
is off, and writes them all to the quality report.
"""

import math
from dataclasses import dataclass

import duckdb

from src.config import load_simulation
from src.entities.establishments import CATEGORIES

_CONFIG = load_simulation()
PROFILE = _CONFIG["quality_profile"]
REVERSAL_RATIO = _CONFIG["simulation"]["reversal_ratio"]

ATTEMPTS = "FROM fact_transactions WHERE transaction_type <> 'reversal'"


@dataclass
class Measure:
    name: str
    value: float | None
    low: float
    high: float

    @property
    def passed(self) -> bool:
        return self.value is not None and self.low <= self.value <= self.high


def _one(duck: duckdb.DuckDBPyConnection, sql: str) -> float | None:
    value = duck.sql(sql).fetchall()[0][0]
    return None if value is None else float(value)


def measures(duck: duckdb.DuckDBPyConnection) -> list[Measure]:
    """Every measure of the profile on the OLAP database."""
    found: list[Measure] = []

    # Months: each approves within the range, none drifts out
    approval = PROFILE["monthly_approval"]
    for month, rate in duck.sql(
        f"SELECT strftime(date, '%Y-%m'), avg((response_code = '00')::INT) {ATTEMPTS} "
        "GROUP BY 1 HAVING count(*) >= 1000 ORDER BY 1"
    ).fetchall():
        found.append(Measure(f"approval {month}", rate, approval["min"], approval["max"]))

    # Tickets: each kind of place near the median the config draws from
    tolerance = PROFILE["ticket_median_tolerance"]
    for category, median in duck.sql(
        "SELECT e.category, median(f.amount) FROM fact_transactions f "
        "JOIN dim_establishments e ON e.id = f.establishment_id "
        "WHERE f.transaction_type = 'purchase' AND NOT f.is_fraud GROUP BY 1 "
        "HAVING count(*) >= 500 ORDER BY 1"
    ).fetchall():
        expected = CATEGORIES[category]["amount"]["median"]
        found.append(
            Measure(
                f"median ticket {category} (BRL)",
                float(median),
                round(expected * (1 - tolerance), 2),
                round(expected * (1 + tolerance), 2),
            )
        )

    # When: restaurants peak at lunch and sell less on weekends
    low, high = PROFILE["restaurant_peak_hours"]
    peak = _one(
        duck,
        "SELECT hour(f.date) FROM fact_transactions f "
        "JOIN dim_establishments e ON e.id = f.establishment_id "
        "WHERE e.category = 'restaurant' GROUP BY 1 ORDER BY count(*) DESC LIMIT 1",
    )
    found.append(Measure("restaurant peak hour", peak, low, high))
    weekend = _one(
        duck,
        "SELECT (count(*) FILTER (WHERE isodow(f.date) >= 6) / 2.0) "
        "/ (count(*) FILTER (WHERE isodow(f.date) < 6) / 5.0) FROM fact_transactions f "
        "JOIN dim_establishments e ON e.id = f.establishment_id WHERE e.category = 'restaurant'",
    )
    ratio = PROFILE["restaurant_weekend_to_weekday"]
    found.append(Measure("restaurant weekend day ÷ weekday", weekend, ratio["min"], ratio["max"]))

    # Why declined: mostly the balance ran out
    share = PROFILE["insufficient_balance_share_of_declines"]
    found.append(
        Measure(
            "insufficient balance ÷ declines",
            _one(
                duck,
                "SELECT avg((decline_reason = 'insufficient_balance')::INT) "
                f"{ATTEMPTS} AND response_code <> '00'",
            ),
            share["min"],
            share["max"],
        )
    )

    # Reversals: the configured share of approved purchases
    tolerance = PROFILE["reversal_ratio_tolerance"]
    found.append(
        Measure(
            "reversals ÷ approved purchases",
            _one(
                duck,
                "SELECT count(*) FILTER (WHERE transaction_type = 'reversal') / count(*) FILTER "
                "(WHERE transaction_type = 'purchase' AND response_code = '00') "
                "FROM fact_transactions",
            ),
            REVERSAL_RATIO * (1 - tolerance),
            REVERSAL_RATIO * (1 + tolerance),
        )
    )

    # Where: in person, mostly in the cardholder's state; a few shops take most
    home = PROFILE["home_state_share"]
    found.append(
        Measure(
            "in-person purchases in the cardholder's state",
            _one(
                duck,
                "SELECT avg((h.state = e.state)::INT) FROM fact_transactions f "
                "JOIN dim_cardholders h ON h.id = f.cardholder_id "
                "JOIN dim_establishments e ON e.id = f.establishment_id "
                "JOIN dim_terminals t ON t.id = f.terminal_id "
                "WHERE t.type IN ('POS', 'TEF') AND NOT f.is_fraud",
            ),
            home["min"],
            home["max"],
        )
    )
    top = PROFILE["top_fifth_establishments_share"]
    found.append(
        Measure(
            "attempts at the busiest fifth of the establishments",
            _one(
                duck,
                "WITH n AS (SELECT establishment_id, count(*) c FROM fact_transactions "
                "GROUP BY 1), "
                "r AS (SELECT c, row_number() OVER (ORDER BY c DESC) i, count(*) OVER () k FROM n) "
                "SELECT sum(c) FILTER (WHERE i <= k / 5) / sum(c) FROM r",
            ),
            top["min"],
            top["max"],
        )
    )

    # The calendar: supermarkets on Christmas Eve, when the window holds one
    lift = _one(
        duck,
        "WITH d AS (SELECT f.date::DATE d, count(*) c FROM fact_transactions f "
        "JOIN dim_establishments e ON e.id = f.establishment_id "
        "WHERE e.category = 'supermarket' GROUP BY 1) "
        "SELECT max(c) FILTER (WHERE month(d) = 12 AND day(d) = 24) / avg(c) FROM d",
    )
    if lift is not None:
        found.append(
            Measure(
                "supermarket Christmas Eve ÷ average day",
                lift,
                PROFILE["christmas_eve_lift"],
                math.inf,
            )
        )
    return found


def render(found: list[Measure]) -> list[str]:
    """The profile as Markdown lines for the quality report."""
    lines = ["", "## Statistical profile", ""]
    lines += ["| Measure | Value | Expected | |", "|---|---:|---|---|"]
    for m in found:
        value = "—" if m.value is None else f"{m.value:,.3f}".rstrip("0").rstrip(".")
        expected = f"≥ {m.low:g}" if m.high == math.inf else f"{m.low:g} – {m.high:g}"
        lines.append(f"| {m.name} | {value} | {expected} | {'✅' if m.passed else '❌'} |")
    return lines
