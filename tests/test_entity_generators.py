"""The generators, chained as the setup pipeline will run them."""

from datetime import date, datetime, timedelta

import polars as pl
import pytest

from src.data_generators.entities.establishment_generator import CATEGORIES, mcc_for
from src.data_generators.providers import fake
from src.utils.read_yamls import (
    load_business_rules,
    load_pre_populated_data,
    load_validation_rules,
)

STATUS_OPTIONS = load_business_rules()["status_options"]
REFERENCE = load_pre_populated_data()


def _schema_columns(table: str) -> list[str]:
    """Columns of an OLTP table, without the audit columns the database fills."""
    from pathlib import Path

    sql = (Path(__file__).parent.parent / "database/oltp_postgres/oltp_schema.sql").read_text()
    body = sql.split(f"CREATE TABLE IF NOT EXISTS {table} (")[1].split(");")[0]
    columns = [line.split()[0] for line in body.strip().splitlines() if line.strip()]
    return [
        c
        for c in columns
        if c.islower() and c not in ("created_at", "updated_at", "primary", "foreign")
    ]


@pytest.fixture
def tables(build_tables):
    fake.seed(42, today=date(2026, 10, 30))
    return build_tables()


@pytest.mark.parametrize(
    "table",
    ["companies", "cardholders", "cards", "card_wallets", "establishments", "terminals"],
)
def test_columns_match_the_schema(tables, table):
    assert tables[table].columns == _schema_columns(table)


@pytest.mark.parametrize(
    ("table", "entity"),
    [
        ("cardholders", "cardholder"),
        ("cards", "card"),
        ("card_wallets", "card_wallet"),
        ("establishments", "establishment"),
        ("terminals", "terminal"),
    ],
)
def test_statuses_are_valid(tables, table, entity):
    assert tables[table]["status"].is_in(STATUS_OPTIONS[entity]).all()


def test_ids_are_unique(tables):
    for df in tables.values():
        assert df["id"].n_unique() == len(df)


def test_dates_follow_their_parents(tables):
    t = tables
    hired = t["cardholders"].join(t["companies"], left_on="company_id", right_on="id")
    assert (hired["admission_date"] >= hired["registration_date"]).all()

    issued = t["cards"].join(t["cardholders"], left_on="cardholder_id", right_on="id")
    assert (issued["issue_date"] >= issued["admission_date"]).all()
    assert (t["cards"]["expiration_date"] > t["cards"]["issue_date"]).all()

    activated = t["card_wallets"].join(t["cards"], left_on="card_id", right_on="id")
    assert (activated["activation_date"] >= activated["issue_date"]).all()

    installed = t["terminals"].join(t["establishments"], left_on="establishment_id", right_on="id")
    assert (installed["installation_date"] >= installed["accreditation_date"]).all()

    today = date(2026, 10, 30)
    for df, column in [
        (t["companies"], "registration_date"),
        (t["cards"], "issue_date"),
        (t["card_wallets"], "activation_date"),
        (t["terminals"], "installation_date"),
    ]:
        assert df[column].max() <= today


def test_card_wallets_follow_the_program(tables):
    """Each card holds exactly the wallets of its program, once each."""
    wallets_by_program = {p["id"]: set(p["wallets"]) for p in REFERENCE["card_programs"]}
    held = tables["card_wallets"].group_by("card_id").agg(pl.col("wallet_id"))
    cards = tables["cards"].join(held, left_on="id", right_on="card_id")
    for program_id, wallet_ids in cards.select("program_id", "wallet_id").iter_rows():
        assert len(wallet_ids) == len(set(wallet_ids))
        assert set(wallet_ids) == wallets_by_program[program_id]


def test_card_network_follows_the_program(tables):
    """3-party programs run on OWN; the 4-party program on one of its brands."""
    programs = {p["id"]: p for p in REFERENCE["card_programs"]}
    for program_id, modality_id in tables["cards"].select("program_id", "modality_id").iter_rows():
        program = programs[program_id]
        if program["network_type"] == "proprietary_network":
            assert modality_id == "OWN"
        else:
            assert modality_id in program["brands"]
    assert tables["cards"]["program_id"].n_unique() > 3


def test_cards_follow_the_company_bundle(tables):
    """A company's cardholders hold the same programs, one card each."""
    bundles = [set(b["programs"]) for b in fake.SETTINGS["program_bundles"]]
    cards = tables["cards"].join(
        tables["cardholders"].select("id", "company_id"), left_on="cardholder_id", right_on="id"
    )
    per_holder = cards.group_by("cardholder_id", "company_id").agg(pl.col("program_id"))
    for company_id, group in per_holder.group_by("company_id"):
        programs = [tuple(sorted(p)) for p in group["program_id"].to_list()]
        assert len(set(programs)) == 1, company_id
        assert len(programs[0]) == len(set(programs[0]))
        assert set(programs[0]) in bundles


def test_card_wallets_settings(tables):
    """Credit in the wallet's range, balance a share of it, limits from the config."""
    settings = fake.SETTINGS["wallets"]
    for row in tables["card_wallets"].iter_rows(named=True):
        wallet = settings[row["wallet_id"]]
        credit = wallet["monthly_credit"]
        assert credit["min"] - 10 <= row["monthly_credit"] <= credit["max"] + 10
        assert 0 <= row["current_balance"] <= row["monthly_credit"]
        assert row["daily_limit"] == wallet["daily_limit"]
        assert row["daily_count_limit"] == wallet["daily_count_limit"]


