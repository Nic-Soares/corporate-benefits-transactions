"""The calendar that moves spending (`simulation.yaml → usage_patterns.seasonality`
and `simulation.year_end_credit`).

National holidays, fixed and the ones that follow Easter (Carnival, Good
Friday, Corpus Christi); the eve of each; a few shopping days (Christmas Eve,
New Year's Eve, Black Friday); a weight per month; the one-off credit some
employers add at the end of the year (a Christmas basket); and the `Calendar`
of a window, which draws the day of each attempt.
"""

import hashlib
import random
from bisect import bisect_left, bisect_right
from datetime import date, datetime, timedelta
from functools import cache
from itertools import accumulate

from src.config import load_simulation

_CONFIG = load_simulation()
USAGE: dict = _CONFIG["usage_patterns"]
SEASONALITY: dict = USAGE["seasonality"]
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


class Calendar:
    """The days of a window and how much each sells, per category: its week
    (a holiday takes Saturday's weight), the day of the month (spending follows
    the credit), the calendar above (`day_factor`) and an intensity each month
    draws (`seasonality.month_noise_sigma`)."""

    def __init__(self, end: date, days_back: int, categories: list[str]) -> None:
        """The `days_back` days before `end`; `categories` with their own curve."""
        start = datetime.combine(end, datetime.min.time())
        self.days = [start - timedelta(days=d) for d in range(days_back, 0, -1)]
        self.dates = [day.date() for day in self.days]
        intensity = {
            month: random.lognormvariate(0, SEASONALITY["month_noise_sigma"])
            for month in sorted({(day.year, day.month) for day in self.dates})
        }
        weeks = USAGE["weekday_weights_by_category"]
        self.cum = {
            category: list(
                accumulate(
                    _day_weight(day, weeks.get(category, USAGE["weekday_weights"]), category)
                    * intensity[day.year, day.month]
                    for day in self.days
                )
            )
            for category in [None, *categories]
        }

    def day(self, earliest: date, category: str | None, latest: date | None = None) -> datetime:
        """A day of the window from `earliest` on (to `latest`), by the category's
        day weights (the nearest day when none is left)."""
        first = bisect_left(self.dates, earliest)
        stop = bisect_right(self.dates, latest) if latest else len(self.days)
        if first >= stop:
            return self.days[min(first, len(self.days) - 1)]
        cum = self.cum.get(category) or self.cum[None]
        low = cum[first - 1] if first else 0.0
        point = low + random.random() * (cum[stop - 1] - low)
        return self.days[min(bisect_right(cum, point, first, stop), stop - 1)]

    @staticmethod
    def at(day: datetime, category: str) -> datetime:
        """A moment of `day` at an hour of the category's day."""
        hours = USAGE["hour_weights_by_category"].get(category, USAGE["hour_weights"])
        hour = random.choices(range(24), weights=hours)[0]
        return day + timedelta(hours=hour, seconds=random.randint(0, 3599))

    def moment(self, category: str, earliest: date) -> datetime:
        """A day of the window from `earliest` on, then an hour of the category's day."""
        return self.at(self.day(earliest, category), category)


def _day_weight(day: datetime, week: list[float], category: str | None) -> float:
    """The weekday's weight (a holiday's is Saturday's), higher early in the
    month (the credit lands), times the calendar's (`day_factor`)."""
    month = USAGE["month_day_weights"]
    progress = (day.day - 1) / 30
    weekday = 5 if is_holiday(day.date()) else day.weekday()
    return (
        week[weekday]
        * (month["first"] + (month["last"] - month["first"]) * progress)
        * day_factor(day.date(), category)
    )
