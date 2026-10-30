import random
from datetime import date, timedelta

import polars as pl

from src.data_generators.providers import fake
from src.utils.read_yamls import load_pre_populated_data

CARD_TYPES = ["physical", "virtual"]

_REFERENCE = load_pre_populated_data()
PROGRAMS = {program["id"]: program for program in _REFERENCE["card_programs"]}
PROPRIETARY_MODALITY = next(
    m["id"] for m in _REFERENCE["transaction_modalities"] if m["type"] == "proprietary_network"
)


def modality_for(program_id: str) -> str:
    """The proprietary network for 3-party programs; one of the program's brands otherwise."""
    program = PROGRAMS[program_id]
    if program["network_type"] == "proprietary_network":
        return PROPRIETARY_MODALITY
    return random.choice(program["brands"])


class Card:
    """A benefit card. Its program fixes the wallets and the network."""

    def __init__(
        self,
        cardholder_id: str,
        program_id: str,
        issued_from: date | None = None,
    ) -> None:
        """`issued_from`: earliest issue date (the cardholder's admission)."""
        self.id: str = fake.new_id("card")
        self.cardholder_id: str = cardholder_id
        self.program_id: str = program_id
        self.modality_id: str = modality_for(program_id)
        self.card_number: str = "".join(str(random.randint(0, 9)) for _ in range(16))
        self.card_type: str = random.choice(CARD_TYPES)
        self.status: str = fake.status("card")
        self.issue_date: date = fake.date_in_range("card_issuance", issued_from)

        validity = fake.SETTINGS["card_validity_years"]
        years = random.randint(validity["min"], validity["max"])
        self.expiration_date: date = self.issue_date + timedelta(days=365 * years)

    def to_dict(self) -> dict[str, str | date]:
        """Columns of the `cards` table; the card number is stored hashed."""
        return {
            "id": self.id,
            "cardholder_id": self.cardholder_id,
            "program_id": self.program_id,
            "card_number_hash": fake.sha256(self.card_number),
            "modality_id": self.modality_id,
            "expiration_date": self.expiration_date,
            "card_type": self.card_type,
            "status": self.status,
            "issue_date": self.issue_date,
        }


class CardGenerator:
    """Generates cards for existing cardholders."""

    def __init__(self, cardholders_df: pl.DataFrame) -> None:
        """`cardholders_df` needs `id` and `admission_date`.

        Programs are drawn with `generation_settings.card_program_distribution`.
        """
        self.cardholders: list[dict] = cardholders_df.select("id", "admission_date").to_dicts()

    def generate_card(self) -> Card:
        cardholder = random.choice(self.cardholders)
        return Card(
            cardholder_id=cardholder["id"],
            program_id=fake.weighted_choice("card_program_distribution"),
            issued_from=cardholder["admission_date"],
        )

    def generate_cards_as_dataframe(self, n_cards: int) -> pl.DataFrame:
        return pl.DataFrame([self.generate_card().to_dict() for _ in range(n_cards)])
