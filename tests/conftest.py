import polars as pl
import pytest

from src.data_generators.entities.card_generator import CardGenerator
from src.data_generators.entities.card_wallet_generator import generate_card_wallets
from src.data_generators.entities.cardholder_generator import CardholderGenerator
from src.data_generators.entities.company_generator import CompanyGenerator
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.terminal_generator import generate_terminals
from src.data_generators.entities.transaction_generator import TransactionGenerator
from src.pipeline.sources import Sources
from src.utils.read_yamls import load_pre_populated_data

REFERENCE = load_pre_populated_data()


@pytest.fixture(scope="session")
def municipios_df() -> pl.DataFrame:
    """Offline stand-in for `fetch_municipios()` with the columns the generators read."""
    return pl.DataFrame(
        {
            "municipio_nome": ["São Paulo", "Recife", "Porto Alegre"],
            "uf_sigla": ["SP", "PE", "RS"],
        }
    )


# One or more CNAE subclasses per establishment category, and one outside them
CNAE_SUBCLASSES = [
    *["4711302", "4711301", "4691500"],
    *["4721102", "4722901", "4724500"],
    *["5611201", "5611203", "5612100"],
    *["4731800", "4520001", "4771701", "4774100", "9313100"],
    *["4751201", "4761003", "8599604", "4781400", "4772500"],
    *["4923002", "6319400", "6422100", "9999999"],
]


@pytest.fixture(scope="session")
def build_tables(municipios_df):
    """Run the generators chained as the setup pipeline will, against the real config."""

    def build():
        companies = CompanyGenerator(municipios_df).generate_companies_as_dataframe(10)
        cardholders = CardholderGenerator(municipios_df).generate_cardholders_as_dataframe(
            companies, scale=0.02
        )
        cards = CardGenerator(cardholders).generate_cards_as_dataframe()
        card_wallets = generate_card_wallets(cards, cardholders)
        establishments = generate_establishments(
            120,
            df_cnae=pl.DataFrame({"subclasse_id": CNAE_SUBCLASSES}),
            municipios_df=municipios_df,
        )
        terminals = generate_terminals(160, establishments, business_data=REFERENCE)
        return {
            "companies": companies,
            "cardholders": cardholders,
            "cards": cards,
            "card_wallets": card_wallets,
            "establishments": establishments,
            "terminals": terminals,
        }

    return build


@pytest.fixture(scope="session")
def transaction_generator():
    """A TransactionGenerator over the tables `build_tables` returns."""

    def make(tables, days_back: int = 30):
        return TransactionGenerator(
            tables["cards"],
            tables["cardholders"],
            tables["card_wallets"],
            tables["establishments"],
            tables["terminals"],
            days_back=days_back,
        )

    return make


@pytest.fixture(scope="session")
def sources(municipios_df) -> Sources:
    """Offline stand-in for `fetch_sources()`: CNAE and MCC rows in the shape the setup reads."""
    cnae = pl.DataFrame(
        {
            "classe_id": [f"{code[:4]}0" for code in CNAE_SUBCLASSES],
            "classe": [f"Class {code[:4]}" for code in CNAE_SUBCLASSES],
            "subclasse_id": CNAE_SUBCLASSES,
            "subclasse": [f"Subclass {code}" for code in CNAE_SUBCLASSES],
        }
    )
    mcc = pl.DataFrame({"mcc_code": ["5411", "5812"], "description": ["Grocery", "Restaurants"]})
    return Sources(cnae=cnae, mcc=mcc, municipios=municipios_df)
