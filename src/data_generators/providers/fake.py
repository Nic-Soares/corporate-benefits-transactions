"""Shared sources of fake data, so one `seed()` makes a whole run reproducible.

Every generator draws from the module-level `random` and the providers below,
never from its own instances.
"""

import hashlib
import math
import random
import uuid
from datetime import date, timedelta
from itertools import accumulate

import polars as pl
from mimesis import Person
from mimesis.locales import Locale

from src.data_generators.providers.brazil_provider import BrazilProvider
from src.utils.read_yamls import load_simulation_config

person = Person(Locale.PT_BR)
brazil = BrazilProvider()

SETTINGS = load_simulation_config()["generation_settings"]

# Dates in the config ("-2y", "today") are relative to this day
reference_date: date = date.today()


def seed(value: int, today: date | None = None) -> None:
    """Reseed every source; `today` pins the reference date as well."""
    global reference_date
    random.seed(value)
    for provider in (person, brazil):
        provider.reseed(value)
    reference_date = today or date.today()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.UUID(int=random.getrandbits(128), version=4)}"


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def weighted_key(distribution: dict[str, float]) -> str:
    """A key of `distribution`, drawn with its value as weight."""
    return random.choices(list(distribution), weights=list(distribution.values()))[0]


def weighted_choice(setting: str) -> str:
    """A key of `generation_settings.<setting>`, drawn with its value as weight."""
    return weighted_key(SETTINGS[setting])


def log_uniform_int(low: int, high: int) -> int:
    """An integer in [low, high], uniform on a log scale: small values are commoner."""
    return min(high, max(low, round(math.exp(random.uniform(math.log(low), math.log(high))))))


def lognormal_amount(median: float, p90: float, cap: float, step: float = 0.01) -> float:
    """A log-normal amount with this median and 90th percentile, capped, in `step` units."""
    sigma = math.log(p90 / median) / 1.2816  # z of the 90th percentile
    value = min(random.lognormvariate(math.log(median), sigma), cap)
    return round(max(round(value / step), 1) * step, 2)


def status(entity: str) -> str:
    """A status drawn from `generation_settings.<entity>_status_distribution`."""
    return weighted_choice(f"{entity}_status_distribution")


def status_since(status: str, start: date) -> date:
    """The day `status` began: the record's start when active; otherwise a day
    from the start to today, no more than `status_since_max_days` back for a
    status that doesn't last (a terminal in maintenance)."""
    if status == "active":
        return start
    limit = SETTINGS["status_since_max_days"].get(status)
    earliest = max(start, reference_date - timedelta(days=limit)) if limit else start
    return date_between(min(earliest, reference_date), reference_date)


class Municipalities:
    """Municipalities to draw from, weighted by the `weight` column when
    `municipios_df` has it (IBGE `population` or `gdp`), uniformly otherwise."""

    def __init__(self, municipios_df: pl.DataFrame, weight: str = "population") -> None:
        df = municipios_df.unique(["municipio_nome", "uf_sigla"], maintain_order=True)
        self.rows: list[dict[str, str]] = df.select("municipio_nome", "uf_sigla").to_dicts()
        self.cum_weights: list[int] | None = None
        if weight in df.columns:
            self.cum_weights = list(accumulate(df[weight].fill_null(1).to_list()))

    def draw(self) -> dict[str, str]:
        """`{municipio_nome, uf_sigla}`"""
        return random.choices(self.rows, cum_weights=self.cum_weights)[0]


# Legal names: "<Surname> <activity> <type>"; synthetic, never a real company's
ACTIVITIES = [
    "Comércio",
    "Indústria e Comércio",
    "Serviços",
    "Tecnologia",
    "Engenharia",
    "Logística",
    "Alimentos",
    "Construções",
    "Consultoria",
    "Participações",
]
LEGAL_TYPES = {"Ltda": 0.8, "S.A.": 0.2}


def company_names(word: str | None = None) -> tuple[str, str]:
    """(legal name, trade name) from Brazilian surnames. `word` (e.g. "Padaria")
    goes into the trade name; without it the trade name is the surnames."""
    surname = person.surname()
    if random.random() < 0.3:
        surname = f"{surname} & {person.surname()}"
    trade = (
        surname
        if word is None
        else (
            f"{surname} {word}"
            if word in ("Mobilidade", "Transportes", "Digital", "Streaming")
            else f"{word} {surname}"
        )
    )
    legal = f"{surname} {random.choice(ACTIVITIES)} {weighted_key(LEGAL_TYPES)}"
    return legal, trade


def relative_date(spec: str) -> date:
    """`"today"` or `"-<n>y"` / `"-<n>d"`, relative to `reference_date`."""
    if spec == "today":
        return reference_date
    amount, unit = int(spec[1:-1]), spec[-1]
    days = amount * 365 if unit == "y" else amount
    return reference_date - timedelta(days=days)


def amount_between(setting: str) -> float:
    """A value in `generation_settings.<setting>` ({min, max}), rounded to cents."""
    bounds = SETTINGS[setting]
    return round(random.uniform(bounds["min"], bounds["max"]), 2)


def date_between(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, max((end - start).days, 0)))


def date_in_range(range_name: str, not_before: date | None = None) -> date:
    """A date in `generation_settings.date_ranges.<range_name>`, no earlier than `not_before`."""
    date_range = SETTINGS["date_ranges"][range_name]
    start, end = relative_date(date_range["start"]), relative_date(date_range["end"])
    if not_before and not_before > start:
        start = min(not_before, end)
    return date_between(start, end)