def test_establishments(tables):
    """The MCC is the CNAE's; the category is the one whose CNAE prefixes match."""
    for row in tables["establishments"].iter_rows(named=True):
        assert row["mcc_code"] == mcc_for(row["main_cnae"])
        prefixes = CATEGORIES[row["category"]]["cnae"]
        assert any(row["main_cnae"].startswith(prefix) for prefix in prefixes)
    assert tables["establishments"]["category"].n_unique() > 5
    # 9999999 belongs to no category
    assert "9999999" not in tables["establishments"]["main_cnae"].to_list()


def test_terminals(tables):
    """Each establishment has a terminal of its kind, of an acquirer that has that model."""
    terminals = tables["terminals"].join(
        tables["establishments"].select("id", "category"),
        left_on="establishment_id",
        right_on="id",
    )
    assert set(terminals["establishment_id"]) == set(tables["establishments"]["id"])
    allowed = {
        (acquirer, model["model"], model["type"])
        for acquirer, models in REFERENCE["terminal_models_by_acquirer"].items()
        for model in models
    }
    for row in terminals.iter_rows(named=True):
        assert (row["acquirer_id"], row["model"], row["type"]) in allowed
        category = CATEGORIES[row["category"]]
        if category.get("atm"):
            assert row["type"] == "ATM"
        elif category.get("online"):
            assert row["type"] == "ECOMMERCE"
        else:
            assert row["type"] in ("POS", "TEF")


@pytest.fixture
def transactions(tables, transaction_generator):
    generator = transaction_generator(tables)
    return pl.DataFrame([generator.generate() for _ in range(2000)])


def test_transaction_columns(transactions):
    assert transactions.columns == _schema_columns("transactions")


def test_transactions_are_coherent(tables, transactions):
    cards = tables["cards"].select("id", "modality_id", "card_type")
    terminals = tables["terminals"].select(
        pl.col("id").alias("terminal_id"), "establishment_id", pl.col("type").alias("terminal_type")
    )
    categories = tables["establishments"].select(pl.col("id").alias("establishment_id"), "category")
    tx = (
        transactions.join(cards, left_on="card_id", right_on="id")
        .join(terminals, on=["terminal_id", "establishment_id"])
        .join(categories, on="establishment_id")
    )
    assert len(tx) == len(transactions)  # the terminal belongs to the establishment

    own = tx.filter(modality_id="OWN")
    assert own["wallet_option"].is_in(["FOOD", "MEAL", "OTHERS"]).all()
    assert tx.filter(pl.col("modality_id") != "OWN")["wallet_option"].is_null().all()
    # cash withdrawals: at cash machines only
    assert (tx["transaction_type"] == "withdrawal").eq(tx["category"] == "atm").all()
    # the routed wallet and the answer come later
    assert tx["card_wallet_id"].is_null().all() and tx["response_code"].is_null().all()
    # captures the terminal takes; a virtual card never uses the physical ones
    supported = load_validation_rules()["infrastructure_validations"]["capture_type_support"][
        "supported_by_terminal_type"
    ]
    physical = tx.filter(card_type="physical")
    for terminal_type, capture in physical.select("terminal_type", "capture_type").iter_rows():
        assert capture in supported[terminal_type]
    assert not tx.filter(card_type="virtual")["capture_type"].is_in(["CHIP", "CONTACTLESS"]).any()
    pin = tx["capture_type"].is_in(["CHIP", "MAG_STRIPE"])
    assert tx.filter(pin)["pin_status"].is_in(["ok", "wrong"]).all()
    assert (tx.filter(~pin)["pin_status"] == "not_required").all()
    assert tx["nsu"].str.len_chars().eq(12).all()


def test_transactions_look_like_the_market(tables, transactions):
    """Lunch and evening peaks, quiet nights, small tickets, uneven use across cards."""
    hours = transactions["date"].dt.hour()
    assert (hours.is_between(11, 13).mean()) > 3 * hours.is_between(0, 5).mean()
    assert hours.is_between(0, 5).mean() < 0.05

    purchases = transactions.filter(transaction_type="purchase")["amount"]
    assert 15 <= purchases.median() <= 90
    assert purchases.quantile(0.9) > 2 * purchases.median()

    # uneven use: big credits and spenders buy far more than small credits and savers
    per_card = transactions["card_id"].value_counts()["count"]
    assert per_card.max() > 3 * per_card.median()
    assert per_card.min() < per_card.median() / 2
    # within the window, before the reference day
    today = datetime(2026, 10, 30)
    assert transactions["date"].max() < today
    assert transactions["date"].min() >= today - timedelta(days=30)


def test_same_seed_same_data(build_tables, transaction_generator):
    def run():
        fake.seed(7, today=date(2026, 10, 30))
        tables = build_tables()
        generator = transaction_generator(tables)
        return tables, [generator.generate() for _ in range(5)]

    (first, first_txs), (second, second_txs) = run(), run()
    for name in first:
        assert first[name].equals(second[name]), name
    assert first_txs == second_txs
