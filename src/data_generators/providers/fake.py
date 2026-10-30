"""Shared sources of fake data, so one `seed()` makes a whole run reproducible.

Every generator draws from the module-level `random` and the providers below,
never from its own instances.
"""

import hashlib
import random
import uuid
from datetime import date, timedelta

from mimesis import Finance, Person
from mimesis.locales import Locale

from src.data_generators.providers.brazil_provider import BrazilProvider
from src.utils.read_yamls import load_simulation_config

person = Person(Locale.PT_BR)
finance = Finance(Locale.PT_BR)
brazil = BrazilProvider()

SETTINGS = load_simulation_config()["generation_settings"]

# Dates in the config ("-2y", "today") are relative to this day
reference_date: date = date.today()


def seed(value: int, today: date | None = None) -> None:
    """Reseed every source; `today` pins the reference date as well."""
    global reference_date
    random.seed(value)
    for provider in (person, finance, brazil):
        provider.reseed(value)
    reference_date = today or date.today()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.UUID(int=random.getrandbits(128), version=4)}"


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def status(entity: str) -> str:
    """A status drawn from `generation_settings.<entity>_status_distribution`."""
    distribution = SETTINGS[f"{entity}_status_distribution"]
    return random.choices(list(distribution), weights=list(distribution.values()))[0]


def relative_date(spec: str) -> date:
    """`"today"` or `"-<n>y"` / `"-<n>d"`, relative to `reference_date`."""
    if spec == "today":
        return reference_date
    amount, unit = int(spec[1:-1]), spec[-1]
    days = amount * 365 if unit == "y" else amount
    return reference_date - timedelta(days=days)


def date_between(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, max((end - start).days, 0)))


def date_in_range(range_name: str, not_before: date | None = None) -> date:
    """A date in `generation_settings.date_ranges.<range_name>`, no earlier than `not_before`."""
    date_range = SETTINGS["date_ranges"][range_name]
    start, end = relative_date(date_range["start"]), relative_date(date_range["end"])
    if not_before and not_before > start:
        start = min(not_before, end)
    return date_between(start, end)
