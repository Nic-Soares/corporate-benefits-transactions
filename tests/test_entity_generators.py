"""The generators, chained as the setup pipeline will run them."""

from datetime import date

import polars as pl
import pytest

from src.data_generators.entities.transaction_generator import generate_single_transaction
from src.data_generators.providers import fake
from src.utils.read_yamls import load_business_rules, load_pre_populated_data

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


def test_establishments(tables):
    establishments = tables["establishments"]
    # 85% (34 of 40) take a CNAE that accepts a wallet
    accepting = ["5611201", "4711302", "4731800", "4771701"]
    assert establishments.head(34)["main_cnae"].is_in(accepting).all()
    category = dict(establishments.select("main_cnae", "category").unique().iter_rows())
    assert category["5611201"] == "restaurant"
    assert category["4711302"] == "supermarket"
    assert category["4731800"] == "mobility"
    assert category["4771701"] == "health"


def test_terminals(tables):
    """Model and type come from the acquirer's list in pre_populated_data.yaml."""
    allowed = {
        (acquirer, model["model"], model["type"])
        for acquirer, models in REFERENCE["terminal_models_by_acquirer"].items()
        for model in models
    }
    used = set(tables["terminals"].select("acquirer_id", "model", "type").iter_rows())
    assert used <= allowed
    assert len({acquirer for acquirer, _, _ in used}) > 1


def test_transaction(tables):
    cards, card_wallets = tables["cards"], tables["card_wallets"]
    txs = [generate_single_transaction(cards, card_wallets, tables["terminals"]) for _ in range(50)]

    for tx in txs:
        card = cards.filter(id=tx["card_id"]).row(0, named=True)
        if card["modality_id"] == "OWN":
            # the cardholder picked one of the card's wallets
            held = card_wallets.filter(card_id=tx["card_id"])["wallet_id"]
            assert tx["wallet_id"] in held
        else:
            # the issuer routes brand cards by MCC later
            assert tx["wallet_id"] is None
        terminal = tables["terminals"].filter(id=tx["terminal_id"]).row(0, named=True)
        assert tx["establishment_id"] == terminal["establishment_id"]
        assert 0 <= tx["amount"] <= 500
        expected = (
            {"ok", "wrong"} if tx["capture_type"] in ("CHIP", "MAG_STRIPE") else {"not_required"}
        )
        assert tx["pin_status"] in expected


def test_same_seed_same_data(build_tables):
    def run():
        fake.seed(7, today=date(2026, 10, 30))
        tables = build_tables()
        txs = [
            generate_single_transaction(
                tables["cards"], tables["card_wallets"], tables["terminals"]
            )
            for _ in range(5)
        ]
        return tables, txs

    (first, first_txs), (second, second_txs) = run(), run()
    for name in first:
        assert first[name].equals(second[name]), name
    assert first_txs == second_txs
