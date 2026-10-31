import random
from datetime import date

import polars as pl

from src.data_generators.entities.company_generator import COMPANY_SEGMENTS
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
        """`municipios_df` needs `municipio_nome` and `uf_sigla`; with `population`,
        cardholders who don't live in their company's city follow where people live."""
        self.municipios = fake.Municipalities(municipios_df)

    def generate_cardholder(
        self,
        company_id: str,
        hired_from: date | None = None,
        company_city: dict[str, str] | None = None,
    ) -> Cardholder:
        """Lives in `company_city` (`{municipio_nome, uf_sigla}`) most of the time
        (`generation_settings.cardholder_same_city_ratio`)."""
        same_city = company_city and random.random() < fake.SETTINGS["cardholder_same_city_ratio"]
        return Cardholder(
            company_id, company_city if same_city else self.municipios.draw(), hired_from
        )

    def generate_cardholders_as_dataframe(
        self, companies_df: pl.DataFrame, scale: float = 1.0
    ) -> pl.DataFrame:
        """Cardholders of each company, as many as its segment says.

        `companies_df` needs `id`, `segment`, `registration_date` (admissions
        come after it), `city` and `state`. The count is drawn from the segment's
        range in `generation_settings.company_segments`, small sizes commoner,
        times `scale`.
        """
        cardholders = []
        for company in companies_df.select(
            "id", "segment", "registration_date", "city", "state"
        ).iter_rows(named=True):
            city = {"municipio_nome": company["city"], "uf_sigla": company["state"]}
            size = COMPANY_SEGMENTS[company["segment"]]["cardholders"]
            count = max(round(fake.log_uniform_int(size["min"], size["max"]) * scale), 1)
            cardholders += [
                self.generate_cardholder(company["id"], company["registration_date"], city)
                for _ in range(count)
            ]
        return pl.DataFrame([cardholder.to_dict() for cardholder in cardholders])
