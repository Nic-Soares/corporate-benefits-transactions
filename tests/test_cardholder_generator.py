from datetime import date

import polars as pl

from src.data_generators.entities.cardholder_generator import CardholderGenerator
from src.data_generators.entities.company_generator import COMPANY_SEGMENTS


def test_cardholder_fields(municipios_df):
    cardholder = CardholderGenerator(municipios_df).generate_cardholder("company_1").to_dict()

    assert cardholder["company_id"] == "company_1"
    assert cardholder["id"].startswith("cardholder_")
    assert len(cardholder["cpf_hash"]) == 64
    assert (cardholder["city"], cardholder["state"]) in set(
        municipios_df.select("municipio_nome", "uf_sigla").iter_rows()
    )


def test_cardholders_dataframe(municipios_df):
    companies_df = pl.DataFrame(
        {
            "id": ["c1", "c2"],
            "segment": ["SME", "Middle"],
            "registration_date": [date(2020, 1, 1), date(2023, 6, 1)],
        }
    )

    df = CardholderGenerator(municipios_df).generate_cardholders_as_dataframe(companies_df)

    assert df["id"].n_unique() == len(df)
    # as many as the segment says
    counts = dict(df["company_id"].value_counts().iter_rows())
    for company_id, segment in [("c1", "SME"), ("c2", "Middle")]:
        size = COMPANY_SEGMENTS[segment]["cardholders"]
        assert size["min"] <= counts[company_id] <= size["max"]
    # hired after the company was registered
    hired = df.join(companies_df, left_on="company_id", right_on="id")
    assert (hired["admission_date"] >= hired["registration_date"]).all()
