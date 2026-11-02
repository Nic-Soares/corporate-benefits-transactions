"""`simulate`: purchase attempts answered by the issuer, written to the OLTP database."""

import logging
from datetime import date, datetime, time, timedelta

import psycopg

from src.data_generators.providers import fake
from src.infrastructure.database.postgres_manager import (
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
    attempts = [generator.generate() for _ in range(n_attempts)]
    fraud = FraudGenerator(generator).generate(round(n_attempts * FRAUD["share_of_attempts"]))
    attempts += fraud
    log.info("%s attempts generated (%s in fraud incidents)", f"{len(attempts):,}", len(fraud))

    end = datetime.combine(today, time())
    result = TransactionSimulator(tables).run(
        attempts, end - timedelta(days=days), end, generator.opening_balances()
    )
    log.info("Attempts answered")
    provenance.record(
        conn,
        window_start=(end - timedelta(days=days)).date(),
        window_end=(end - timedelta(days=1)).date(),
        window_days=days,
        simulate_code_version=provenance.code_version(),
        simulate_config_hash=provenance.config_hash(),
    )

    copy_dataframe(conn, "transactions", result.transactions)
    copy_dataframe(conn, "balance_history", result.balance_history)
    conn.execute(
        "CREATE TEMP TABLE new_balances (id VARCHAR PRIMARY KEY, current_balance NUMERIC) "
        "ON COMMIT DROP"
    )
    copy_dataframe(conn, "new_balances", result.card_wallets.select("id", "current_balance"))
    conn.execute(
        "UPDATE card_wallets c SET current_balance = n.current_balance, updated_at = now() "
        "FROM new_balances n WHERE c.id = n.id"
    )

    answers = (
        result.transactions.group_by("response_code", "decline_reason")
        .len()
        .sort("len", descending=True)
    )
    return {
        "transactions": result.transactions.height,
        "balance_history": result.balance_history.height,
        "approval_rate": (result.transactions["response_code"] == "00").mean(),
        "fraud": result.transactions["is_fraud"].sum(),
        "disputed": result.transactions["disputed"].sum(),
        "answers": answers,
    }


def simulation_defaults() -> int:
    """`simulation.days` from the config."""
    config = load_simulation_config()
    return config["simulation"]["days"]
