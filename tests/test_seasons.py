"""The calendar that moves spending."""

from datetime import date

from src.simulation import seasons


def test_easter_and_the_holidays_it_moves():
    assert seasons.easter(2025) == date(2025, 4, 20)
    assert seasons.easter(2026) == date(2026, 4, 5)
    holidays = seasons.national_holidays(2026)
    assert holidays[date(2026, 2, 16)] == "carnival_monday"
    assert holidays[date(2026, 4, 3)] == "good_friday"
    assert holidays[date(2026, 6, 4)] == "corpus_christi"
    assert len(holidays) == len(seasons.FIXED_HOLIDAYS) + len(seasons.EASTER_HOLIDAYS)


def test_special_days():
    assert seasons.special_days(2025)[date(2025, 11, 28)] == "black_friday"
    assert seasons.special_days(2026)[date(2026, 11, 27)] == "black_friday"


def test_day_factor():
    plain = seasons.day_factor(date(2026, 3, 10), "supermarket")
    assert seasons.day_factor(date(2026, 4, 2), "supermarket") > plain  # eve of Good Friday
    assert seasons.day_factor(date(2025, 12, 24), "supermarket") > 1.5
    assert seasons.day_factor(date(2025, 11, 28), "retail") > 2
    assert seasons.day_factor(date(2025, 11, 28), "restaurant") == seasons.day_factor(
        date(2025, 11, 27), "restaurant"
    )


def test_year_end_credit():
    amounts = [seasons.year_end_credit(f"comp_{i}", 2025) for i in range(2000)]
    given = [a for a in amounts if a]
    share = seasons.YEAR_END_CREDIT["company_share"]
    assert abs(len(given) / len(amounts) - share) < 0.05
    bounds = seasons.YEAR_END_CREDIT["amount"]
    assert all(bounds["min"] <= a <= bounds["max"] and a % 10 == 0 for a in given)
    assert seasons.year_end_credit("comp_1", 2025) == seasons.year_end_credit("comp_1", 2025)
