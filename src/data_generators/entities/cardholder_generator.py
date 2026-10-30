import random
from datetime import date

import polars as pl

from src.data_generators.providers import fake

JOB_POSITIONS = [
    "Director",
    "Manager",
    "Coordinator",
    "Analyst",
    "Specialist",
    "Executive",
    "Consultant",
    "Officer",
]

DEPARTMENTS = [
    "Finance",
    "Operations",
    "Sales",
    "HR",
    "IT",
    "Marketing",
    "Legal",
    "Procurement",
]


class Cardholder:
    """An employee of a client company who holds benefit cards."""

    def __init__(
        self,
        company_id: str,
        municipio_data: dict[str, str],
        hired_from: date | None = None,
    ) -> None:
        """`hired_from`: earliest admission date (the company's registration)."""
        self.id: str = fake.new_id("cardholder")
        self.company_id: str = company_id
        self.cpf: str = fake.brazil.cpf()
        self.name: str = fake.person.full_name()
        self.city: str = municipio_data["municipio_nome"]
        self.state: str = municipio_data["uf_sigla"]
        self.position: str = random.choice(JOB_POSITIONS)
        self.department: str = random.choice(DEPARTMENTS)
        self.admission_date: date = fake.date_in_range("cardholder_admission", hired_from)
        self.status: str = fake.status("cardholder")

    def to_dict(self) -> dict[str, str | date]:
        """Columns of the `cardholders` table; the CPF is stored hashed."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "cpf_hash": fake.sha256(self.cpf),
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "admission_date": self.admission_date,
            "position": self.position,
            "department": self.department,
            "status": self.status,
        }


class CardholderGenerator:
    """Generates cardholders located in real IBGE municipalities."""

    def __init__(self, municipios_df: pl.DataFrame) -> None:
        """`municipios_df` needs the columns `municipio_nome` and `uf_sigla`."""
        self.municipios: list[dict[str, str]] = (
            municipios_df.select(["municipio_nome", "uf_sigla"])
            .unique(maintain_order=True)
            .to_dicts()
        )

    def generate_cardholder(self, company_id: str, hired_from: date | None = None) -> Cardholder:
        return Cardholder(company_id, random.choice(self.municipios), hired_from)

    def generate_cardholders_as_dataframe(
        self, companies_df: pl.DataFrame, cardholders_per_company: int
    ) -> pl.DataFrame:
        """`companies_df` needs `id` and `registration_date` (admissions come after it)."""
        cardholders = [
            self.generate_cardholder(company["id"], company["registration_date"])
            for company in companies_df.select("id", "registration_date").iter_rows(named=True)
            for _ in range(cardholders_per_company)
        ]
        return pl.DataFrame([cardholder.to_dict() for cardholder in cardholders])
