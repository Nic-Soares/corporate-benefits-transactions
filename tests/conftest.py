import polars as pl
import pytest

from src.data_generators.entities.card_generator import CardGenerator
from src.data_generators.entities.card_wallet_generator import generate_card_wallets
from src.data_generators.entities.cardholder_generator import CardholderGenerator
from src.data_generators.entities.company_generator import CompanyGenerator
from src.data_generators.entities.establishment_generator import generate_establishments
from src.data_generators.entities.terminal_generator import generate_terminals
from src.utils.read_yamls import load_pre_populated_data

REFERENCE = load_pre_populated_data()


@pytest.fixture
def municipios_df() -> pl.DataFrame:
    """Offline stand-in for `fetch_municipios()` with the columns the generators read."""
    return pl.DataFrame(
        {
            "municipio_nome": ["São Paulo", "Recife", "Porto Alegre"],
            "uf_sigla": ["SP", "PE", "RS"],
        }
    )


@pytest.fixture
def build_tables(municipios_df):
    """Run the generators chained as the setup pipeline will, against the real config."""

    def build():
        companies = CompanyGenerator(municipios_df).generate_companies_as_dataframe(10)
        cardholders = CardholderGenerator(municipios_df).generate_cardholders_as_dataframe(
            companies, cardholders_per_company=5
        )
        cards = CardGenerator(cardholders).generate_cards_as_dataframe(80)
        card_wallets = generate_card_wallets(cards)
        establishments = generate_establishments(
            40,
            df_cnae=pl.DataFrame(
                {"subclasse_id": ["5611201", "4711302", "4731800", "4771701", "9999999"]}
            ),
            df_mcc=pl.DataFrame({"mcc_code": ["5812", "5411"]}),
            municipios_df=municipios_df,
            cnae_wallets_mapping=REFERENCE["cnae_wallets"],
        )
        terminals = generate_terminals(
            60,
            establishments,
            acquirers_df=pl.DataFrame({"id": [a["id"] for a in REFERENCE["acquirers"]]}),
            business_data=REFERENCE,
        )
        return {
            "companies": companies,
            "cardholders": cardholders,
            "cards": cards,
            "card_wallets": card_wallets,
            "establishments": establishments,
            "terminals": terminals,
        }

    return build
