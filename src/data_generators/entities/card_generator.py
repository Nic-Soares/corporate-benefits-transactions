import random
from datetime import date, timedelta

import polars as pl

from src.data_generators.providers import fake
from src.utils.read_yamls import load_pre_populated_data

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
        """`issued_from`: the cardholder's admission; the card comes a few days after
        (`card_issue_days_after_admission`), no later than today."""
        self.id: str = fake.new_id("card")
        self.cardholder_id: str = cardholder_id
        self.program_id: str = program_id
        self.modality_id: str = modality_for(program_id)
        self.card_number: str = "".join(str(random.randint(0, 9)) for _ in range(16))
        self.card_type: str = fake.weighted_choice("card_type_distribution")
        self.status: str = fake.status("card")
        delay = fake.SETTINGS["card_issue_days_after_admission"]
        admission = issued_from or fake.date_in_range("cardholder_admission")
        self.issue_date: date = min(
            admission + timedelta(days=random.randint(delay["min"], delay["max"])),
            fake.reference_date,
        )

        # Renewed on expiry: the current plastic expires after today
        validity = fake.SETTINGS["card_validity_years"]
        plastic = timedelta(days=365 * random.randint(validity["min"], validity["max"]))
        self.expiration_date: date = self.issue_date + plastic
        while self.expiration_date <= fake.reference_date:
            self.expiration_date += plastic

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
    """Generates the cards of existing cardholders.

    Each company contracts a bundle of programs (`generation_settings.program_bundles`)
    and each of its cardholders gets one card per program of the bundle.
    """

    def __init__(self, cardholders_df: pl.DataFrame) -> None:
        """`cardholders_df` needs `id`, `company_id` and `admission_date`."""
        self.cardholders: list[dict] = cardholders_df.select(
            "id", "company_id", "admission_date"
        ).to_dicts()

    @staticmethod
    def draw_bundle() -> list[str]:
        bundles = fake.SETTINGS["program_bundles"]
        return random.choices(bundles, weights=[b["weight"] for b in bundles])[0]["programs"]

    def generate_cards(self) -> list[Card]:
        bundles: dict[str, list[str]] = {}
        cards = []
        for cardholder in self.cardholders:
            company_id = cardholder["company_id"]
            if company_id not in bundles:
                bundles[company_id] = self.draw_bundle()
            cards += [
                Card(cardholder["id"], program_id, issued_from=cardholder["admission_date"])
                for program_id in bundles[company_id]
            ]
        return cards

    def generate_cards_as_dataframe(self) -> pl.DataFrame:
        return pl.DataFrame([card.to_dict() for card in self.generate_cards()])
