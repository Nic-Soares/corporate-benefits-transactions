import random
import uuid
from datetime import date

import polars as pl
from mimesis import Datetime, Finance
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale

# Initialize providers
finance = Finance(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()

# Valid statuses for companies
VALID_COMPANY_STATUSES = ["active", "inactive", "suspended"]

# Business segments for companies
COMPANY_SEGMENTS = [
    "Public",  # Setor Público
    "Corporate",  # Grande Empresa / Corporativo
    "Middle",  # Média Empresa
    "SME",  # Pequena/Média Empresa
    "High SME",  # PME de Alto Crescimento
]


class Company:
    """Classe que representa uma empresa corporativa"""

    def __init__(
        self,
        segment_name: str,
        municipio_data: dict[str, str],
        parent_id: str | None = None,
    ) -> None:
        self.id: str = f"comp_{uuid.uuid7()}"
        # Lógica: Se tiver parent_id, é filial. Se for None, é Holding.
        self.parent_id: str | None = parent_id
        self.cnpj: str = brazil.cnpj()
        self.company_name: str = finance.company()
        self.trade_name: str = finance.company()
        self.segment_name: str = segment_name
        self.municipio_nome: str = municipio_data["municipio_nome"]
        self.uf_sigla: str = municipio_data["uf_sigla"]
        self.status: str = random.choice(VALID_COMPANY_STATUSES)
        self.registration_date: date = datetime_provider.date(start=2010, end=2024)

    def to_dict(self) -> dict[str, str | date | None]:
        """Converte a empresa para dicionário - Ajustado para dim_companies"""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "cnpj": self.cnpj,
            "name": self.company_name,
            "trade_name": self.trade_name,
            "segment": self.segment_name,
            "city": self.municipio_nome,
            "state": self.uf_sigla,
            "status": self.status,
            "registration_date": self.registration_date,
        }


class CompanyGenerator:
    """Gerador de empresas corporativas com dados reais do IBGE"""

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
        """Extrai dados de referência para geração de empresas"""
        self.segment_names: list[str] = COMPANY_SEGMENTS
        self.municipios_list: list[dict[str, str]] = (
            self.municipios_df.select(["municipio_nome", "uf_sigla"])
            .unique()
            .to_dicts()
        )

    def generate_company(self, parent_id: str | None = None) -> Company:
        """
        Gera uma empresa, permitindo passar um parent_id para criar filial.

        Args:
            parent_id: ID da empresa-mãe (None para holdings)

        Returns:
            Company: Instância de Company gerada
        """
        segment_name: str = random.choice(self.segment_names)
        municipio_data: dict[str, str] = random.choice(self.municipios_list)

        return Company(
            segment_name=segment_name,
            municipio_data=municipio_data,
            parent_id=parent_id,
        )

    def generate_hierarchical_companies(
        self, n_companies: int, holding_ratio: float = 0.2
    ) -> list[Company]:
        """
        Gera empresas com estrutura hierárquica (Holding -> Filiais).

        Args:
            n_companies: Total de empresas a gerar
            holding_ratio: Proporção de empresas que serão Holdings (0.0 a 1.0)

        Returns:
            list[Company]: Lista de empresas com relacionamentos parent-child
        """
        n_holdings = int(n_companies * holding_ratio)
        if n_holdings < 1:
            n_holdings = 1
        n_branches = n_companies - n_holdings

        companies: list[Company] = []

        # 1. Gerar Holdings (parent_id = None)
        holdings = [self.generate_company(parent_id=None) for _ in range(n_holdings)]
        companies.extend(holdings)

        # 2. Gerar Filiais (parent_id = ID de uma Holding aleatória)
        holding_ids = [h.id for h in holdings]
        for _ in range(n_branches):
            random_parent = random.choice(holding_ids)
            branch = self.generate_company(parent_id=random_parent)
            companies.append(branch)

        return companies

    def generate_companies_as_dataframe(self, n_companies: int) -> pl.DataFrame:
        """
        Gera empresas como DataFrame Polars com a lógica hierárquica.

        Args:
            n_companies: Total de empresas a gerar

        Returns:
            pl.DataFrame: DataFrame com colunas de empresa
        """
        companies_list = self.generate_hierarchical_companies(n_companies)
        return pl.DataFrame([c.to_dict() for c in companies_list])
