import hashlib
import random
from datetime import date

import polars as pl
import ulid
from mimesis import Datetime

# Valid statuses for cards
VALID_CARD_STATUSES = ["active", "inactive", "blocked", "canceled"]
VALID_CARD_TYPES = ["physical", "virtual"]


class Card:
    """Classe que representa um cartão corporativo."""

    def __init__(
        self,
        cardholder_id: str,
        modality_id: str | None = None,
    ) -> None:
        """
        Construtor da classe Card - cria um novo cartão.

        Args:
            cardholder_id: ID do portador do cartão (obrigatório).
            modality_id: ID da modalidade do cartão (opcional, pode ser None).
        """
        datetime_provider = Datetime()

        self.card_id: str = f"card_{ulid.ULID()}"
        self.cardholder_id: str = cardholder_id
        self.modality_id: str | None = modality_id

        card_number = self._generate_card_number()
        self.card_number_hash: str = self._generate_card_hash(card_number)

        self.expiration_date: date = datetime_provider.date(start=2025, end=2029)
        self.card_type: str = random.choice(VALID_CARD_TYPES)
        self.status: str = random.choice(VALID_CARD_STATUSES)
        self.issuance_date: date = datetime_provider.date(start=2020, end=2024)

    def _generate_card_number(self) -> str:
        """Método privado para gerar número do cartão (16 dígitos)."""
        return "".join([str(random.randint(0, 9)) for _ in range(16)])

    def to_dict(self) -> dict[str, str | date | None]:
        """Converte o cartão para um dicionário compatível com a tabela SQL."""
        return {
            "card_id": self.card_id,
            "cardholder_id": self.cardholder_id,
            "card_number": self.card_number_hash,
            "modality_id": self.modality_id,
            "expiration_date": self.expiration_date,
            "card_type": self.card_type,
            "status": self.status,
            "issuance_date": self.issuance_date,
        }

    def __str__(self) -> str:
        """Representação em string do cartão para impressão."""
        return f"Cartão {self.card_id} - {self.card_type} - {self.status}"

    def __repr__(self) -> str:
        """Representação detalhada para debug."""
        return f"Card(card_id='{self.card_id}', cardholder_id='{self.cardholder_id}', status='{self.status}')"


class CardGenerator:
    """Gerador de cartões corporativos."""

    def __init__(
        self,
        cardholder_ids: list[str],
        modality_ids: list[str] | None = None,
    ) -> None:
        """
        Construtor do gerador de cartões.

        Args:
            cardholder_ids: Lista com IDs dos portadores que podem ter cartão.
            modality_ids: Lista com IDs das modalidades de cartão (opcional).
        """
        self.cardholder_ids: list[str] = cardholder_ids
        self.modality_ids: list[str] = modality_ids or []

    def generate_card(self) -> Card:
        """Gera um único cartão com dados aleatórios."""
        cardholder_id = random.choice(self.cardholder_ids)
        modality_id = random.choice(self.modality_ids) if self.modality_ids else None

        return Card(cardholder_id=cardholder_id, modality_id=modality_id)

    def generate_card_as_dict(self) -> dict[str, str | date | None]:
        """Gera um cartão e o retorna como um dicionário."""
        return self.generate_card().to_dict()

    def generate_multiple_cards(self, n_cards: int) -> list[Card]:
        """Gera uma lista de múltiplos cartões."""
        return [self.generate_card() for _ in range(n_cards)]

    def generate_cards_as_dicts(
        self, n_cards: int
    ) -> list[dict[str, str | date | None]]:
        """Gera uma lista de múltiplos cartões como dicionários."""
        return [card.to_dict() for card in self.generate_multiple_cards(n_cards)]

    def generate_cards_as_dataframe(self, n_cards: int) -> pl.DataFrame:
        """Gera múltiplos cartões como um DataFrame Polars."""
        card_dicts = self.generate_cards_as_dicts(n_cards)
        return pl.DataFrame(card_dicts)
