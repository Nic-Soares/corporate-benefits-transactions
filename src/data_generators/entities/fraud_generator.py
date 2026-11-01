"""Fraud attempts, by scenario (`simulation_config.yaml → fraud`).

Typologies of the benefits-card market: someone other than the cardholder
uses the card. Each incident is a short burst on one card (or, for a point of
compromise, on several cards skimmed at the same shop). The attempts go
through the same issuer as the legit ones; `is_fraud` and `fraud_scenario`
label them.
"""

import random
from datetime import datetime, timedelta

from src.data_generators.entities.establishment_generator import CATEGORIES
from src.data_generators.entities.transaction_generator import TransactionGenerator
from src.data_generators.providers import fake
from src.utils.read_yamls import load_simulation_config

FRAUD = load_simulation_config()["fraud"]

# Shops with a physical terminal; each scenario keeps those the card's wallets fit
IN_PERSON = [c for c, rule in CATEGORIES.items() if not rule.get("online") and not rule.get("atm")]
WALLET_CAPTURES = ["APPLE_PAY", "GOOGLE_PAY", "MOBILE_NFC"]
SKIMMED_AT = ["fuel", "supermarket"]
# Tries to find an eligible victim before giving up on an incident
TRIES = 20


class FraudGenerator:
    def __init__(self, generator: TransactionGenerator) -> None:
        """Uses the legit generator's cards, terminals and calendar."""
        self.g = generator
        self.start, self.end = generator.days[0], generator.days[-1] + timedelta(days=1)
        self.active = [c for c in generator.cards if c["status"] == "active"]
        # States with terminals of each category, for "far from home"
        self.states: dict[str, list[str]] = {}
        self.state_of: dict[str, str] = {}  # terminal id → state
        for key, (terminals, _) in generator.local.items():
            if len(key) == 2:
                category, state = key
                self.states.setdefault(category, []).append(state)
                self.state_of |= {t["id"]: state for t in terminals}

    # --- helpers ------------------------------------------------------------

    def _home_state(self, card: dict) -> str:
        return self.g.home[card["cardholder_id"]][1]

    def _terminal(self, category: str, state: str, types: tuple[str, ...]) -> dict | None:
        terminals, weights = self.g.local.get((category, state), ([], []))
        usable = [(t, w) for t, w in zip(terminals, weights, strict=True) if t["type"] in types]
        if not usable:
            return None
        return random.choices([t for t, _ in usable], weights=[w for _, w in usable])[0]

    def _far(self, card: dict, categories: list[str], types: tuple[str, ...]):
        """(category, terminal) in a state other than the cardholder's, where the
        card's wallets work: fraudsters learn fast where a card passes."""
        home = self._home_state(card)
        categories = [c for c in categories if self.g._fits(c, card)] or categories
        for _ in range(TRIES):
            category = random.choice(categories)
            states = [s for s in self.states.get(category, []) if s != home]
            if not states:
                continue
            terminal = self._terminal(category, random.choice(states), types)
            if terminal:
                return category, terminal
        return None

    def _start(self, card: dict, category: str, terminal: dict) -> datetime:
        """A moment of the window after the card and the terminal exist."""
        return self.g._moment(category, max(card["issue_date"], terminal["installation_date"]))

    @staticmethod
    def _after(moment: datetime, minutes: tuple[int, int]) -> datetime:
        return moment + timedelta(minutes=random.randint(*minutes))

    def _victim(self, condition) -> dict | None:
        candidates = [c for c in self.active if condition(c)]
        return random.choice(candidates) if candidates else None

    # --- scenarios ----------------------------------------------------------

    def account_takeover_wallet(self) -> list[dict]:
        """The app account is taken over and the card added to a mobile wallet: a
        burst of wallet payments in shops of another state, within hours."""
        card = self._victim(lambda c: True)
        if not card:
            return []
        attempts, moment = [], None
        for _ in range(random.randint(3, 8)):
            found = self._far(card, IN_PERSON, ("POS",))
            if not found:
                break
            category, terminal = found
            moment = (
                self._after(moment, (5, 60)) if moment else self._start(card, category, terminal)
            )
            attempts.append(
                self.g.attempt(
                    card,
                    category,
                    terminal,
                    moment,
                    random.choice(WALLET_CAPTURES),
                    amount=self.g.amount(category, 1.8),
                    fraud_scenario="account_takeover_wallet",
                )
            )
        return attempts

    def card_not_present(self) -> list[dict]:
        """A brand card's number used online: purchases over a few days that drain
        the open wallet."""
        online = [c for c in CATEGORIES if CATEGORIES[c].get("online") and c in self.g.terminals]
        card = self._victim(
            lambda c: c["modality_id"] != "OWN" and "GIFT" in self.g.wallets_by_card[c["id"]]
        )
        if not card or not online:
            return []
        attempts, moment = [], None
        for _ in range(random.randint(4, 12)):
            category = random.choice(online)
            terminal = random.choice(self.g.terminals[category])
            moment = (
                self._after(moment, (10, 600)) if moment else self._start(card, category, terminal)
            )
            attempts.append(
                self.g.attempt(
                    card,
                    category,
                    terminal,
                    moment,
                    "ECOMMERCE",
                    amount=self.g.amount(category, 2.0),
                    fraud_scenario="card_not_present",
                )
            )
        return attempts

    def intercepted_card(self) -> list[dict]:
        """A new card used before the cardholder gets it, in another state:
        contactless where no PIN is asked, chip attempts with a wrong PIN."""
        card = self._victim(
            lambda c: c["card_type"] == "physical" and c["issue_date"] >= self.start.date()
        )
        if not card:
            return []
        moment = datetime.combine(card["issue_date"], datetime.min.time()) + timedelta(
            days=random.randint(1, 5), hours=random.randint(8, 20)
        )
        attempts = []
        for _ in range(random.randint(2, 6)):
            found = self._far(card, IN_PERSON, ("POS",))
            if not found:
                break
            category, terminal = found
            moment = self._after(moment, (15, 720))
            chip = random.random() < 0.3
            attempts.append(
                self.g.attempt(
                    card,
                    category,
                    terminal,
                    moment,
                    "CHIP" if chip else "CONTACTLESS",
                    amount=self.g.amount(category, 1.5),
                    pin="wrong" if chip else None,
                    fraud_scenario="intercepted_card",
                )
            )
        return attempts

    def point_of_compromise(self) -> list[dict]:
        """Cards skimmed at one shop (a legit visit), then the cloned stripe used
        with the captured PIN in another state, days later."""
        category = random.choice([c for c in SKIMMED_AT if c in self.g.terminals])
        shop = random.choice([t for t in self.g.terminals[category] if t["type"] in ("POS", "TEF")])
        state = self.state_of.get(shop["id"])
        nearby = [
            c for c in self.active if c["card_type"] == "physical" and self._home_state(c) == state
        ] or [c for c in self.active if c["card_type"] == "physical"]
        attempts = []
        for card in random.sample(nearby, min(len(nearby), random.randint(4, 10))):
            visit = self.g._moment(category, max(card["issue_date"], shop["installation_date"]))
            if visit > self.end - timedelta(days=4):
                continue
            # The legit visit where the card was skimmed
            attempts.append(self.g.attempt(card, category, shop, visit, "CHIP", pin="ok"))
            moment = visit + timedelta(days=random.randint(3, 15))
            for _ in range(random.randint(1, 3)):
                found = self._far(card, IN_PERSON, ("POS", "TEF"))
                if not found:
                    break
                far_category, terminal = found
                moment = self._after(moment, (10, 240))
                attempts.append(
                    self.g.attempt(
                        card,
                        far_category,
                        terminal,
                        moment,
                        "MAG_STRIPE",
                        amount=self.g.amount(far_category, 1.5),
                        pin="ok",
                        fraud_scenario="point_of_compromise",
                    )
                )
        return attempts

    def generate(self, n_attempts: int) -> list[dict]:
        """Incidents by scenario weight until about `n_attempts` fraud attempts,
        each inside the window."""
        attempts: list[dict] = []
        fraud = 0
        for _ in range(n_attempts * TRIES):
            if fraud >= n_attempts:
                break
            incident = getattr(self, fake.weighted_key(FRAUD["scenarios"]))()
            incident = [a for a in incident if self.start <= a["date"] < self.end]
            attempts += incident
            fraud += sum(a["is_fraud"] for a in incident)
        return attempts
