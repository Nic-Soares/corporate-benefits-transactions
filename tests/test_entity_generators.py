import polars as pl
import pytest

from src.data_generators.entities.card_generator import CardGenerator
from src.data_generators.entities.card_product_generator import generate_card_products
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.terminal_generator import generate_terminals


@pytest.mark.xfail(
    reason="ST-03.2: Card calls _generate_card_hash, which doesn't exist", strict=True
)
def test_cards():
    df = CardGenerator(
        cardholder_ids=["h1", "h2"], modality_ids=["VISA"]
    ).generate_cards_as_dataframe(50)

    assert len(df) == 50
    assert df["card_id"].n_unique() == 50
    assert df["cardholder_id"].is_in(["h1", "h2"]).all()
    assert (df["modality_id"] == "VISA").all()


def test_card_products():
    cards_df = pl.DataFrame({"card_id": ["card_1", "card_2", "card_3"]})
    products_df = pl.DataFrame({"product_id": ["VA", "VR"]})

    df = generate_card_products(cards_df, products_df, min_products=1, max_products=3)

    per_card = df["card_id"].value_counts()["count"]
    assert per_card.min() >= 1 and per_card.max() <= 3
    assert df["product_id"].is_in(["VA", "VR"]).all()
    # deactivated products are never "active"
    assert (
        df.filter(pl.col("deactivation_date").is_not_null())["status"]
        .is_in(["suspended", "cancelled"])
        .all()
    )


def test_establishments():
    df_cnae = pl.DataFrame({"subclasse_id": ["5611201", "4711302", "9999999"]})
    df_mcc = pl.DataFrame({"mcc_code": ["5812", "5411"]})
    df_municipalities = pl.DataFrame({"municipality_id": [1, 2], "state_id": [35, 26]})

    df = generate_establishments(
        20, df_cnae, df_mcc, df_municipalities, cnae_products_mapping={"5611": ["VR"]}
    )

    assert len(df) == 20
    assert df["establishment_id"].n_unique() == 20
    # 85% (17) take a CNAE that accepts a product
    assert (df["main_cnae"].head(17) == "5611201").all()


def test_terminals():
    establishments_df = pl.DataFrame({"establishment_id": ["EST_0", "EST_1"]})
    acquirers_df = pl.DataFrame({"name": ["Cielo", "Rede"], "acquirer_id": ["CIE", "RED"]})
    business_data = {
        "terminal_models_by_acquirer": {"Cielo": ["POS Cielo LIO"], "Rede": ["TEF Rede"]}
    }

    df = generate_terminals(30, establishments_df, acquirers_df, business_data)

    assert len(df) == 30
    assert df["establishment_id"].is_in(["EST_0", "EST_1"]).all()
    model_by_acquirer = dict(df.select("acquirer_id", "terminal_model").unique().iter_rows())
    assert model_by_acquirer == {"CIE": "POS Cielo LIO", "RED": "TEF Rede"}
