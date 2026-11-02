import random
from datetime import date

import polars as pl

from src.entities import fake

# Segment → {weight, cardholders: {min, max}} (simulation.yaml)
COMPANY_SEGMENTS: dict[str, dict] = fake.SETTINGS["company_segments"]


class Company:
    """A client company (the employer that buys the benefits)."""

    def __init__(
        self,
        segment: str,
        municipio_data: dict[str, str],
        parent_id: str | None = None,
        registered_after: date | None = None,
    ) -> None:
        self.id: str = fake.new_id("comp")
        # With a parent_id it's a branch; without one, a holding
        self.parent_id: str | None = parent_id
        self.cnpj: str = fake.brazil.cnpj()
        self.name, self.trade_name = fake.company_names()
        self.segment: str = segment
        self.city: str = municipio_data["municipio_nome"]
        self.state: str = municipio_data["uf_sigla"]
        self.status: str = fake.status("company")
        self.registration_date: date = fake.date_in_range(
            "company_registration", not_before=registered_after
        )

    def to_dict(self) -> dict[str, str | date | None]:
        """Columns of the `companies` table."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "cnpj": self.cnpj,
            "name": self.name,
            "trade_name": self.trade_name,
            "segment": self.segment,
            "city": self.city,
            "state": self.state,
            "status": self.status,
            "registration_date": self.registration_date,
        }


class CompanyGenerator:
    """Generates companies located in real IBGE municipalities."""

    def __init__(self, municipios_df: pl.DataFrame) -> None:
        """`municipios_df` needs `municipio_nome` and `uf_sigla`; with `gdp`,
        companies follow the economy: big employers sit where the GDP is."""
        self.municipios = fake.Municipalities(municipios_df, weight="gdp")

    def generate_company(
        self,
        parent_id: str | None = None,
        segment: str | None = None,
        registered_after: date | None = None,
    ) -> Company:
        """A branch keeps its holding's segment and is registered after it; a
        holding draws a segment by weight."""
        weights = {name: s["weight"] for name, s in COMPANY_SEGMENTS.items()}
        return Company(
            segment=segment or fake.weighted_key(weights),
            municipio_data=self.municipios.draw(),
            parent_id=parent_id,
            registered_after=registered_after,
        )

    def generate_hierarchical_companies(
        self, n_companies: int, holding_ratio: float = 0.2
    ) -> list[Company]:
        """Holdings (`holding_ratio` of the total, at least one) and branches under them."""
        n_holdings = max(int(n_companies * holding_ratio), 1)
        holdings = [self.generate_company() for _ in range(n_holdings)]
        branches = []
        for _ in range(n_companies - n_holdings):
            holding = random.choice(holdings)
            branches.append(
                self.generate_company(holding.id, holding.segment, holding.registration_date)
            )
        return holdings + branches

    def generate_companies_as_dataframe(self, n_companies: int) -> pl.DataFrame:
        companies = self.generate_hierarchical_companies(n_companies)
        # Holdings come first, without parent: read every row for the types
        return pl.DataFrame([company.to_dict() for company in companies], infer_schema_length=None)
