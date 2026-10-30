from src.data_generators.entities.cardholder_generator import CardholderGenerator


def test_cardholder_fields(municipios_df):
    cardholder = CardholderGenerator(municipios_df).generate_cardholder("company_1").to_dict()

    assert cardholder["company_id"] == "company_1"
    assert cardholder["id"].startswith("cardholder_")
    assert (cardholder["city"], cardholder["state"]) in set(
        municipios_df.select("municipio_nome", "uf_sigla").iter_rows()
    )


def test_cardholders_dataframe(municipios_df):
    df = CardholderGenerator(municipios_df).generate_cardholders_as_dataframe(
        company_ids=["c1", "c2"], cardholders_per_company=10
    )

    assert len(df) == 20
    assert df["id"].n_unique() == 20
    assert df["company_id"].value_counts()["count"].to_list() == [10, 10]
