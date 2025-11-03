from datetime import date
import polars as pl
import random
import ulid
from mimesis import Finance, Datetime
from mimesis.builtins import BrazilSpecProvider
from mimesis.locales import Locale
from pathlib import Path
from src.utils.read_data_files import read_parquet

# Initialize providers
finance = Finance(Locale.PT_BR)
datetime_provider = Datetime(Locale.PT_BR)
brazil = BrazilSpecProvider()

# Valid statuses for companies
VALID_COMPANY_STATUSES = ["active", "inactive", "suspended"]


class Company:
    """Classe que representa uma empresa corporativa"""

    def __init__(
        self,
        cnpj: str,
        company_name: str,
        trade_name: str,
        segment_name: str,
        municipio_nome: str,
        uf_sigla: str,
        status: str,
        registration_date: date,
    ) -> None:
        """Construtor da classe Company - cria uma nova empresa"""
        self.company_id: str = f"comp_{ulid.ULID()}"
        self.cnpj: str = cnpj
        self.company_name: str = company_name
        self.trade_name: str = trade_name
        self.segment_name: str = segment_name
        self.municipio_nome: str = municipio_nome
        self.uf_sigla: str = uf_sigla
        self.status: str = status
        self.registration_date: date = registration_date

    def to_dict(self) -> dict[str, str | date]:
        """Converte a empresa para dicionário - exatamente como a tabela SQL"""
        return {
            "company_id": self.company_id,
            "cnpj": self.cnpj,
            "company_name": self.company_name,
            "trade_name": self.trade_name,
            "segment_name": self.segment_name,
            "municipio_nome": self.municipio_nome,
            "uf_sigla": self.uf_sigla,
            "status": self.status,
            "registration_date": self.registration_date,
        }

    def __str__(self) -> str:
        """Representação em string da empresa para impressão"""
        return f"Empresa {self.company_id} - {self.company_name} ({self.cnpj}) - {self.status}"

    def __repr__(self) -> str:
        """Representação detalhada para debug"""
        return f"Company(cnpj='{self.cnpj}', name='{self.company_name}', segment='{self.segment_name}', status='{self.status}')"


class CompanyGenerator:
    """Gerador de empresas corporativas com dados reais do IBGE e segmentos"""

    def __init__(
        self,
        municipios_df: pl.DataFrame,
        segments_df: pl.DataFrame | None = None,
        segments_parquet_path: str | None = None,
    ) -> None:
        """
        Construtor do gerador de empresas

        Args:
            municipios_df: DataFrame Polars com dados de municípios do IBGE
            segments_df: DataFrame Polars com dados de segmentos
            segments_parquet_path: Caminho para arquivo Parquet de segmentos
        """
        self.municipios_df: pl.DataFrame = municipios_df

        # Carrega dados de segmentos
        if segments_df is None:
            if segments_parquet_path is None:
                segments_parquet_path = str(
                    Path(__file__).parent.parent.parent.parent
                    / "data"
                    / "reference_data"
                    / "segments.parquet"
                )

            self.segments_df: pl.DataFrame = read_parquet(segments_parquet_path)
        else:
            self.segments_df = segments_df

        self._extract_reference_data()

    def _extract_reference_data(self) -> None:
        """Extrai dados de referência dos DataFrames para uso rápido"""
        self.segment_names: list[str] = (
            self.segments_df.select("segment_name").to_series().to_list()
        )
        self.municipios_list: list[dict[str, str]] = (
            self.municipios_df.select(["municipio_nome", "uf_sigla"])
            .unique()
            .to_dicts()
        )

    def generate_company(self) -> Company:
        """Gera uma única empresa com dados aleatórios"""
        segment_name: str = random.choice(self.segment_names)
        municipio_data: dict[str, str] = random.choice(self.municipios_list)

        return Company(
            cnpj=brazil.cnpj(),
            company_name=finance.company(),
            trade_name=finance.company(),
            segment_name=segment_name,
            municipio_nome=municipio_data["municipio_nome"],
            uf_sigla=municipio_data["uf_sigla"],
            status="active",
            registration_date=datetime_provider.date(start=2010, end=2024),
        )

    def generate_company_as_dict(self) -> dict[str, str | date]:
        """Gera uma empresa e retorna como dicionário"""
        return self.generate_company().to_dict()

    def generate_multiple_companies(self, n_companies: int) -> list[Company]:
        """Gera múltiplas empresas"""
        return [self.generate_company() for _ in range(n_companies)]

    def generate_companies_as_dicts(
        self, n_companies: int
    ) -> list[dict[str, str | date]]:
        """Gera múltiplas empresas como dicionários"""
        return [c.to_dict() for c in self.generate_multiple_companies(n_companies)]

    def generate_companies_as_dataframe(self, n_companies: int) -> pl.DataFrame:
        """Gera múltiplas empresas como DataFrame Polars"""
        return pl.DataFrame(self.generate_companies_as_dicts(n_companies))
