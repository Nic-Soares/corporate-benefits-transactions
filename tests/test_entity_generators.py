"""The generators, chained as the setup pipeline will run them."""

from datetime import date

import polars as pl
import pytest

from src.data_generators.entities.card_generator import CardGenerator
from src.data_generators.entities.card_product_generator import generate_card_products
from src.data_generators.entities.cardholder_generator import CardholderGenerator
from src.data_generators.entities.company_generator import CompanyGenerator
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.terminal_generator import generate_terminals
from src.data_generators.entities.transaction_generator import generate_single_transaction
from src.data_generators.providers import fake
from src.utils.read_yamls import load_business_rules

STATUS_OPTIONS = load_business_rules()["status_options"]


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


def _chain(municipios_df):
    companies = CompanyGenerator(municipios_df).generate_companies_as_dataframe(10)
    cardholders = CardholderGenerator(municipios_df).generate_cardholders_as_dataframe(
        companies, cardholders_per_company=5
    )
    cards = CardGenerator(cardholders).generate_cards_as_dataframe(80)
    products = pl.DataFrame({"id": ["VA", "VR", "VC"]})
    card_products = generate_card_products(cards, products)
    establishments = generate_establishments(
        40,
        df_cnae=pl.DataFrame({"subclasse_id": ["5611201", "4711302", "4731800", "9999999"]}),
        df_mcc=pl.DataFrame({"mcc_code": ["5812", "5411"]}),
        municipios_df=municipios_df,
        cnae_products_mapping={
            "5611": ["VR", "GF"],
            "5611201": ["VR"],
            "4711": ["VA"],
            "4731": ["VC"],
        },
    )
    terminals = generate_terminals(
        60,
        establishments,
        acquirers_df=pl.DataFrame({"id": ["CIE", "RED"], "name": ["Cielo", "Rede"]}),
        business_data={
            "terminal_models_by_acquirer": {"Cielo": ["POS Cielo LIO"], "Rede": ["TEF Rede"]}
        },
    )
    return {
        "companies": companies,
        "cardholders": cardholders,
        "cards": cards,
        "card_products": card_products,
        "establishments": establishments,
        "terminals": terminals,
    }


@pytest.fixture
def tables(municipios_df):
    fake.seed(42, today=date(2026, 10, 30))
    return _chain(municipios_df)


@pytest.mark.parametrize(
    "table",
    ["companies", "cardholders", "cards", "card_products", "establishments", "terminals"],
)
def test_columns_match_the_schema(tables, table):
    assert tables[table].columns == _schema_columns(table)


@pytest.mark.parametrize(
    ("table", "entity"),
    [
        ("cardholders", "cardholder"),
        ("cards", "card"),
        ("card_products", "card_product"),
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

    activated = t["card_products"].join(t["cards"], left_on="card_id", right_on="id")
    assert (activated["activation_date"] >= activated["issue_date"]).all()

    installed = t["terminals"].join(t["establishments"], left_on="establishment_id", right_on="id")
    assert (installed["installation_date"] >= installed["accreditation_date"]).all()

    today = date(2026, 10, 30)
    for df, column in [
        (t["companies"], "registration_date"),
        (t["cards"], "issue_date"),
        (t["card_products"], "activation_date"),
        (t["terminals"], "installation_date"),
    ]:
        assert df[column].max() <= today


def test_card_products_are_distinct_per_card(tables):
    pairs = tables["card_products"].select("card_id", "product_id")
    assert pairs.n_unique() == len(pairs)
    per_card = tables["card_products"]["card_id"].value_counts()["count"]
    assert per_card.min() >= 1 and per_card.max() <= 3


def test_establishments(tables):
    establishments = tables["establishments"]
    # 85% (34 of 40) take a CNAE that accepts a product
    assert establishments.head(34)["main_cnae"].is_in(["5611201", "4711302", "4731800"]).all()
    category = dict(establishments.select("main_cnae", "category").unique().iter_rows())
    assert category["5611201"] == "restaurant"
    assert category["4711302"] == "supermarket"
    assert category["4731800"] == "gas_station"


def test_terminals(tables):
    model_by_acquirer = dict(
        tables["terminals"].select("acquirer_id", "model").unique().iter_rows()
    )
    assert model_by_acquirer == {"CIE": "POS Cielo LIO", "RED": "TEF Rede"}
    assert dict(tables["terminals"].select("model", "type").unique().iter_rows()) == {
        "POS Cielo LIO": "POS",
        "TEF Rede": "TEF",
    }


def test_transaction(tables):
    tx = generate_single_transaction(tables["card_products"], tables["terminals"])

    assert tx["card_id"] in tables["cards"]["id"]
    owned = tables["card_products"].filter(card_id=tx["card_id"])["product_id"]
    assert tx["product_id"] in owned
    terminal = tables["terminals"].filter(id=tx["terminal_id"]).row(0, named=True)
    assert tx["establishment_id"] == terminal["establishment_id"]
    assert 0 <= tx["amount"] <= 500


def test_same_seed_same_data(municipios_df):
    def run():
        fake.seed(7, today=date(2026, 10, 30))
        tables = _chain(municipios_df)
        txs = [
            generate_single_transaction(tables["card_products"], tables["terminals"])
            for _ in range(5)
        ]
        return tables, txs

    (first, first_txs), (second, second_txs) = run(), run()
    for name in first:
        assert first[name].equals(second[name]), name
    assert first_txs == second_txs
