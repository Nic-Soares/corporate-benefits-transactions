"""The star schema built from a simulated OLTP database."""

from datetime import date, datetime, timedelta

import duckdb
import polars as pl
import pytest

from src.entities import fake
from src.pipeline.etl import OLAP_TABLES, build_olap
from src.reference import build_reference_tables
from src.simulation.simulator import TransactionSimulator

TODAY = date(2026, 10, 30)


@pytest.fixture(scope="module")
def olap(build_tables, sources, transaction_generator):
    """An in-memory OLAP database and the OLTP tables it was built from."""
    make_generator = transaction_generator

    fake.seed(6, today=TODAY)
    oltp = build_tables() | build_reference_tables(sources.cnae, sources.mcc)
    generator = make_generator(oltp, days_back=45)
    end = datetime(2026, 10, 30)
    result = TransactionSimulator(oltp).run(
        [generator.generate() for _ in range(500)], end - timedelta(days=45), end
    )
    oltp |= {
        "transactions": result.transactions,
        "balance_history": result.balance_history,
        "card_wallets": result.card_wallets,
    }
    duck = duckdb.connect()
    counts = build_olap(duck, oltp)
    yield duck, oltp, counts
    duck.close()


def scalar(duck, query: str):
    return duck.sql(query).fetchall()[0][0]


def test_every_table_is_loaded(olap):
    duck, oltp, counts = olap
    assert set(counts) == set(OLAP_TABLES)
    assert counts["fact_transactions"] == oltp["transactions"].height
    assert counts["fact_balance_movements"] == oltp["balance_history"].height
    assert counts["dim_card_wallets"] == oltp["card_wallets"].height
    total = scalar(duck, "SELECT sum(amount) FROM fact_transactions")
    assert float(total) == pytest.approx(oltp["transactions"]["amount"].sum())


@pytest.mark.parametrize(
    ("column", "dimension"),
    [
        ("card_id", "dim_cards"),
        ("cardholder_id", "dim_cardholders"),
        ("company_id", "dim_companies"),
        ("program_id", "dim_card_programs"),
        ("modality_id", "dim_transaction_modalities"),
        ("card_wallet_id", "dim_card_wallets"),
        ("wallet_id", "dim_wallets"),
        ("establishment_id", "dim_establishments"),
        ("terminal_id", "dim_terminals"),
        ("acquirer_id", "dim_acquirers"),
    ],
)
def test_fact_keys_resolve(olap, column, dimension):
    duck, _, _ = olap
    dangling = scalar(
        duck,
        f"SELECT count(*) FROM fact_transactions f LEFT JOIN {dimension} d ON d.id = f.{column} "
        f"WHERE f.{column} IS NOT NULL AND d.id IS NULL",
    )
    assert dangling == 0


def test_denormalized_keys_agree(olap):
    """The keys copied into the fact match the ones the dimensions hold."""
    duck, _, _ = olap
    assert (
        scalar(
            duck,
            """
        SELECT count(*) FROM fact_transactions f
        JOIN dim_cards c ON c.id = f.card_id
        JOIN dim_cardholders h ON h.id = f.cardholder_id
        JOIN dim_terminals t ON t.id = f.terminal_id
        WHERE c.cardholder_id <> f.cardholder_id OR h.company_id <> f.company_id
           OR c.program_id <> f.program_id OR c.modality_id <> f.modality_id
           OR t.acquirer_id <> f.acquirer_id""",
        )
        == 0
    )
    assert (
        scalar(duck, "SELECT count(*) FROM fact_transactions WHERE response_message IS NULL") == 0
    )
    # every movement of a transaction points to a fact row
    assert (
        scalar(
            duck,
            """
        SELECT count(*) FROM fact_balance_movements m
        LEFT JOIN fact_transactions f ON f.id = m.transaction_id
        WHERE m.transaction_id IS NOT NULL AND f.id IS NULL""",
        )
        == 0
    )


def test_no_personal_hashes(olap):
    duck, _, _ = olap
    columns = {
        row[0] for row in duck.sql("SELECT column_name FROM information_schema.columns").fetchall()
    }
    assert not {"cpf_hash", "card_number_hash", "cnpj"} & columns
    holder_columns = {
        row[0]
        for row in duck.sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'dim_cardholders'"
        ).fetchall()
    }
    assert "name" not in holder_columns


def test_views_answer(olap):
    duck, oltp, _ = olap
    approval = duck.sql("SELECT sum(attempts) FROM v_approval_by_program").fetchall()[0][0]
    attempts = oltp["transactions"].filter(pl.col("transaction_type") != "reversal").height
    assert approval == attempts
    shares = scalar(duck, "SELECT sum(share) FROM v_declines")
    assert shares == pytest.approx(1, abs=0.01)
    for view in ["v_ticket_by_category", "v_daily", "v_wallet_flows_by_month"]:
        assert scalar(duck, f"SELECT count(*) FROM {view}") > 0
