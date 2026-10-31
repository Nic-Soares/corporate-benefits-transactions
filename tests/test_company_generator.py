import polars as pl

from src.data_generators.entities.company_generator import COMPANY_SEGMENTS, CompanyGenerator


def test_holding_and_branch(municipios_df):
    generator = CompanyGenerator(municipios_df=municipios_df)

    holding = generator.generate_company(parent_id=None)
    branch = generator.generate_company(parent_id=holding.id)

    assert holding.to_dict()["parent_id"] is None
    assert branch.to_dict()["parent_id"] == holding.id


def test_companies_dataframe(municipios_df):
    df = CompanyGenerator(municipios_df=municipios_df).generate_companies_as_dataframe(
        n_companies=100
    )

    assert len(df) == 100
    assert df["id"].n_unique() == 100
    assert df["cnpj"].n_unique() == 100
    # 20% holdings by default; every branch points to one of them
    holdings = df.filter(pl.col("parent_id").is_null())["id"]
    branches = df.filter(pl.col("parent_id").is_not_null())
    assert len(holdings) == 20
    assert branches["parent_id"].is_in(holdings.implode()).all()


def test_segments(municipios_df):
    df = CompanyGenerator(municipios_df=municipios_df).generate_companies_as_dataframe(
        n_companies=100
    )
    assert df["segment"].is_in(list(COMPANY_SEGMENTS)).all()
    # a branch belongs to its holding's segment
    pairs = df.join(df, left_on="parent_id", right_on="id", suffix="_holding")
    assert (pairs["segment"] == pairs["segment_holding"]).all()
