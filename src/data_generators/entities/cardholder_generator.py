import hashlib
import random
import uuid
from datetime import date

import polars as pl
from mimesis import Person, Datetime
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale

# Initialize providers
person = Person(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()

# Valid statuses for cardholders
VALID_CARDHOLDER_STATUSES = ["active", "inactive", "suspended"]

# Job positions
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

# Departments
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
    """Classe que representa um portador de cartão corporativo"""

    def __init__(
        self,
        company_id: str,
        municipio_data: dict[str, str],
    ) -> None:
        self.id: str = f"cardholder_{uuid.uuid7()}"
        self.company_id: str = company_id
        self.cpf: str = brazil.cpf()
        self.name: str = person.full_name()
        self.city: str = municipio_data["municipio_nome"]
        self.state: str = municipio_data["uf_sigla"]
        self.position: str = random.choice(JOB_POSITIONS)
        self.department: str = random.choice(DEPARTMENTS)
        self.admission_date: date = datetime_provider.date(start=2015, end=2024)
        self.status: str = random.choice(VALID_CARDHOLDER_STATUSES)

    def to_dict(self) -> dict[str, str | date]:
        """Converte o portador para dicionário - Ajustado para dim_cardholders"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "position": self.position,
            "department": self.department,
            "admission_date": self.admission_date,
            "status": self.status,
        }


class CardholderGenerator:
    """Gerador de portadores de cartão corporativo"""

    def __init__(self, municipios_df: pl.DataFrame) -> None:
        """
        Inicializa o gerador com dados de municípios.

        Args:
            municipios_df: DataFrame Polars com dados de municípios do IBGE
                           (requer colunas: municipio_nome, uf_sigla)
        """
        self.municipios_df: pl.DataFrame = municipios_df
        self._extract_reference_data()

    def _extract_reference_data(self) -> None:
        """Extrai dados de referência para geração de portadores"""
        self.municipios_list: list[dict[str, str]] = (
            self.municipios_df.select(["municipio_nome", "uf_sigla"])
            .unique()
            .to_dicts()
        )

    def generate_cardholder(self, company_id: str) -> Cardholder:
        """
        Gera um portador de cartão corporativo para uma empresa.

        Args:
            company_id: ID da empresa à qual o portador pertence

        Returns:
            Cardholder: Instância de Cardholder gerada
        """
        municipio_data: dict[str, str] = random.choice(self.municipios_list)
        return Cardholder(company_id=company_id, municipio_data=municipio_data)

    def generate_cardholders_for_company(
        self, company_id: str, n_cardholders: int
    ) -> list[Cardholder]:
        """
        Gera múltiplos portadores para uma empresa.

        Args:
            company_id: ID da empresa
            n_cardholders: Número de portadores a gerar

        Returns:
            list[Cardholder]: Lista de portadores gerados
        """
        return [self.generate_cardholder(company_id) for _ in range(n_cardholders)]

    def generate_cardholders_as_dataframe(
        self, company_ids: list[str], cardholders_per_company: int
    ) -> pl.DataFrame:
        """
        Gera portadores como DataFrame Polars.

        Args:
            company_ids: Lista de IDs de empresas
            cardholders_per_company: Número de portadores por empresa

        Returns:
            pl.DataFrame: DataFrame com colunas de portador
        """
        cardholders_list = []
        for company_id in company_ids:
            cardholders = self.generate_cardholders_for_company(
                company_id, cardholders_per_company
            )
            cardholders_list.extend(cardholders)

        return pl.DataFrame([c.to_dict() for c in cardholders_list])