"""`simulate`: purchase attempts answered by the issuer, written to the OLTP database."""

import logging
from collections import defaultdict
from datetime import date, datetime, time, timedelta

import polars as pl
import psycopg

from src.data_generators.providers import fake
from src.infrastructure.database.postgres_manager import (
    bulk_load,
    copy_dataframe,
    count_rows,
    read_table,
)
from src.pipeline import provenance
from src.simulation.fraud import FRAUD, FraudGenerator
from src.simulation.generator import TransactionGenerator
from src.simulation.simulator import TABLES, TransactionSimulator
from src.utils.read_yamls import load_simulation_config

log = logging.getLogger(__name__)


class SimulationError(Exception):
    pass


def run_simulation(conn: psycopg.Connection, seed: int, today: date, days: int) -> dict:
    """Simulate the `days` before `today` and write the result. Doesn't commit.

    The volume follows the credits (`TransactionGenerator.expected_attempts`).
    Stops when the database
    already has transactions (balances moved: start over with `setup --reset`),
    has no entities, or when `today` is before the generated data.
    Returns the counts and the share of each response.
    """
    if count_rows(conn, "transactions"):
        raise SimulationError(
            "The database already has transactions; run setup --reset to start over"
        )
    tables = {name: read_table(conn, name) for name in TABLES}
    if not tables["cards"].height:
        raise SimulationError("No entities in the database; run setup first")
    latest = max(
        tables["cards"]["issue_date"].max(), tables["terminals"]["installation_date"].max()
    )
    if today < latest:
        raise SimulationError(
            f"--today {today} is before the generated data ({latest}); use setup's --today"
        )

    fake.seed(seed, today=today)
    generator = TransactionGenerator(
        tables["cards"],
        tables["cardholders"],
        tables["card_wallets"],
        tables["establishments"],
        tables["terminals"],
        days_back=days,
    )
    n_attempts = round(generator.expected_attempts())
    plan = generator.plan(n_attempts)
    fraud: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for tx in FraudGenerator(generator).generate(round(n_attempts * FRAUD["share_of_attempts"])):
        fraud[tx["date"].year, tx["date"].month].append(tx)
    log.info(
        "%s attempts planned (%s in fraud incidents)",
        f"{n_attempts + sum(map(len, fraud.values())):,}",
        sum(map(len, fraud.values())),
    )

    # Month by month: the attempts of a month are built, answered and written,
    # so memory follows a month, not the window
    end = datetime.combine(today, time())
    start = end - timedelta(days=days)
    simulator = TransactionSimulator(tables)
    simulator.start(start, end, generator.opening_balances())
    totals = {"transactions": 0, "balance_history": 0, "approved": 0, "fraud": 0, "disputed": 0}
    answers: list[pl.DataFrame] = []
    with bulk_load(conn, ["transactions", "balance_history"]):
        for month in _months(start, end):
            attempts = generator.build_month(plan.pop(month, ((), (), ()))) + fraud.pop(month, [])
            following = date(month[0] + month[1] // 12, month[1] % 12 + 1, 1)
            result = simulator.advance(attempts, min(datetime.combine(following, time()), end))
            copy_dataframe(conn, "balance_history", result.balance_history)
            totals["balance_history"] += result.balance_history.height
            txs = result.transactions
            if not txs.height:
                continue
            copy_dataframe(conn, "transactions", txs)
            totals["transactions"] += txs.height
            totals["approved"] += (txs["response_code"] == "00").sum()
            totals["fraud"] += txs["is_fraud"].sum()
            totals["disputed"] += txs["disputed"].sum()
            answers.append(txs.group_by("response_code", "decline_reason").len())
            log.info(
                "  %d-%02d %9s attempts, %.1f%% approved",
                *month,
                f"{txs.height:,}",
                100 * (txs["response_code"] == "00").mean(),
            )
    log.info("Attempts answered")
    provenance.record(
        conn,
        window_start=start.date(),
        window_end=(end - timedelta(days=1)).date(),
        window_days=days,
        simulate_code_version=provenance.code_version(),
        simulate_config_hash=provenance.config_hash(),
    )

    conn.execute(
        "CREATE TEMP TABLE new_balances (id VARCHAR PRIMARY KEY, current_balance NUMERIC) "
        "ON COMMIT DROP"
    )
    balances = simulator.card_wallets.to_frame().select("id", "current_balance")
    copy_dataframe(conn, "new_balances", balances)
    conn.execute(
        "UPDATE card_wallets c SET current_balance = n.current_balance, updated_at = now() "
        "FROM new_balances n WHERE c.id = n.id"
    )

    answered = totals["transactions"]
    return {
        "transactions": answered,
        "balance_history": totals["balance_history"],
        "approval_rate": totals["approved"] / answered if answered else 0.0,
        "fraud": totals["fraud"],
        "disputed": totals["disputed"],
        "answers": (
            pl.concat(answers, how="vertical_relaxed")
            .group_by("response_code", "decline_reason")
            .agg(pl.col("len").sum())
            .sort("len", descending=True)
            if answers
            else pl.DataFrame()
        ),
    }


def _months(start: datetime, end: datetime) -> list[tuple[int, int]]:
    """The (year, month) pairs of [start, end)."""
    months, year, month = [], start.year, start.month
    while date(year, month, 1) < end.date():
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def simulation_defaults() -> int:
    """`simulation.days` from the config."""
    config = load_simulation_config()
    return config["simulation"]["days"]
