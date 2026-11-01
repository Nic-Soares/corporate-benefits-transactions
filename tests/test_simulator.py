"""The simulator over generated tables: answers, ledger and time order."""

from datetime import date, datetime, timedelta

import polars as pl
import pytest

from src.data_generators.providers import fake
from src.pipeline.reference import build_reference_tables
from src.processors import transaction_simulator
from src.processors.transaction_simulator import TransactionSimulator, credit_moments

TODAY = date(2026, 10, 30)
END = datetime(2026, 10, 30)
START = END - timedelta(days=45)


@pytest.fixture
def world(build_tables, sources):
    fake.seed(5, today=TODAY)
    tables = build_tables() | build_reference_tables(sources.cnae, sources.mcc)
    return tables


def simulate(world, transaction_generator, attempts: int = 800):
    generator = transaction_generator(world, days_back=45)
    txs = [generator.generate() for _ in range(attempts)]
    return TransactionSimulator(world).run(txs, START, END)


def test_credit_moments():
    moments = credit_moments(datetime(2026, 8, 15), datetime(2026, 10, 30))
    assert moments == [datetime(2026, 9, 1, 6), datetime(2026, 10, 1, 6)]


def test_answers(world, transaction_generator, sources):
    result = simulate(world, transaction_generator)
    tx = result.transactions
    codes = set(build_reference_tables(sources.cnae, sources.mcc)["response_codes"]["id"])
    assert set(tx["response_code"]) <= codes

    approved = tx.filter(response_code="00")
    assert approved["card_wallet_id"].is_not_null().all()
    assert approved["authorization_code"].str.len_chars().eq(6).all()
    assert approved["decline_reason"].is_null().all()
    declined = tx.filter(pl.col("response_code") != "00")
    assert declined["decline_reason"].is_not_null().all()
    assert declined["authorization_code"].is_null().all()
    # most attempts pass; lack of balance is the commonest decline
    assert 0.6 < len(approved) / len(tx) < 0.97
    assert tx["date"].is_sorted()


def test_ledger(world, transaction_generator):
    result = simulate(world, transaction_generator)
    history = result.balance_history.sort("card_wallet_id", "operation_date", "id")

    # each movement does its math, and starts where the previous one ended
    sign = pl.when(pl.col("operation_type").is_in(["credit", "reversal"])).then(1).otherwise(-1)
    error = pl.col("previous_balance") + sign * pl.col("operation_amount")
    assert history.select((error - pl.col("posterior_balance")).abs().max()).item() < 0.005
    chained = history.with_columns(
        before=pl.col("posterior_balance").shift().over("card_wallet_id")
    ).filter(pl.col("before").is_not_null())
    assert (chained["before"] == chained["previous_balance"]).all()
    assert (history["posterior_balance"] >= 0).all()

    # one movement per approved attempt; the final balance is the last movement
    approved = result.transactions.filter(response_code="00")
    moved = history.filter(pl.col("transaction_id").is_not_null())
    assert sorted(moved["transaction_id"]) == sorted(approved["id"])
    last = history.group_by("card_wallet_id").agg(pl.col("posterior_balance").last())
    final = result.card_wallets.join(last, left_on="id", right_on="card_wallet_id")
    assert (final["current_balance"] == final["posterior_balance"]).all()


def test_limits_hold(world, transaction_generator):
    result = simulate(world, transaction_generator, attempts=1500)
    per_day = (
        result.transactions.filter(response_code="00", transaction_type="purchase")
        .group_by("card_wallet_id", pl.col("date").dt.date())
        .len()
        .join(
            world["card_wallets"].select("id", "daily_count_limit"),
            left_on="card_wallet_id",
            right_on="id",
        )
    )
    assert per_day.filter(
        pl.col("daily_count_limit") > 0, pl.col("len") > pl.col("daily_count_limit")
    ).is_empty()


def test_reversals(world, transaction_generator, monkeypatch):
    monkeypatch.setitem(transaction_simulator.SIMULATION, "reversal_ratio", 0.3)
    tx = simulate(world, transaction_generator).transactions
    reversals = tx.filter(transaction_type="reversal")
    assert reversals.height > 0
    originals = reversals.join(tx, left_on="related_transaction_id", right_on="id", suffix="_o")
    assert originals.height == reversals.height
    assert (originals["response_code_o"] == "00").all()
    assert (originals["transaction_type_o"] == "purchase").all()
    assert (originals["date"] > originals["date_o"]).all()
    assert (originals["amount"] == originals["amount_o"]).all()


def test_gives_up_after_insufficient_balance(world, transaction_generator, monkeypatch):
    """With a give-up share of 1, after a decline for balance the cardholder doesn't
    try that option (or kind of place, on a brand card) again until the next credit."""
    monkeypatch.setitem(transaction_simulator.SIMULATION, "give_up_after_insufficient_balance", 1)
    tx = simulate(world, transaction_generator, attempts=1500).transactions
    credits = credit_moments(START, END)
    category = world["establishments"].select(pl.col("id").alias("establishment_id"), "category")
    intent = pl.coalesce("wallet_option", "category")
    period = pl.col("date").map_elements(
        lambda d: sum(d >= c for c in credits), return_dtype=pl.Int64
    )
    purchases = (
        tx.filter(~pl.col("is_fraud"), pl.col("transaction_type") != "reversal")
        .join(category, on="establishment_id")
        .with_columns(period=period, intent=intent)
    )
    for key, rows in purchases.group_by("card_id", "intent", "period"):
        reasons = rows.sort("date")["decline_reason"].to_list()
        if "insufficient_balance" in reasons:
            assert reasons.index("insufficient_balance") == len(reasons) - 1, key


def test_same_seed_same_simulation(build_tables, sources, transaction_generator):
    def run():
        fake.seed(9, today=TODAY)
        world = build_tables() | build_reference_tables(sources.cnae, sources.mcc)
        return simulate(world, transaction_generator, attempts=300)

    first, second = run(), run()
    assert first.transactions.equals(second.transactions)
    assert first.balance_history.equals(second.balance_history)
