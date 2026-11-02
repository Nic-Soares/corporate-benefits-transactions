"""The calendar that moves spending (`simulation_config.yaml → usage_patterns.seasonality`
and `simulation.year_end_credit`).

National holidays, fixed and the ones that follow Easter (Carnival, Good
Friday, Corpus Christi); the eve of each; a few shopping days (Christmas Eve,
New Year's Eve, Black Friday); a weight per month; and the one-off credit some
employers add at the end of the year (a Christmas basket).
"""

import hashlib
from datetime import date, timedelta
from functools import cache

from src.utils.read_yamls import load_simulation_config

_CONFIG = load_simulation_config()
SEASONALITY: dict = _CONFIG["usage_patterns"]["seasonality"]
YEAR_END_CREDIT: dict = _CONFIG["simulation"]["year_end_credit"]

# Month and day of the national holidays with a fixed date
FIXED_HOLIDAYS = {
    (1, 1): "new_year",
    (4, 21): "tiradentes",
    (5, 1): "labour_day",
    (9, 7): "independence",
    (10, 12): "our_lady_aparecida",
    (11, 2): "all_souls",
    (11, 15): "republic",
    (11, 20): "black_consciousness",
    (12, 25): "christmas",
}
# Days from Easter Sunday
EASTER_HOLIDAYS = {
    -48: "carnival_monday",
    -47: "carnival_tuesday",
    -2: "good_friday",
    60: "corpus_christi",
}


def easter(year: int) -> date:
    """Easter Sunday (Gregorian calendar; anonymous algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l_) // 433
    month = (h + l_ - 7 * m + 90) // 25
    return date(year, month, (h + l_ - 7 * m + 33 * month + 19) % 32)


@cache
def national_holidays(year: int) -> dict[date, str]:
    holidays = {date(year, month, day): name for (month, day), name in FIXED_HOLIDAYS.items()}
    sunday = easter(year)
    holidays |= {sunday + timedelta(days=d): name for d, name in EASTER_HOLIDAYS.items()}
    return holidays


@cache
def special_days(year: int) -> dict[date, str]:
    """Christmas Eve, New Year's Eve and Black Friday (fourth Friday of November)."""
    first_friday = date(year, 11, 1) + timedelta(days=(4 - date(year, 11, 1).weekday()) % 7)
    return {
        date(year, 12, 24): "christmas_eve",
        date(year, 12, 31): "new_years_eve",
        first_friday + timedelta(weeks=3): "black_friday",
    }


def is_holiday(day: date) -> bool:
    return day in national_holidays(day.year)


def _weight(table: dict[str, float], category: str | None) -> float:
    return table.get(category, table.get("all", 1.0))


def day_factor(day: date, category: str | None = None) -> float:
    """How much more (or less) the category sells on `day` than on a plain day of
    its weekday: the month's weight, times the holiday's, the eve's or the
    special day's."""
    factor = SEASONALITY["month_weights"][day.month - 1]
    special = special_days(day.year).get(day)
    if special:
        factor *= _weight(SEASONALITY["special_days"].get(special, {}), category)
    if is_holiday(day):
        factor *= _weight(SEASONALITY["holiday"], category)
    elif not special and is_holiday(day + timedelta(days=1)):
        factor *= _weight(SEASONALITY["eve"], category)
    return factor


def year_end_credit_day(year: int) -> date:
    return date(year, 12, YEAR_END_CREDIT["day"])


def year_end_credit(company_id: str, year: int) -> float:
    """The extra credit a company gives that year (0 if none): a share of the
    companies (`company_share`), an amount in the range rounded to 10. Drawn
    from the company id, so the attempts and the credits agree."""
    digest = hashlib.sha256(f"{company_id}:{year}".encode()).digest()
    if int.from_bytes(digest[:4]) / 2**32 >= YEAR_END_CREDIT["company_share"]:
        return 0.0
    amount = YEAR_END_CREDIT["amount"]
    share = int.from_bytes(digest[4:8]) / 2**32
    return round((amount["min"] + share * (amount["max"] - amount["min"])) / 10) * 10.0
