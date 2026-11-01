"""Fraud scenarios: each leaves the signature a fraud team looks for."""

from datetime import date, datetime, timedelta

import polars as pl
import pytest

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.entities.fraud_generator import WALLET_CAPTURES, FraudGenerator
from src.data_generators.providers import fake
from src.processors import disputes

TODAY = date(2026, 10, 30)


@pytest.fixture
def setting(build_tables, transaction_generator):
    fake.seed(4, today=TODAY)
    tables = build_tables()
    generator = transaction_generator(tables, days_back=90)
    return tables, FraudGenerator(generator)


def incident(fraud: FraudGenerator, scenario: str) -> list[dict]:
    """The first non-empty incident of the scenario (victims are drawn at random)."""
    for _ in range(50):
        if attempts := getattr(fraud, scenario)():
            return attempts
    pytest.skip(f"no eligible victim for {scenario} in this small world")


def where(tables, attempts) -> pl.DataFrame:
    """Attempts with the cardholder's state and the shop's state and category."""
    homes = tables["cards"].join(
        tables["cardholders"].select(pl.col("id").alias("cardholder_id"), home="state"),
        on="cardholder_id",
    )
    shops = tables["establishments"].select(
        pl.col("id").alias("establishment_id"), shop="state", category="category"
    )
    return (
        pl.DataFrame(attempts)
        .join(
            homes.select(
                pl.col("id").alias("card_id"), "home", "issue_date", "modality_id", "card_type"
            ),
            on="card_id",
        )
        .join(shops, on="establishment_id")
    )


def test_account_takeover_wallet(setting):
    tables, fraud = setting
    df = where(tables, incident(fraud, "account_takeover_wallet"))
    assert df["is_fraud"].all() and (df["fraud_scenario"] == "account_takeover_wallet").all()
    assert df["capture_type"].is_in(WALLET_CAPTURES).all()
    assert (df["shop"] != df["home"]).all()
    assert df["card_id"].n_unique() == 1
    assert df["date"].max() - df["date"].min() <= timedelta(hours=8)


def test_card_not_present(setting):
    tables, fraud = setting
    df = where(tables, incident(fraud, "card_not_present"))
    assert (df["capture_type"] == "ECOMMERCE").all()
    assert (df["modality_id"] != "OWN").all()  # brand cards: the number works online
    assert df["category"].map_elements(lambda c: CATEGORIES[c].get("online", False)).all()


def test_intercepted_card(setting):
    tables, fraud = setting
    df = where(tables, incident(fraud, "intercepted_card"))
    assert (df["card_type"] == "physical").all()
    assert (df["shop"] != df["home"]).all()
    first = df["date"].min()
    assert first.date() - df["issue_date"][0] <= timedelta(days=6)
    # no PIN known: contactless, or chip with a wrong PIN
    chip = df.filter(capture_type="CHIP")
    assert (chip["pin_status"] == "wrong").all()
    assert df["capture_type"].is_in(["CHIP", "CONTACTLESS"]).all()


def test_point_of_compromise(setting):
    tables, fraud = setting
    df = where(tables, incident(fraud, "point_of_compromise"))
    visits, misuse = df.filter(~pl.col("is_fraud")), df.filter(pl.col("is_fraud"))
    # the legit visits share one terminal: the point of compromise
    assert visits["terminal_id"].n_unique() == 1
    assert (misuse["capture_type"] == "MAG_STRIPE").all()
    assert (misuse["shop"] != misuse["home"]).all()
    first_visit = visits.group_by("card_id").agg(visit=pl.col("date").min())
    later = misuse.join(first_visit, on="card_id")
    assert (later["date"] >= later["visit"] + timedelta(days=3)).all()


def test_generate_reaches_the_share(setting):
    _, fraud = setting
    attempts = fraud.generate(30)
    assert sum(a["is_fraud"] for a in attempts) >= 30
    assert all(fraud.start <= a["date"] < fraud.end for a in attempts)


def test_disputes(monkeypatch):
    monkeypatch.setitem(disputes.FRAUD, "report_ratio", 1.0)
    monkeypatch.setitem(disputes.FRAUD, "friendly_disputes_per_fraud_dispute", 0.5)
    rows = [
        # card_a: two approved frauds and a declined one
        ("t1", "card_a", "00", True, "purchase", "not_required"),
        ("t2", "card_a", "00", True, "purchase", "not_required"),
        ("t3", "card_a", "51", True, "purchase", "not_required"),
        # legit purchases: only the approved ones with a PIN can be contested by mistake
        ("t4", "card_b", "00", False, "purchase", "ok"),
        ("t5", "card_b", "00", False, "purchase", "not_required"),
        ("t6", "card_b", "51", False, "purchase", "ok"),
    ]
    df = pl.DataFrame(
        rows,
        schema=["id", "card_id", "response_code", "is_fraud", "transaction_type", "pin_status"],
        orient="row",
    )
    disputed = set(disputes.mark_disputes(df).filter("disputed")["id"])
    assert disputed == {"t1", "t2", "t4"}


def test_names_are_brazilian(build_tables):
    fake.seed(1, today=TODAY)
    tables = build_tables()
    for name in tables["companies"]["name"]:
        assert name.endswith(("Ltda", "S.A."))
    for trade_name, category in (
        tables["establishments"].select("trade_name", "category").iter_rows()
    ):
        assert any(word in trade_name for word in CATEGORIES[category]["names"])


def test_simulated_fraud_is_labeled(build_tables, sources, transaction_generator):
    from src.pipeline.reference import build_reference_tables
    from src.processors.transaction_simulator import TransactionSimulator

    fake.seed(4, today=TODAY)
    world = build_tables() | build_reference_tables(sources.cnae, sources.mcc)
    generator = transaction_generator(world, days_back=60)
    attempts = [generator.generate() for _ in range(600)] + FraudGenerator(generator).generate(40)
    end = datetime(2026, 10, 30)
    tx = TransactionSimulator(world).run(attempts, end - timedelta(days=60), end).transactions

    assert tx["is_fraud"].sum() >= 40
    assert tx.filter("is_fraud")["fraud_scenario"].is_not_null().all()
    assert tx.filter(~pl.col("is_fraud"))["fraud_scenario"].is_null().all()
    # only approved transactions are contested; fraud is never reversed
    assert (tx.filter("disputed")["response_code"] == "00").all()
    reversed_ids = tx.filter(transaction_type="reversal")["related_transaction_id"]
    assert not tx.filter(pl.col("id").is_in(reversed_ids.implode()))["is_fraud"].any()
